# AI Decision Intelligence System

A production-grade, scalable AI Decision Intelligence Platform with AutoML, real-time inference, SHAP explainability, and AI Copilot.

## 🎯 Overview

This platform enables users to:
- **Upload datasets** (CSV, Excel, JSON, Parquet)
- **Auto-profile data** with quality analysis
- **Train ML models** using AutoML (10+ algorithms)
- **Make predictions** (single & batch)
- **Explain results** using SHAP
- **Chat with AI Copilot** for data insights

## 🏗️ Architecture

- **Frontend**: React + TypeScript, modern UI with dark/light themes
- **Backend**: FastAPI, async endpoints, MLflow integration
- **ML Engine**: Scikit-learn, XGBoost, LightGBM, SHAP
- **MLOps**: MLflow for experiments, Celery for async tasks, Redis for caching
- **Deployment**: Docker containers, Docker Compose

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node 18+
- Redis (optional, for caching)
- Docker & Docker Compose (for containerized deployment)

### Option 1: Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run backend
uvicorn api.main:app --reload --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env
# Edit .env (set REACT_APP_API_URL=http://localhost:8000)

# Run frontend
PORT=3001 npm start

# Or on Windows:
$env:PORT=3001; npm start
```

Access the app at: **http://localhost:3001**

### Option 2: Docker Compose (Full Stack)

```bash
# Build and run all services
docker-compose up --build

# Access:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - MLflow UI: http://localhost:5000
```

## 📁 Project Structure

```
├── frontend/                # React TypeScript app
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── pages/           # Page components
│   │   ├── context/         # React contexts
│   │   ├── services/        # API services
│   │   └── styles/          # CSS and design system
│   └── Dockerfile
├── backend/                 # FastAPI backend
│   ├── api/                 # API routes
│   ├── ml/                  # ML engine
│   │   ├── automl.py        # AutoML training
│   │   ├── inference.py     # Predictions
│   │   ├── explainability.py # SHAP
│   │   └── data_*.py        # Data processing
│   ├── services/            # Business logic
│   ├── tasks.py             # Celery async tasks
│   ├── copilot/             # AI Copilot tools
│   └── Dockerfile
└── docker-compose.yml       # Full stack deployment
```

## 🔧 Key Features

### 1. AutoML Training

Train models automatically with 10+ algorithms:
- **Classification**: Logistic Regression, Random Forest, XGBoost, LightGBM, Gradient Boosting
- **Regression**: Linear, Ridge, Lasso, Random Forest, XGBoost, Gradient Boosting

```bash
POST /api/v1/models/train
{
  "dataset_id": "dataset_123",
  "target_column": "target",
  "task_type": "auto",
  "test_size": 0.2
}
```

### 2. Inference

Make predictions:

```bash
# Single prediction
POST /api/v1/models/predict
{
  "model_id": "model_123",
  "data": {"feature1": 10, "feature2": 20}
}

# Batch predictions
POST /api/v1/models/predict/batch
{
  "model_id": "model_123",
  "data": [{"feature1": 10}, {"feature1": 15}]
}
```

### 3. Explainability (SHAP)

Understand model decisions:

```bash
# Global feature importance
GET /api/v1/models/{model_id}/explain/global?top_n=10

# Explain specific prediction
POST /api/v1/models/{model_id}/explain/local
{
  "instance": {"feature1": 10, "feature2": 20}
}

# Get SHAP plots
GET /api/v1/models/{model_id}/explain/plots?plot_type=summary
```

### 4. Data Profiling

Auto-analyze datasets:
- Auto-detect column types
- Suggest target variable
- Identify outliers
- Find quality issues

## 📊 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/datasets/upload` | POST | Upload dataset |
| `/api/v1/datasets/` | GET | List datasets (paginated) |
| `/api/v1/models/train` | POST | Train AutoML model |
| `/api/v1/models/tasks/{task_id}/status` | GET | Check training status |
| `/api/v1/models/predict` | POST | Single prediction |
| `/api/v1/models/predict/batch` | POST | Batch predictions |
| `/api/v1/models/{id}/explain/global` | GET | Feature importance |
| `/api/v1/models/{id}/explain/local` | POST | Explain prediction |

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_ml_core.py -v

# With coverage
pytest --cov=ml --cov-report=html
```

## 🌟 Features Implemented

### Core ML
- ✅ AutoML with 10+ models
- ✅ Auto task detection (classification/regression)
- ✅ Cross-validation
- ✅ MLflow experiment tracking
- ✅ Model versioning & registry

### Inference
- ✅ Real-time predictions
- ✅ Batch predictions
- ✅ Confidence scores
- ✅ Model loading (file, MLflow, URI)

### Explainability
- ✅ SHAP global importance
- ✅ SHAP local explanations
- ✅ Summary plots
- ✅ Feature importance charts

### Frontend
- ✅ Modern UI with dark/light themes
- ✅ Responsive design
- ✅ Dashboard with stats
- ✅ Model performance visualization
- ✅ Feature importance charts
- ✅ AI Copilot chat interface
- ✅ Drag-and-drop upload

### Backend
- ✅ Async background tasks (Celery)
- ✅ Rate limiting
- ✅ Request logging
- ✅ Security headers
- ✅ Redis caching
- ✅ Input validation
- ✅ Comprehensive error handling

## 🔒 Security

- CORS configuration (env-based)
- Rate limiting (60 req/min)
- Input validation & sanitization
- Security headers (XSS, clickjacking protection)
- Auto-generated secure secrets

## 📝 Environment Variables

### Backend (.env)

```env
DEBUG_MODE=true
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0
MLFLOW_TRACKING_URI=http://localhost:5000
SECRET_KEY=auto-generated
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:8000
PORT=3001
```

## 🚢 Deployment

### Production Build

```bash
# Frontend
cd frontend
npm run build

# Serve with nginx or serve
npx serve -s build

# Backend
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment

```bash
# Build images
docker-compose build

# Run in production mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🛠️ Development

### Running Celery Worker

```bash
cd backend
celery -A celery_app worker --loglevel=info
```

### MLflow UI

```bash
mlflow ui --port 5000
```

## 📚 Documentation

- [Implementation Plan](docs/implementation_plan.md)
- [Gap Analysis](docs/gap_analysis.md)
- [Walkthrough](docs/walkthrough.md)
- [API Reference](http://localhost:8000/docs)

## 🤝 Contributing

This is a production-ready AI platform. Future enhancements:
- [ ] Advanced hyperparameter tuning (Optuna)
- [ ] Time-series models (Prophet, LSTM)
- [ ] Model monitoring & drift detection
- [ ] Complete LLM Copilot integration
- [ ] Kubernetes deployment manifests
- [ ] CI/CD pipeline

## 📊 Status

- **Core ML**: 100% ✅
- **Frontend UI**: 95% ✅
- **Backend API**: 90% ✅
- **Production Ready**: 75% ⚠️

## 📄 License

MIT License

## 🙏 Credits

Built with:
- FastAPI
- React
- Scikit-learn
- XGBoost
- LightGBM
- SHAP
- MLflow
- Celery
- Redis