"""
model/src/models/random_forest.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Random Forest Classifier — Sports Injury Predictor
====================================================
Dataset  : data/injury_data.csv
Target   : Likelihood_of_Injury  (0 = not injured, 1 = injured)
Features : Player_Age, Player_Weight, Player_Height,
           Previous_Injuries, Training_Intensity, Recovery_Time

Every line below is explained with a comment.  The script is structured
as a mini pipeline that matches the full project layout:

    Load → Preprocess → Split → Train → Evaluate → Save → Inspect

Run from project root:
    python -m model.src.models.random_forest
"""

# ── Standard library ──────────────────────────────────────────────────────────
import json                         # For serialising the evaluation report to disk
from pathlib import Path            # OS-agnostic file paths (works on Win/Mac/Linux)

# ── Third-party ───────────────────────────────────────────────────────────────
import joblib                       # Efficient binary serialisation for sklearn objects
import numpy as np                  # Numerical operations (arrays, random seeds, etc.)
import pandas as pd                 # Tabular data manipulation

# sklearn: preprocessing
from sklearn.preprocessing import StandardScaler   # Zero-mean, unit-variance scaling

# sklearn: model selection
from sklearn.model_selection import (
    train_test_split,               # Splits dataset into train and test subsets
    StratifiedKFold,                # K-Fold that preserves class balance in each fold
    cross_val_score,                # Runs cross-validation and returns per-fold scores
    GridSearchCV,                   # Exhaustive hyperparameter search with cross-validation
)

# sklearn: the model itself
from sklearn.ensemble import RandomForestClassifier  # Ensemble of decision trees

# sklearn: evaluation metrics
from sklearn.metrics import (
    accuracy_score,                 # (TP + TN) / total — overall correctness
    precision_score,                # TP / (TP + FP) — how many predicted positives are real
    recall_score,                   # TP / (TP + FN) — how many actual positives we caught
    f1_score,                       # Harmonic mean of precision & recall
    roc_auc_score,                  # Area under ROC curve — probability ranking quality
    classification_report,          # Full per-class breakdown of all metrics above
    confusion_matrix,               # 2×2 matrix: [[TN, FP], [FN, TP]]
)

# Internal project logger (writes timestamped messages to stdout)
from model.src.utils import get_logger

# ── Logger setup ──────────────────────────────────────────────────────────────
# Creates a named logger for this module so log messages are traceable
logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
# Absolute path to the raw CSV — uses __file__ so it works regardless of cwd
# parents[3] → model/src/models → model/src → model → project root
DATA_PATH     = Path(__file__).parents[3] / "data" / "injury_data.csv"

# Directory where fitted model + report are persisted
ARTIFACTS_DIR = Path(__file__).parents[3] / "model" / "artifacts"

# The column we are trying to predict
TARGET_COL    = "Likelihood_of_Injury"

# Columns used as input features (everything except the target)
FEATURE_COLS  = [
    "Player_Age",           # Age of the athlete (years)
    "Player_Weight",        # Body weight (kg)
    "Player_Height",        # Height (cm)
    "Previous_Injuries",    # Binary flag: had prior injury (0/1)
    "Training_Intensity",   # Normalised training load score [0, 1]
    "Recovery_Time",        # Days between training sessions
]

# Fix the random seed so results are fully reproducible across runs
RANDOM_STATE  = 42

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Load Data
# ─────────────────────────────────────────────────────────────────────────────

def load_data(path: Path) -> pd.DataFrame:
    """
    Read the CSV into a pandas DataFrame.

    pd.read_csv() parses the header row automatically, infers dtypes,
    and stores each column as a Series.  The result is a table with
    1,000 rows and 7 columns for injury_data.csv.
    """
    logger.info(f"Loading data from: {path}")

    df = pd.read_csv(path)  # Parse CSV → DataFrame

    # Log basic facts so we can sanity-check the load
    logger.info(f"  Shape : {df.shape}  ({df.shape[0]:,} rows × {df.shape[1]} columns)")
    logger.info(f"  Target distribution:\n{df[TARGET_COL].value_counts().to_string()}")

    return df


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Preprocess
# ─────────────────────────────────────────────────────────────────────────────

