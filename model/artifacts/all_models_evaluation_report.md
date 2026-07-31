# Model Training Evaluation Report

Evaluated **12 model training approaches** across test set (6,182 samples, 75 injuries).

| Training Approach | Precision | Recall | F1 Score | AUC-ROC | PR-AUC | Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGBoost Baseline (th=0.50)** | 1.50% | 32.00% | 0.0287 | 0.5832 | 0.0161 | 73.68% |
| **XGBoost F1-Tuned (th=0.25)** | 1.36% | 77.33% | 0.0267 | 0.5832 | 0.0161 | 31.49% |
| **XGBoost High Recall / Max Safety (th=0.15)** | 1.30% | 96.00% | 0.0256 | 0.5832 | 0.0161 | 11.50% |
| **Balanced HistGradientBoosting (th=0.45)** | 1.51% | 26.67% | 0.0286 | 0.5659 | 0.0168 | 78.05% |
| **LightGBM Balanced Classifier (th=0.25)** | 1.48% | 57.33% | 0.0289 | 0.5681 | 0.0216 | 53.33% |
| **Random Forest Classifier (th=0.25)** | 1.48% | 93.33% | 0.0291 | 0.5950 | 0.0171 | 24.39% |
| **Logistic Regression Classifier (th=0.15)** | 1.23% | 100.00% | 0.0244 | 0.5895 | 0.0161 | 2.83% |
| **Saved Artifact: model.pkl** | 1.63% | 89.33% | 0.0320 | 0.6040 | 0.0190 | 34.36% |
| **Saved Artifact: balanced_ts_model.joblib** | 1.69% | 16.00% | 0.0306 | 0.5792 | 0.0165 | 87.69% |
| **Saved Artifact: high_perf_xgboost_model.joblib** | 1.63% | 89.33% | 0.0320 | 0.6040 | 0.0190 | 34.36% |
| **Saved Artifact: optimized_ts_model.joblib** | 1.50% | 80.00% | 0.0295 | 0.5894 | 0.0164 | 36.10% |
| **Saved Artifact: high_recall_ts_model.joblib** | 1.53% | 52.00% | 0.0298 | 0.5792 | 0.0165 | 58.88% |
