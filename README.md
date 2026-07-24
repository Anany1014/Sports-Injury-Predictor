# 🏋️ Sports Injury Predictor

A machine learning system that predicts the likelihood of sports injuries based on athlete biometrics, training load, recovery metrics, and historical data.

---

## 📁 Project Structure

```
Sports Injury Predictor/
├── data/
│   ├── raw/                  # Raw, immutable input data
│   ├── processed/            # Cleaned & feature-engineered data
│   └── external/             # External reference datasets
├── notebooks/
│   ├── 01_EDA.ipynb          # Exploratory Data Analysis
│   ├── 02_feature_engineering.ipynb
│   └── 03_model_experiments.ipynb
├── model/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── data/             # Data loading & preprocessing
│   │   ├── features/         # Feature engineering
│   │   ├── models/           # ML model definitions & training
│   │   ├── evaluation/       # Model evaluation & metrics
│   │   └── utils/            # Shared utilities
│   ├── configs/              # Training & model configs (YAML)
│   ├── artifacts/            # Saved models, scalers, encoders
│   └── tests/                # Unit & integration tests
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic & ML inference
│   │   └── core/             # Config, logging, security
│   └── tests/
├── frontend/                 # UI (see frontend README)
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── Makefile
└── .env.example
```

---

## 🚀 Quick Start

### 1. Create & activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
# For development (linting, testing, notebooks)
pip install -r requirements-dev.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your values
```

### 4. Run the full ML pipeline
```bash
make pipeline
```

### 5. Start the API server
```bash
make serve
```

---

## 🧠 ML Pipeline

| Step | Script | Description |
|------|--------|-------------|
| 1 | `model/src/data/ingest.py` | Load & validate raw data |
| 2 | `model/src/data/preprocess.py` | Clean, impute, encode |
| 3 | `model/src/features/engineering.py` | Build features |
| 4 | `model/src/models/train.py` | Train ML models |
| 5 | `model/src/evaluation/evaluate.py` | Evaluate & log metrics |
| 6 | `model/src/models/predict.py` | Run inference |

---

## 🔧 Make Commands

```bash
make pipeline      # Run full data → train → evaluate pipeline
make train         # Train model only
make evaluate      # Evaluate trained model
make serve         # Start FastAPI backend
make test          # Run all tests
make lint          # Run ruff + mypy
make clean         # Remove generated artifacts
```

---

## 📊 Key Features Used

- **Biometrics**: Age, weight, height, BMI, sport type, position
- **Training Load**: Weekly volume, intensity, acute:chronic workload ratio (ACWR)
- **Recovery**: Sleep hours, HRV, soreness score, rest days
- **History**: Prior injuries, days since last injury, injury count

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Open a Pull Request

---

## 📄 License

MIT License © 2026