def preprocess(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean the raw DataFrame and scale numeric features.

    Returns
    -------
    X : pd.DataFrame  — feature matrix  (1,000 × 6)
    y : pd.DataFrame  — target series   (1,000,)

    Why StandardScaler?
        Random Forests are tree-based and are theoretically scale-invariant,
        BUT scaling is still applied here so the pipeline stays consistent
        with the rest of the project (e.g., logistic regression baselines
        and distance-based models all need it).  It never hurts a tree model.
    """
    # ── 2a. Remove duplicate rows ─────────────────────────────────────────────
    n_before = len(df)
    df = df.drop_duplicates()           # Removes rows where ALL column values match
    n_removed = n_before - len(df)
    logger.info(f"  Duplicates removed : {n_removed}")

    # ── 2b. Impute any missing values (none in this dataset, but defensive) ───
    for col in FEATURE_COLS:
        if df[col].isna().any():
            # Median is robust to outliers; mode for categoricals handled separately
            df[col] = df[col].fillna(df[col].median())
            logger.info(f"  Imputed '{col}' with median")

    # ── 2c. Separate features (X) from the label (y) ─────────────────────────
    X = df[FEATURE_COLS].copy()     # Select only the 6 feature columns
    y = df[TARGET_COL].copy()       # Select only the target column

    # ── 2d. Standardise numeric features ─────────────────────────────────────
    # StandardScaler computes: z = (x - mean) / std for every column
    # After transformation each feature has mean ≈ 0 and std ≈ 1
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)   # fit: learns mean/std; transform: applies it

    # Convert the numpy array back to a DataFrame so column names are preserved
    X_scaled_df = pd.DataFrame(X_scaled, columns=FEATURE_COLS, index=X.index)

    # Persist the fitted scaler so inference can reuse the same parameters
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, ARTIFACTS_DIR / "rf_scaler.joblib")
    logger.info("  Scaler saved → model/artifacts/rf_scaler.joblib")

    logger.info(f"  Feature matrix shape : {X_scaled_df.shape}")
    logger.info(f"  Label vector shape   : {y.shape}")

    return X_scaled_df, y


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Stratified Train / Test Split
# ─────────────────────────────────────────────────────────────────────────────

def split_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Divide X and y into training (80%) and test (20%) subsets.

    stratify=y  → sklearn ensures both subsets have the *same class ratio*
                  as the full dataset.  Without this, a random split might
                  put all the injured samples into one subset by chance.

    random_state → fixes the RNG so the split is identical on every run.
    """
    logger.info("Splitting data — 80% train / 20% test (stratified)")

    X_train, X_test, y_train, y_test = train_test_split(
        X,                        # Feature matrix
        y,                        # Target vector
        test_size=test_size,      # 0.2 → 200 rows for test, 800 for train
        stratify=y,               # Preserve class balance in both splits
        random_state=RANDOM_STATE,# Reproducible split
    )

    # Log the shapes and class distributions of both halves
    logger.info(f"  Train : {X_train.shape}  | Class dist: {y_train.value_counts().to_dict()}")
    logger.info(f"  Test  : {X_test.shape}   | Class dist: {y_test.value_counts().to_dict()}")

    return X_train, X_test, y_train, y_test


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Build & Train the Random Forest
# ─────────────────────────────────────────────────────────────────────────────

def build_model() -> RandomForestClassifier:
    """
    Instantiate a Random Forest Classifier with hand-tuned hyperparameters.

    Random Forest = bagged ensemble of independent decision trees.

    Key hyperparameter breakdown
    ----------------------------
    n_estimators=200
        Build 200 decision trees.  Each tree sees a bootstrap sample
        (random subset with replacement) of the training data.
        Predictions are made by majority vote across all trees.
        More trees → lower variance, but diminishing returns > ~200.

    max_depth=10
        Each tree can split up to 10 levels deep.
        Shallow trees (e.g. 3) underfit; unlimited depth overfits.
        10 is a safe default for a 6-feature, 1,000-row dataset.

    min_samples_split=5
        A node must contain ≥ 5 samples before it is allowed to split.
        Prevents trees from learning noise in tiny leaf groups.

    min_samples_leaf=2
        Every leaf node must have ≥ 2 training samples.
        Acts as a regulariser — avoids single-sample leaves.

    max_features='sqrt'
        At each split, randomly consider only √6 ≈ 2-3 features.
        This de-correlates the trees from each other, which is the
        key idea behind Random Forests vs. a plain bagged tree.

    class_weight='balanced'
        Automatically adjusts sample weights inversely proportional
        to class frequency: weight_i = n_samples / (n_classes × n_i).
        Protects against majority-class bias on imbalanced data.

    bootstrap=True
        Each tree is trained on a bootstrap sample (drawn with replacement).
        ~37% of training rows are left out per tree ("out-of-bag" samples),
        which gives a free internal validation signal.

    oob_score=True
        Compute the Out-Of-Bag accuracy using those held-out samples.
        A useful sanity-check that does NOT require a separate val set.

    n_jobs=-1
        Use ALL available CPU cores for parallelism.  Building 200 trees
        is embarrassingly parallel — each tree is independent.

    random_state=RANDOM_STATE
        Seeds the internal RNG so the forest is reproducible.
        Without this, results differ on every run.
    """
    model = RandomForestClassifier(
        n_estimators=200,           # Number of trees in the forest
        max_depth=10,               # Maximum depth of each tree
        min_samples_split=5,        # Min samples required to split a node
        min_samples_leaf=2,         # Min samples required at each leaf
        max_features="sqrt",        # Features considered per split
        class_weight="balanced",    # Handle class imbalance automatically
        bootstrap=True,             # Use bootstrap sampling for each tree
        oob_score=True,             # Enable Out-Of-Bag accuracy estimate
        n_jobs=-1,                  # Parallelise across all CPU cores
        random_state=RANDOM_STATE,  # Reproducibility seed
    )
    return model


def train(
    model: RandomForestClassifier,
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> RandomForestClassifier:
    """
    Fit the Random Forest on the training data.

    model.fit(X, y) internally:
      1. Draws n_estimators bootstrap samples from X_train
      2. Grows one decision tree per sample (in parallel)
      3. At each node, randomly selects max_features candidates
         and picks the best split (highest Gini impurity reduction)
      4. Stores all trees as model.estimators_
    """
    logger.info("Training Random Forest …")
    model.fit(X_train, y_train)     # ← All the learning happens here

    # model.oob_score_ is the accuracy measured on the out-of-bag samples
    # It's a pessimistic estimate (good) and doesn't require a held-out set
    logger.info(f"  OOB accuracy (internal estimate) : {model.oob_score_:.4f}")
    logger.info(f"  Trees grown                      : {len(model.estimators_)}")
    logger.info(f"  Max depth used                   : {model.max_depth}")

    return model


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Cross-Validation
# ─────────────────────────────────────────────────────────────────────────────

def cross_validate(
    model: RandomForestClassifier,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_splits: int = 5,
) -> dict[str, float]:
    """
    Run Stratified K-Fold cross-validation on the TRAINING set only.

    Why CV on train only?
        The test set must not influence any modelling decisions.
        CV gives a robust estimate of generalisation performance
        by cycling through k different train/val partitions.

    StratifiedKFold(n_splits=5)
        Divides the 800 training rows into 5 equal folds of 160 rows.
        In each iteration:
          - 4 folds (640 rows) → training
          - 1 fold  (160 rows) → validation
        The 'stratified' part ensures each fold has the same 50/50 ratio.

    cross_val_score(scoring='roc_auc')
        For each fold, trains a fresh copy of the model, predicts
        probabilities on the validation fold, and returns the ROC-AUC.
        ROC-AUC is preferred over accuracy for binary classification
        because it measures *ranking quality* across all thresholds.
    """
    logger.info("Running 5-Fold Stratified Cross-Validation …")

    # Stratified K-Fold: k=5 folds, shuffled, reproducible
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)

    # Collect ROC-AUC for each fold
    roc_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc", n_jobs=-1)

    # Collect F1 for each fold (useful alongside ROC-AUC)
    f1_scores  = cross_val_score(model, X_train, y_train, cv=cv, scoring="f1",      n_jobs=-1)

    logger.info(f"  ROC-AUC per fold : {[round(s, 4) for s in roc_scores]}")
    logger.info(f"  ROC-AUC mean±std : {roc_scores.mean():.4f} ± {roc_scores.std():.4f}")
    logger.info(f"  F1 per fold      : {[round(s, 4) for s in f1_scores]}")
    logger.info(f"  F1 mean±std      : {f1_scores.mean():.4f} ± {f1_scores.std():.4f}")

    return {
        "cv_roc_auc_mean": float(roc_scores.mean()),
        "cv_roc_auc_std":  float(roc_scores.std()),
        "cv_f1_mean":      float(f1_scores.mean()),
        "cv_f1_std":       float(f1_scores.std()),
    }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Evaluate on the Held-Out Test Set
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(
    model: RandomForestClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, float]:
    """
    Measure performance on the 200-row test set that the model never saw.

    model.predict(X_test)
        Each tree votes for a class; the majority label wins.
        Returns a hard binary array: [0, 1, 1, 0, …]

    model.predict_proba(X_test)[:, 1]
        Returns the *fraction of trees* that voted for class 1.
        This soft probability is used for ROC-AUC (needs probabilities,
        not hard labels) and for setting a custom decision threshold.

    Confusion matrix layout:
        [[TN  FP]
         [FN  TP]]
        TN = correctly predicted "not injured"
        FP = predicted "injured" but actually not  (false alarm)
        FN = predicted "not injured" but actually was  (missed injury ← costly!)
        TP = correctly predicted "injured"
    """
    logger.info("─" * 65)
    logger.info("EVALUATION ON HELD-OUT TEST SET (200 rows)")
    logger.info("─" * 65)

    # Hard class predictions (0 or 1)
    y_pred  = model.predict(X_test)

    # Soft probability scores (fraction of trees voting class-1)
    y_proba = model.predict_proba(X_test)[:, 1]

    # ── Individual metrics ────────────────────────────────────────────────────
    acc  = accuracy_score(y_test, y_pred)
    # accuracy — fraction of all predictions that are correct
    # Fine for balanced datasets; misleading for imbalanced ones

    prec = precision_score(y_test, y_pred, zero_division=0)
    # precision — of all rows we labelled "injured", what fraction truly were?
    # Low precision → too many false alarms (crying wolf)

    rec  = recall_score(y_test, y_pred, zero_division=0)
    # recall (sensitivity) — of all truly injured rows, how many did we catch?
    # Low recall → missed injuries — the most dangerous error type here

    f1   = f1_score(y_test, y_pred, zero_division=0)
    # F1 — harmonic mean of precision & recall; balances both concerns
    # Especially useful when one class matters more than overall accuracy

    roc  = roc_auc_score(y_test, y_proba)
    # ROC-AUC — probability that the model ranks a random positive higher
    # than a random negative.  0.5 = random guess, 1.0 = perfect.

    # ── Confusion matrix ──────────────────────────────────────────────────────
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()   # Unpack the four quadrants

    # ── Log everything ────────────────────────────────────────────────────────
    logger.info(f"  Accuracy       : {acc:.4f}   ({acc*100:.1f}%)")
    logger.info(f"  Precision      : {prec:.4f}  (of 'injury' preds, {prec*100:.1f}% were real)")
    logger.info(f"  Recall         : {rec:.4f}   (caught {rec*100:.1f}% of actual injuries)")
    logger.info(f"  F1 Score       : {f1:.4f}")
    logger.info(f"  ROC-AUC        : {roc:.4f}")
    logger.info("")
    logger.info("  Confusion Matrix:")
    logger.info(f"                Predicted 0   Predicted 1")
    logger.info(f"    Actual 0  :     {tn:>5}         {fp:>5}   (TN | FP)")
    logger.info(f"    Actual 1  :     {fn:>5}         {tp:>5}   (FN | TP)")
    logger.info("")

    # Per-class precision, recall, F1 + weighted averages
    report = classification_report(
        y_test, y_pred,
        target_names=["Not Injured (0)", "Injured (1)"],
    )
    logger.info("  Full Classification Report:")
    for line in report.strip().split("\n"):
        logger.info(f"    {line}")

    logger.info("─" * 65)

    return {
        "accuracy":  float(acc),
        "precision": float(prec),
        "recall":    float(rec),
        "f1":        float(f1),
        "roc_auc":   float(roc),
        "TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp),
    }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Feature Importance
# ─────────────────────────────────────────────────────────────────────────────

def feature_importance(
    model: RandomForestClassifier,
    feature_names: list[str],
) -> pd.DataFrame:
    """
    Extract and rank Mean Decrease in Impurity (MDI) feature importances.

    model.feature_importances_
        For every feature, measures the average reduction in Gini impurity
        (weighted by the number of samples reaching that node) summed across
        ALL trees and ALL nodes where that feature was used for a split.
        Values are normalised to sum to 1.0.

    Interpretation:
        Higher value → the feature contributes more to reducing uncertainty
        in the prediction.  A feature with importance 0.0 was never used
        as a split criterion across all 200 trees.

    Caveat: MDI is biased towards high-cardinality numeric features.
    For a rigorous alternative, use Permutation Importance (sklearn also
    provides this via sklearn.inspection.permutation_importance).
    """
    # model.feature_importances_ is a 1D numpy array, one value per feature
    importances = model.feature_importances_

    # Pair each importance score with its feature name and sort descending
    imp_df = (
        pd.DataFrame({"Feature": feature_names, "Importance": importances})
        .sort_values("Importance", ascending=False)  # Best features first
        .reset_index(drop=True)                      # Clean index after sort
    )
    # Add a running cumulative total — the top-N features that explain X% of decisions
    imp_df["Cumulative"] = imp_df["Importance"].cumsum().round(4)

    logger.info("Feature Importances (Mean Decrease in Impurity):")
    logger.info(f"  {'Rank':<5} {'Feature':<25} {'Importance':>11}  {'Cumulative':>11}")
    logger.info(f"  {'─'*55}")
    for rank, row in imp_df.iterrows():
        logger.info(
            f"  {rank+1:<5} {row['Feature']:<25} "
            f"{row['Importance']:>10.4f}   {row['Cumulative']:>10.4f}"
        )

    return imp_df


# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 — Save Model & Report
# ─────────────────────────────────────────────────────────────────────────────

def save_artifacts(
    model: RandomForestClassifier,
    metrics: dict,
    cv_metrics: dict,
    imp_df: pd.DataFrame,
) -> None:
    """
    Persist the trained model and evaluation report to disk.

    joblib.dump()
        Serialises the Python object using pickle + memory-mapped arrays.
        Much faster and more memory-efficient than Python's built-in pickle
        for large numpy arrays inside sklearn estimators.

    The JSON report gives a human-readable audit trail of the training run,
    useful for experiment tracking when MLflow is not available.
    """
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Save the fitted model ─────────────────────────────────────────────────
    model_path = ARTIFACTS_DIR / "random_forest.joblib"
    joblib.dump(model, model_path)
    # joblib.dump: serialise the entire fitted RandomForestClassifier (all 200 trees)
    logger.info(f"  Model saved → {model_path}")

    # ── Save the evaluation report as JSON ────────────────────────────────────
    report = {
        "model":             "RandomForestClassifier",
        "n_estimators":      model.n_estimators,
        "max_depth":         model.max_depth,
        "oob_accuracy":      round(model.oob_score_, 4),
        "cross_validation":  cv_metrics,
        "test_metrics":      metrics,
        "feature_importances": imp_df.set_index("Feature")["Importance"].round(6).to_dict(),
    }

    report_path = ARTIFACTS_DIR / "rf_report.json"
    with report_path.open("w") as f:
        json.dump(report, f, indent=2)
    # json.dump: writes the dict as formatted JSON text to the file handle
    logger.info(f"  Report saved → {report_path}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE — runs when script is executed directly
# ─────────────────────────────────────────────────────────────────────────────

def main() -> RandomForestClassifier:
    """
    Execute the full training pipeline end-to-end:
        Load → Preprocess → Split → Build → Train → CV → Evaluate → Save
    """
    logger.info("=" * 65)
    logger.info("  RANDOM FOREST TRAINING PIPELINE — Sports Injury Predictor")
    logger.info("=" * 65)

    # ── 1. Load ───────────────────────────────────────────────────────────────
    df = load_data(DATA_PATH)

    # ── 2. Preprocess ─────────────────────────────────────────────────────────
    X, y = preprocess(df)

    # ── 3. Split 80 / 20 ──────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2)

    # ── 4. Build model ────────────────────────────────────────────────────────
    model = build_model()

    # ── 5. Train ──────────────────────────────────────────────────────────────
    model = train(model, X_train, y_train)

    # ── 6. Cross-validate (on train set) ─────────────────────────────────────
    cv_metrics = cross_validate(model, X_train, y_train)

    # ── 7. Evaluate on held-out test set ──────────────────────────────────────
    metrics = evaluate(model, X_test, y_test)

    # ── 8. Feature importance ─────────────────────────────────────────────────
    imp_df = feature_importance(model, FEATURE_COLS)

    # ── 9. Persist model + report ─────────────────────────────────────────────
    save_artifacts(model, metrics, cv_metrics, imp_df)

    logger.info("=" * 65)
    logger.info("  ✅  Training complete.")
    logger.info(f"  ROC-AUC (test) : {metrics['roc_auc']:.4f}")
    logger.info(f"  F1      (test) : {metrics['f1']:.4f}")
    logger.info(f"  Recall  (test) : {metrics['recall']:.4f}  ← key metric for injury detection")
    logger.info("=" * 65)

    return model


# ── Entry point ───────────────────────────────────────────────────────────────
# This block runs only when the file is executed directly (not when imported).
# Executing as a module: python -m model.src.models.random_forest
if __name__ == "__main__":
    main()
