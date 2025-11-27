# 🚀 ML Production System - Complete Data Pipeline

A production-grade ML pipeline with data ingestion, validation, predictions, monitoring, and auto-retraining.

## 📋 Project Overview

**9 Phases of ML Production:**

1. **Phase 1-4**: PostgreSQL, ML Model, FastAPI, Monitoring
2. **Phase 5**: Automated Data Ingestion & Validation
3. **Phase 6**: Real-time Model Predictions
4. **Phase 7**: Drift Detection & Alerts
5. **Phase 8**: Auto-Retraining & Deployment
6. **Phase 9**: Analytics & Business Intelligence

## 🛠️ **Technologies Used**

- **Database**: PostgreSQL
- **ML Framework**: Scikit-learn (Random Forest)
- **API**: FastAPI + Uvicorn
- **Orchestration**: Apache Airflow
- **Dashboard**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Language**: Python 3.12

## 🚀 **Quick Start**

### Prerequisites
```bash
# Python 3.12+
python --version

# PostgreSQL running
brew services start postgresql
```

### Installation
```bash
cd /Users/meharuu/Desktop/work/ml-production-system

# Activate conda environment
source /opt/miniconda3/envs/yo/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Start All Services (4 Terminals)

**Terminal 1: PostgreSQL**
```bash
brew services start postgresql
```

**Terminal 2: FastAPI Backend**
```bash
cd /Users/meharuu/Desktop/work/ml-production-system
source /opt/miniconda3/envs/yo/bin/activate
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3: Airflow Orchestration**
```bash
export AIRFLOW_HOME=/Users/meharuu/Desktop/work/ml-production-system/airflow
export no_proxy='*'
airflow standalone
```
- Visit: http://localhost:8080
- Enable all 5 DAGs

**Terminal 4: Streamlit Dashboard**
```bash
streamlit run /Users/meharuu/Desktop/work/ml-production-system/streamlit_app.py
```
- Visit: http://localhost:8501

---

## 📊 **System Architecture**
```
Raw Data (10,000 files)
    ↓
[Phase 5] data_ingestion_pipeline (Every 1 min)
    ↓ Validates & Splits
good_data/ ← valid rows
bad_data/ ← invalid rows
    ↓
[Phase 6] model_prediction_pipeline (Every 2 mins)
    ↓ Makes predictions
model_predictions table
    ↓
[Phase 7] model_monitoring_pipeline (Every 1 hour)
    ↓ Detects drift
model_monitoring table
    ↓
[Phase 8] model_retraining_pipeline (Every Sunday)
    ↓ Retrains & deploys
new_model.pkl
    ↓
[Phase 9] analytics_dashboard_pipeline (Daily 6 AM)
    ↓ Generates reports
reports/ + executive_summary.json
```

---

## 📁 **Project Structure**
```
ml-production-system/
├── src/
│   ├── api/              # FastAPI backend
│   ├── database/         # Database models
│   └── ml/               # ML training code
├── dags/                 # Airflow DAGs (5 files)
│   ├── data_ingestion_dag.py
│   ├── model_prediction_dag.py
│   ├── model_monitoring_dag.py
│   ├── model_retraining_dag.py
│   └── analytics_dashboard_dag.py
├── model/                # Trained models & preprocessor
├── data/
│   ├── raw_data/         # 10,000 input CSV files
│   ├── good_data/        # Valid data after processing
│   ├── bad_data/         # Invalid data
│   └── predictions/      # Prediction outputs
├── airflow/              # Airflow configuration
├── reports/              # Analytics & reports
├── streamlit_app.py      # Dashboard
└── README.md
```

---

## 🎯 **Key Features**

- ✅ **Automated Data Pipeline**: 10,000 files processed automatically
- ✅ **Data Validation**: 8 validation rules with error tracking
- ✅ **Real-time Predictions**: Every 2 minutes on validated data
- ✅ **Performance Monitoring**: Drift detection & alerts
- ✅ **Auto-Retraining**: Weekly model updates
- ✅ **Analytics Dashboard**: KPIs, trends, alerts
- ✅ **Production Ready**: Logging, error handling, recovery

---

## 📊 **Dashboard Features**

**Streamlit UI (http://localhost:8501):**
- 📊 Overview with KPIs
- 📈 Data quality metrics
- 🤖 Prediction analytics
- ⚠️ System alerts
- 🔮 Interactive prediction tool
- 📋 Executive reports

---

## 🔧 **Configuration**

**Database**: `postgresql://meharuu@localhost:5432/ml_production`

**Model Features**:
- road_type, num_lanes, curvature, speed_limit
- lighting, weather, time_of_day, num_reported_accidents

**Airflow DAGs** (Enable in UI):
1. `data_ingestion_pipeline` - Every 1 minute
2. `model_prediction_pipeline` - Every 2 minutes
3. `model_monitoring_pipeline` - Every 1 hour
4. `model_retraining_pipeline` - Every Sunday
5. `analytics_dashboard_pipeline` - Daily 6 AM

---

## 📈 **Expected Performance**

- **Processing**: ~1 file per minute = 10,000 files in 7 days
- **Data Quality**: ~90% valid rows
- **Predictions**: ~450 per minute
- **Model Accuracy**: ~0.7+ R² score

---

## 🚨 **Troubleshooting**

**Airflow won't start:**
```bash
rm -rf /Users/meharuu/Desktop/work/ml-production-system/airflow/airflow.db
airflow standalone
```

**Database connection error:**
```bash
psql -U meharuu -d ml_production -c "SELECT 1;"
```

**API not responding:**
```bash
curl http://localhost:8000/health
```

**Streamlit error:**
```bash
pip install --upgrade streamlit
streamlit run streamlit_app.py
```

---

## 📝 **API Documentation**

**Health Check**:
```bash
GET http://localhost:8000/health
```

**Make Prediction**:
```bash
POST http://localhost:8000/predict
Content-Type: application/json

{
  "features": {
    "road_type": "highway",
    "num_lanes": 3,
    "curvature": 5,
    "speed_limit": 90,
    "lighting": "daylight",
    "weather": "clear",
    "time_of_day": "day",
    "num_reported_accidents": 0
  }
}
```

---

## 📊 **Database Schema**

- `ingestion_statistics` - Track data ingestion batches
- `model_predictions` - Store predictions
- `model_monitoring` - Monitoring metrics
- `model_deployments` - Model version history
- `system_reports` - Analytics reports

---

## 🎓 **Learning Resources**

- Airflow: https://airflow.apache.org/docs/
- FastAPI: https://fastapi.tiangolo.com/
- Streamlit: https://docs.streamlit.io/
- PostgreSQL: https://www.postgresql.org/docs/

---

## 📄 **License**

MIT License

---

## 👤 **Author**

Created as a complete ML production system demonstrating best practices.

---

**Status**: ✅ Production Ready

**Last Updated**: 2025-11-24
