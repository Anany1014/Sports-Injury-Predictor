# 🏋️ Sports Injury Predictor

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF.svg)](https://vitejs.dev/)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end Machine Learning system and interactive web platform that predicts athlete injury risk based on biometric data, training workload, recovery signals, and historical injury logs.

---

## 🌟 Key Features

- **🧠 Machine Learning Engine**: Advanced gradient boosting algorithms (XGBoost, LightGBM, Random Forest) tuned with class imbalance handling (`scale_pos_weight`) and Acute:Chronic Workload Ratio (ACWR) feature engineering.
- **⚡ High-Performance FastAPI Backend**: RESTful API providing real-time single and batch prediction endpoints, strict data validation via Pydantic, and automated OpenAPI documentation (`/docs`).
- **💻 Interactive React Dashboard**: Modern UI built with React 19, Vite, Recharts, and Lucide icons for risk visualization and batch athlete assessments.
- **🔄 Automated ML Pipeline**: Modular pipeline stages covering data ingestion, preprocessing, rolling-window feature engineering, model training, evaluation, and artifact serialization.
- **🛡️ Production Ready**: Full test suite (Pytest), static type checking (Mypy), and strict code formatting (Ruff, Oxlint).

---

## 📁 Project Structure

```
Sports Injury Predictor/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/              # API endpoints (health, predict, batch)
│   │   ├── core/             # Configuration & environment settings
│   │   ├── schemas/          # Pydantic data schemas
│   │   ├── services/         # Model inference & predictor service
│   │   └── main.py           # FastAPI entrypoint & lifespan events
│   └── tests/                # API integration & unit tests
├── frontend/                 # React + Vite Dashboard UI
│   ├── src/                  # React components & dashboard views
│   ├── public/               # Static web assets
│   ├── package.json          # Frontend dependencies & scripts
│   └── vite.config.js        # Vite configuration
├── model/                    # ML Core & Pipeline
│   ├── artifacts/            # Trained models, encoders, and scalers
│   ├── configs/              # YAML training & hyperparameter configs
│   ├── src/
│   │   ├── data/             # Ingestion & preprocessing modules
│   │   ├── evaluation/       # Performance metrics & reports
│   │   ├── features/         # Feature engineering & ACWR calculation
│   │   ├── models/           # Model definitions, training & inference
│   │   └── utils/            # Helper utilities & logging
│   └── tests/                # ML pipeline & model unit tests
├── data/
│   ├── raw/                  # Raw input datasets
│   ├── processed/            # Feature-engineered & cleaned data
│   └── external/             # External reference datasets
├── notebooks/                # Exploratory Data Analysis & experiments
├── Makefile                  # Automation commands
├── pyproject.toml            # Tooling configuration (Ruff, Mypy, Pytest)
├── requirements.txt          # Core production dependencies
├── requirements-dev.txt      # Development & testing dependencies
└── .env.example              # Environment variables template
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** & **npm**

### 1. Backend & ML Environment Setup

```bash
# 1. Clone repository and navigate to root directory
cd "Sports Injury Predictor"

# 2. Create and activate a Python virtual environment
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Configure environment variables
cp .env.example .env
```

### 2. Run ML Pipeline & Start Backend API

```bash
# Execute the full pipeline: Ingest -> Preprocess -> Engineer Features -> Train -> Evaluate
make pipeline

# Start the FastAPI server (runs on http://localhost:8000)
make serve
```

### 3. Frontend Setup & Launch

Open a new terminal window:

```bash
cd frontend

# Install Node dependencies
npm install

# Start the development server (runs on http://localhost:5173)
npm run dev
```

---

## 🔌 API Reference & Documentation

FastAPI provides automated interactive API documentation accessible when the backend server is running:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Core Endpoints

#### 1. Health Check
`GET /health`
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "0.1.0"
}
```

#### 2. Single Athlete Prediction
`POST /api/v1/predict`

**Request Payload**:
```json
{
  "athlete_id": "ATH-001",
  "date": "2026-07-25",
  "sport": "Football",
  "position": "Midfielder",
  "age": 24,
  "weight_kg": 75.5,
  "height_cm": 178.0,
  "weekly_volume_hrs": 12.5,
  "weekly_intensity_score": 7.2,
  "sleep_hours": 7.5,
  "hrv_ms": 65.0,
  "soreness_score": 3.0,
  "rest_days": 1,
  "prior_injuries": 2,
  "days_since_last_injury": 90.0
}
```

**Response Payload**:
```json
{
  "athlete_id": "ATH-001",
  "injury_probability": 0.18,
  "injury_risk_label": "LOW",
  "risk_factors": [
    "High weekly training load",
    "Sub-optimal sleep"
  ],
  "timestamp": "2026-07-25T17:10:00Z"
}
```

#### 3. Batch Prediction
`POST /api/v1/predict/batch`

Accepts an array of athlete records (up to 100 per request) for bulk evaluations.

---

## 🧠 ML Features & Model Training

### Engineered Feature Categories

| Feature Group | Indicators |
|---|---|
| **Biometrics** | Age, Weight, Height, BMI, Sport Type, Field Position |
| **Workload & ACWR** | Weekly Volume (hrs), Weekly Intensity (1-10), Acute:Chronic Workload Ratio (7-day / 28-day rolling window) |
| **Recovery & Fatigue** | Sleep Duration (hrs), Heart Rate Variability (HRV ms), Soreness Score (0-10), Rest Days |
| **Historical Risk** | Prior Injury Count, Days Elapsed Since Last Injury |

### Hyperparameter Configuration

Model architecture and training settings are specified in `model/configs/training_config.yaml`:

```yaml
model:
  name: "sports_injury_predictor"
  version: "1.0.0"
  type: "xgboost" # Options: xgboost | lightgbm | random_forest | logistic_regression

xgboost:
  n_estimators: 300
  max_depth: 6
  learning_rate: 0.05
  scale_pos_weight: 3 # Handles class imbalance
```

---

## 🔧 Automation & Make Commands

| Command | Action |
|---|---|
| `make pipeline` | Runs data ingestion, preprocessing, feature extraction, model training, and evaluation |
| `make train` | Trains ML model using the latest engineered features |
| `make evaluate` | Evaluates trained model performance metrics on test split |
| `make serve` | Launches FastAPI production/development Uvicorn server |
| `make test` | Executes all Pytest unit and integration test suites |
| `make lint` | Runs `ruff check` and `mypy` for static analysis |
| `make format` | Formats Python code using `ruff format` |
| `make clean` | Removes cached artifacts, bytecode, and compiled temporary files |

---

## 🧪 Testing & Code Quality

### Backend & Model Tests

```bash
# Run pytest test suite
pytest

# Type checking and linting
ruff check .
mypy model/src backend/app
```

### Frontend Quality & Build

```bash
cd frontend
npm run lint      # Run oxlint
npm run build     # Validate production bundle build
```

---

## 👥 Contributors

- **Sanyam Aggarwal** ([@sanyamaggarwal4](https://github.com/sanyamaggarwal4))
- **Anany Pratyush** ([@Anany1014](https://github.com/Anany1014))
- **Ojaswini** ([@ojaswiniii07-ai](https://github.com/ojaswiniii07-ai))

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
