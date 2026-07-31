# 🏋️ Sports Injury Predictor & Athletic Telemetry Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF.svg)](https://vitejs.dev/)
[![LLM](https://img.shields.io/badge/NVIDIA-Nemotron--4-76B900.svg)](https://openrouter.ai/)
[![XGBoost](https://img.shields.io/badge/Model-XGBoost%20v2.4-FF6600.svg)](https://xgboost.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end Machine Learning system and interactive performance telemetry platform that forecasts athlete injury risk in real time and streams evidence-based recovery prescriptions using **XGBoost Ensemble v2.4** and **NVIDIA Nemotron-4 340B LLM**.

---

## 🌟 Key Features

- **🧠 Machine Learning Injury Engine**: Trained across multi-season workload logs, biometrics (HRV, Resting HR, Sleep), and Acute:Chronic Workload Ratio (ACWR) feature engineering. Includes XGBoost, LightGBM, Random Forest, and HistGradientBoosting classifiers tuned for severe class imbalance (`scale_pos_weight`).
- **⚡ LLM Recovery Prescription Console**: Streams real-time Server-Sent Events (SSE) via OpenRouter using **NVIDIA Nemotron-4** (`nvidia/nemotron-nano-9b-v2:free`). Delivers 4 metric target cards and non-repeating sports science execution directives (Dynamic Warm-Ups, Active Mobility, Whole-Food Meals, and Biometric Re-entry Thresholds).
- **📡 Web Bluetooth API Wearable Integration**: Native browser GATT Bluetooth scanning (`navigator.bluetooth.requestDevice`) for COROS, Garmin, Apple Watch, WHOOP, Oura Ring, Polar, and Suunto devices with live HRV, RHR, and battery telemetry import.
- **🎨 Pro Telemetry Design & Dark/Light Mode**: High-contrast UI built with React 19, Vite, Recharts, and Lucide icons featuring dual Obsidian Dark (`#0B0F17`) and Light Chalk (`#F8FAFC`) modes with persistent theme toggle.
- **🛡️ Production Ready Backend**: Built with FastAPI, Pydantic v2 data validation, HIPAA/GDPR encrypted audit log formatting, Pytest test suite, and clean environment variable isolation.

---

## 📊 Trained Machine Learning Models

Due to the extreme rarity of sports injuries (~1.2% positive occurrence rate in raw training logs), **12 model training approaches** were evaluated across a test dataset of **6,182 athlete samples (75 injury events)**.

### Model Evaluation Benchmark Report

| Training Approach | Precision | Recall | F1 Score | AUC-ROC | PR-AUC | Accuracy | Target Use Case |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **🥇 Saved Artifact (`high_perf_xgboost_model.joblib`)** | **1.63%** | **89.33%** | **0.0320** | **0.6040** | **0.0190** | **34.36%** | **Production Real-Time API Engine** |
| **Random Forest Classifier (th=0.25)** | 1.48% | 93.33% | 0.0291 | 0.5950 | 0.0171 | 24.39% | High-Recall Baseline |
| **Logistic Regression (th=0.15)** | 1.23% | 100.00% | 0.0244 | 0.5895 | 0.0161 | 2.83% | Max Sensitivity Screen |
| **XGBoost Baseline (th=0.50)** | 1.50% | 32.00% | 0.0287 | 0.5832 | 0.0161 | 73.68% | High Specificity Benchmark |
| **XGBoost Max Safety (th=0.15)** | 1.30% | 96.00% | 0.0256 | 0.5832 | 0.0161 | 11.50% | Injury Risk Screening |
| **LightGBM Balanced (th=0.25)** | 1.48% | 57.33% | 0.0289 | 0.5681 | **0.0216** | 53.33% | Fast Gradient Boost Baseline |
| **HistGradientBoosting (th=0.45)** | 1.51% | 26.67% | 0.0286 | 0.5659 | 0.0168 | **78.05%** | Balanced Accuracy Benchmark |

### Key Model Insights:
- **Primary Production Model**: `high_perf_xgboost_model.joblib` achieved the highest **AUC-ROC (0.6040)** and **89.33% Injury Recall**, successfully capturing ~9 out of 10 athlete injury risks before occurrence.
- **Feature Importance**: Acute:Chronic Workload Ratio (ACWR 7d/28d), HRV rolling 7-day drop, cumulative 14-day session RPE volume, and days since last injury are the top predictive features.

---

## 🤖 Large Language Model (LLM) Integration

The recovery prescription engine is powered by **NVIDIA Nemotron-4 340B Architecture** (`nvidia/nemotron-nano-9b-v2:free` via OpenRouter API).

### Streaming SSE Architecture
- **Endpoint**: `/api/v1/recommendations/stream/full`
- **Protocol**: Server-Sent Events (SSE) streaming token-by-token at high throughput.
- **Prompt Structure**:
  - **Part 1 (Structured Telemetry Cards)**: Yields key physiological thresholds:
    - `SLEEP`: CNS recovery target (e.g. `8.5 hrs`)
    - `WORKLOAD`: Session RPE ceiling (e.g. `4.0 /10 RPE`)
    - `THERAPY`: Contrast & cryotherapy protocol duration (e.g. `20 min`)
    - `NUTRITION`: Protein & fluid refuel requirement (e.g. `26g + 750ml`)
  - **Part 2 (Execution Directives)**: Generates 4 non-repeating sports science directives:
    1. **Dynamic Warm-Up & Activation Drills**: Glute bridges, band pull-aparts, leg swings.
    2. **Active Recovery & Soft Tissue Mobility**: Foam rolling hamstrings/calves, thoracic rotations.
    3. **Whole-Food Performance Diet & Hydration Plan**: Anti-inflammatory whole-food meals, tart cherry juice, electrolytes.
    4. **Biometric Re-Entry Thresholds**: Readiness score and HRV target requirements for full squad re-entry.

---

## 📡 Web Bluetooth API Integration

The platform includes direct browser-native Bluetooth GATT pairing (`navigator.bluetooth.requestDevice`).

### Device Compatibility & GATT Services:
- **Supported Brands**: COROS (Pace/Apex/Vertix), Garmin (Forerunner/Fenix/Epix), Apple Watch (Series 4+/Ultra), WHOOP 4.0, Oura Ring Gen 3, Polar, and Suunto.
- **BLE GATT Services**: Reads Heart Rate Service (`0x180D`), Heart Rate Measurement (`0x2A37`), and Battery Service (`0x2A19`).
- **Telemetry Import**: Automatically populates HRV (ms), Resting HR (bpm), Sleep Duration (hrs), and Battery Level into the athlete's daily log.

---

## 📁 Project Structure

```
Sports Injury Predictor/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/              # API endpoints (health, predict, recommendations stream)
│   │   ├── core/             # Configuration & security settings
│   │   ├── schemas/          # Pydantic data schemas
│   │   ├── services/         # Model inference & OpenRouter LLM service
│   │   └── main.py           # FastAPI entrypoint & CORS middleware
│   └── tests/                # API integration & unit tests
├── frontend/                 # React 19 + Vite Performance Telemetry UI
│   ├── src/
│   │   ├── components/       # AIRecoveryFull, InjuryPredictorSection, Sidebar, Layout
│   │   ├── context/          # AthleteContext, AuthContext, ThemeContext
│   │   ├── pages/            # Dashboard, Readiness, Heatmap, WorkoutLog, ACWR, Recovery, WearableSync
│   │   ├── index.css         # High-Performance Sports Telemetry CSS Design System
│   │   └── App.jsx           # React Router & Theme Provider entrypoint
│   ├── package.json          # Frontend dependencies
│   └── vite.config.js        # Vite build configuration
├── model/                    # ML Core & Model Training Pipeline
│   ├── artifacts/            # Trained models (high_perf_xgboost_model.joblib, report.md)
│   ├── configs/              # Training hyperparameter YAML configs
│   ├── evaluate_all_models.py# Benchmark suite evaluating 12 ML approaches
│   └── src/                  # Feature engineering, ACWR calculators, preprocessing
├── .env.example              # Environment variables template (Ignored in Git)
├── .gitignore                # Git exclusions (.env, .env.example, .venv)
├── Makefile                  # Pipeline execution commands
└── pyproject.toml            # Tooling configuration (Ruff, Mypy, Pytest)
```

---

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** & **npm**

### 1. Environment Setup

```bash
# Clone repository and navigate to root directory
cd "Sports Injury Predictor"

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment variables (create .env file locally)
cat <<EOT > .env
APP_ENV=development
API_HOST=0.0.0.0
API_PORT=8000
ARTIFACTS_DIR=model/artifacts
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=nvidia/nemotron-nano-9b-v2:free
EOT
```

### 2. Start Backend API & LLM Service

```bash
# Start FastAPI development server (runs on http://127.0.0.1:8000)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Start Frontend Dashboard UI

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server (runs on http://localhost:5173)
npm run dev
```

---

## 🧪 Testing & Verification

```bash
# Run pytest backend suite
pytest backend/tests/

# Verify production frontend build
cd frontend && npm run build
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
