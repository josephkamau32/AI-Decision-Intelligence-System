# 🚀 Decisera - AI Decision Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)](https://www.typescriptlang.org/)

> **Transform Raw Data into Intelligent Decisions with AI**

An enterprise-grade, production-ready analytics platform that automates machine learning workflows, provides natural language insights through AI copilot, and delivers explainable predictions with zero code required.

![Decisera](https://img.shields.io/badge/Status-Production%20Ready-success)

## 🌐 Live Demo

**🚀 [Try Decisera Now](https://decisera.vercel.app/)** - Experience the platform in action!

> **Demo Access:**
> Please contact the administrator to provision a secure demo account.

---

## ✨ Features

### 🤖 **AutoML & Intelligent Forecasting**
- **12+ ML Algorithms**: Automatic model selection (RandomForest, XGBoost, LightGBM, CatBoost, etc.)
- **Time-Series Forecasting**: Prophet for trend analysis, LSTM for complex patterns
- **Hyperparameter Tuning**: Optuna-powered optimization for peak performance
- **Auto Task Detection**: Automatically identifies regression, classification, or time-series tasks

### 📊 **Data Analytics**
- **Automated Data Profiling**: Instant insights into distributions, correlations, and anomalies
- **Interactive Visualizations**: Plot.ly-powered charts, distributions, and feature importance
- **Dataset Management**: Upload CSV, Excel, Parquet files with drag-and-drop
- **Data Quality Checks**: Missing values, outliers, and data drift detection

### 🧠 **AI Copilot**
- **Natural Language Queries**: Ask questions about your data in plain English
- **Contextual Insights**: Get explanations, recommendations, and predictions
- **Conversation History**: Maintain context across multiple questions
- **Confidence Scoring**: Know how reliable each answer is

### 🔍 **Explainable AI**
- **SHAP Values**: Understand which features drive predictions
- **Feature Importance**: Ranked list of most impactful variables
- **Decision Paths**: Visualize how models make decisions
- **Model Interpretation**: Trust through transparency

### 🏢 **Enterprise-Grade Infrastructure**
- **Kubernetes Ready**: Complete deployment manifests with auto-scaling
- **CI/CD Pipelines**: GitHub Actions for automated testing and deployment
- **Monitoring & Observability**: Prometheus metrics + Grafana dashboards
- **Authentication & RBAC**: JWT-based auth with role-based access control
- **API Rate Limiting**: Protect against abuse with configurable limits

### 🎨 **Modern User Interface**
- **Professional Landing Page**: Clear value proposition and feature showcase
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark/Light Mode**: User preference support
- **WCAG AA Compliant**: Accessible to all users
- **Enterprise Aesthetics**: Rivals Power BI and Tableau in visual quality

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React + TypeScript)           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Landing  │  │   Auth   │  │Dashboard │  │ Copilot  │   │
│  │   Page   │  │  Pages   │  │  & Data  │  │   Chat   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI + Python)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ AutoML   │  │ Time-    │  │   AI     │  │  Auth &  │   │
│  │ Pipeline │  │ Series   │  │ Copilot  │  │   RBAC   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure & Services                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ MLflow   │  │  Redis   │  │Prometheus│  │ Grafana  │   │
│  │(Models)  │  │ (Queue)  │  │(Metrics) │  │(Dashboards)  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- React Router for SPA navigation
- Plotly.js for interactive charts
- CSS Modules with design tokens
- Axios for API communication

**Backend:**
- FastAPI (Python 3.11+)
- Scikit-learn, XGBoost, LightGBM, CatBoost
- Prophet & PyTorch (LSTM)
- Optuna for hyperparameter tuning
- SHAP for model explainability
- OpenAI API for copilot functionality

**Infrastructure:**
- Kubernetes for orchestration
- Docker for containerization
- GitHub Actions for CI/CD
- Prometheus + Grafana for monitoring
- MLflow for experiment tracking
- Redis for task queuing

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** and npm
- **Git**

### Local Development

#### 1. Clone the Repository
```bash
git clone https://github.com/josephkamau32/AI-Decision-Intelligence-System.git
cd AI-Decision-Intelligence-System
```

#### 2. Setup Backend
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate
# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies from project root
pip install -r requirements.txt

# For development & testing dependencies, also install:
# pip install -r requirements-dev.txt

# Configure environment variables
copy .env.example .env   # Windows
cp .env.example .env     # Mac/Linux

# Edit .env with your configuration:
# - SECRET_KEY & JWT_SECRET_KEY (generate via: python -c "import secrets; print(secrets.token_urlsafe(32))")
# - GOOGLE_API_KEY (Required for Gemini AI Copilot)
# - OPENAI_API_KEY (Optional)

# Run backend server
uvicorn backend.api.main:app --reload --port 8000
# Or: python -m uvicorn backend.api.main:app --reload --port 8000
```

Backend will be available at: **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics

#### 3. Setup Frontend
```bash
# In a new terminal
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Set environment variables
copy .env.example .env  # Windows
cp .env.example .env    # Mac/Linux

# Edit .env
# REACT_APP_API_URL=http://localhost:8000

# Run frontend server
npm start
```

Frontend will be available at: **http://localhost:3000**

#### 4. First-Time Setup
1. Open http://localhost:3000 in your browser
2. Click **"Get Started Free"**
3. Register a new account
4. You'll be auto-logged in and redirected to the dashboard

---

## 📖 User Guide

### Getting Started

#### 1. Upload Your First Dataset
- Navigate to **Dashboard**
- Use the **Upload Dataset** card
- Drag & drop a CSV, Excel, or Parquet file
- Or click to browse files

**Supported Formats:**
- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)
- Parquet (`.parquet`)

#### 2. View Dataset Insights
- Go to **Datasets** page
- Click on your uploaded dataset
- See automatic profiling:
  - Data quality metrics
  - Missing values analysis
  - Distributions and correlations
  - Feature types identification

#### 3. Train ML Models
- Select your dataset
- Choose target column (what to predict)
- Choose task type or let AutoML detect it:
  - **Classification**: Predict categories
  - **Regression**: Predict numbers
  - **Time-Series**: Predict future values
- Click **Train Model**
- AutoML will:
  - Try 12+ algorithms automatically
  - Tune hyperparameters
  - Select the best model
  - Provide performance metrics

#### 4. Analyze Model Performance
- Go to **Models** page
- View accuracy, precision, recall, F1-score
- See confusion matrices (classification)
- Check R² score and MAE (regression)
- View prediction charts (time-series)

#### 5. Understand Predictions (Explainability)
- Go to **Features** page
- View SHAP values for feature importance
- See which features drive predictions
- Understand model decision-making

#### 6. Ask AI Copilot
- Go to **AI Copilot** page
- Ask questions like:
  - "What are the key drivers of customer churn?"
  - "Forecast sales for next quarter"
  - "Which features are most important?"
  - "Explain this prediction"
- Get natural language answers with confidence scores

---

## 🔐 Authentication & Security

### User Roles
- **Admin**: Full access, user management
- **User**: Standard access, can train models
- **Viewer**: Read-only access

### API Authentication
```bash
# Register
POST /api/v1/auth/register
{
  "username": "yourname",
  "email": "your@email.com",
  "password": "SecurePassword123!"
}

# Login
POST /api/v1/auth/login
{
  "username": "yourname",
  "password": "SecurePassword123!"
}

# Returns JWT token
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}

# Use token in headers
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Security Features
- ✅ JWT tokens with 30-minute expiry
- ✅ Password hashing with bcrypt
- ✅ Role-based access control (RBAC)
- ✅ API rate limiting (60 req/min default)
- ✅ CORS protection
- ✅ Input validation
- ✅ SQL injection prevention

---

## 🧪 Testing

### Backend Tests
```bash
# Run all unit tests from project root
pytest -v

# Run with test coverage
pytest -v --cov=backend/api --cov=backend/ml
```

### Frontend Tests
```bash
cd frontend
npm test
```

---

## 🐳 Docker Deployment

### Build Images
```bash
# Backend
docker build -t ai-decision-backend:latest ./backend

# Frontend
docker build -t ai-decision-frontend:latest ./frontend
```

### Run with Docker Compose
```bash
docker-compose up -d
```

Services:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- MLflow: http://localhost:5000
- Grafana: http://localhost:3001

---

## ☸️ Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (GKE, EKS, AKS, or local with minikube)
- kubectl configured
- Docker images pushed to registry

### Quick Deploy
```bash
# 1. Create secrets
kubectl create secret generic ai-secrets \
  --from-literal=secret_key=$(openssl rand -hex 32) \
  --from-literal=jwt_secret_key=$(openssl rand -hex 32) \
  --from-literal=openai_api_key=your-openai-key

# 2. Apply manifests
kubectl apply -f k8s/

# 3. Check status
kubectl get pods
kubectl get services

# 4. Access application
kubectl port-forward svc/frontend-service 3000:80
```

### Detailed Guide
See [k8s/README.md](k8s/README.md) for comprehensive Kubernetes deployment instructions.

---

## 📊 Monitoring

### Prometheus Metrics
Available at: http://localhost:8000/metrics

**Key Metrics:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `ml_training_duration_seconds` - Model training time
- `ml_model_accuracy` - Model performance
- `ml_predictions_total` - Prediction count
- `data_drift_detected` - Drift detection events

### Grafana Dashboards
Access Grafana at: http://localhost:3001
- Default credentials: `admin` / `admin`
- Pre-configured dashboard: **ML Operations**

**Dashboard Panels:**
- HTTP Request Rate & Latency
- Model Training Duration
- Prediction Accuracy Trends
- Data Drift Alerts
- System Resource Usage

---

## 🛠️ Development

### Project Structure
```
AI-Decision-Intelligence-System/
├── backend/                 # FastAPI backend
│   ├── api/                # API routes
│   ├── ml/                 # ML pipelines
│   ├── schemas/            # Pydantic models
│   ├── services/           # Business logic
│   ├── utils/              # Utilities
│   └── requirements.txt    # Python deps
├── frontend/               # React frontend
│   ├── src/
│   │   ├── pages/          # Page components
│   │   ├── components/     # Reusable components
│   │   ├── context/        # React context
│   │   ├── services/       # API services
│   │   └── styles/         # CSS & design tokens
│   └── package.json        # npm deps
├── scripts/                # Developer & diagnostic utilities (e.g. check_openai_key.py)
├── k8s/                    # Kubernetes manifests
├── grafana/                # Grafana dashboards
├── .github/workflows/      # CI/CD pipelines
└── docker-compose.yml      # Local deployment
```

### Design System
The UI uses a comprehensive design system with:
- **WCAG AA Compliant Colors**
- **Typography Scale** (Inter + Poppins)
- **8px Spacing System**
- **Semantic Tokens**
- **Responsive Breakpoints**

See `frontend/src/styles/design-tokens.css` for all variables.

### Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 API Documentation

### Interactive API Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Datasets
```bash
# Upload dataset
POST /api/v1/datasets/upload

# List datasets
GET /api/v1/datasets

# Get dataset details
GET /api/v1/datasets/{dataset_id}

# Delete dataset
DELETE /api/v1/datasets/{dataset_id}
```

#### Models
```bash
# Train model
POST /api/v1/models/train

# List models
GET /api/v1/models

# Get model details
GET /api/v1/models/{model_id}

# Make prediction
POST /api/v1/models/{model_id}/predict
```

#### AI Copilot
```bash
# Ask question
POST /api/v1/copilot/ask
{
  "question": "What drives customer churn?",
  "dataset_id": "optional-dataset-id",
  "model_id": "optional-model-id"
}
```

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check virtual environment
which python  # Should point to .venv

# Check port availability
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows
```

### Frontend won't compile
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps

# Check Node version
node --version  # Should be 18+

# Clear browser cache
# Use incognito mode or Ctrl+Shift+Delete
```

### OpenAI API Key Diagnostics
- Run `python scripts/check_openai_key.py` to verify that your `OPENAI_API_KEY` is loaded and can authenticate with OpenAI.

### Models not training
- Check dataset format (CSV must have header row)
- Verify target column exists
- Ensure sufficient data (minimum 10 rows)
- Check backend logs for errors

### AI Copilot not responding
- Verify `GOOGLE_API_KEY` in project root `.env` (required for Gemini Copilot)
- Verify `OPENAI_API_KEY` in `.env` if using OpenAI-based workflows
- Check API quota/billing at Google Cloud Console / OpenAI Platform
- View backend logs for API errors

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

**Technologies Used:**
- FastAPI for high-performance API
- React for modern UI
- Scikit-learn for ML algorithms
- Prophet for time-series forecasting
- SHAP for explainability
- OpenAI for natural language understanding
- Kubernetes for orchestration
- Prometheus & Grafana for monitoring

---

## 📞 Support

**Issues**: [GitHub Issues](https://github.com/josephkamau32/AI-Decision-Intelligence-System/issues)

**Questions**: Open a discussion on GitHub

---

## 🗺️ Roadmap

- [ ] Real-time model retraining
- [ ] Multi-user collaboration
- [ ] Advanced data preprocessing
- [ ] Custom model deployment
- [ ] Mobile app (React Native)
- [ ] Streaming data support
- [ ] Advanced NLP models
- [ ] Computer vision support

---

<div align="center">

**Built with ❤️ for Data Teams Worldwide**

[⬆ Back to Top](#-ai-decision-intelligence-platform)

</div>