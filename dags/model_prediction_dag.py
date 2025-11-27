from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
import os, pandas as pd, logging, joblib
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

GOOD_DATA_DIR = '/Users/meharuu/Desktop/work/ml-production-system/data/good_data'
PREDICTIONS_DIR = '/Users/meharuu/Desktop/work/ml-production-system/data/predictions'
MODEL_PATH = '/Users/meharuu/Desktop/work/ml-production-system/model/trained_model.pkl'
PREPROCESSOR_PATH = '/Users/meharuu/Desktop/work/ml-production-system/model/preprocessor.pkl'
DATABASE_URL = 'postgresql://meharuu@localhost:5432/ml_production'

default_args = {'owner': 'ml-team', 'retries': 1, 'retry_delay': timedelta(minutes=2), 'start_date': datetime(2025, 1, 1)}

dag = DAG('model_prediction_pipeline', default_args=default_args, description='Make predictions on good data', schedule='*/2 * * * *', catchup=False, tags=['model', 'predictions'])

def read_good_file(**context):
    logger.info("📖 Reading good data file...")
    files = sorted([f for f in os.listdir(GOOD_DATA_DIR) if f.endswith('.csv')])
    if not files:
        logger.warning("❌ No good data files found")
        return None
    
    file_path = os.path.join(GOOD_DATA_DIR, files[0])
    df = pd.read_csv(file_path)
    logger.info(f"✅ Loaded: {files[0]} ({len(df)} rows)")
    
    context['task_instance'].xcom_push(key='file_path', value=file_path)
    context['task_instance'].xcom_push(key='file_name', value=files[0])
    context['task_instance'].xcom_push(key='n_rows', value=len(df))
    return file_path

def make_predictions(**context):
    logger.info("🤖 Making predictions...")
    ti = context['task_instance']
    file_path = ti.xcom_pull(task_ids='read_good_file', key='file_path')
    file_name = ti.xcom_pull(task_ids='read_good_file', key='file_name')
    
    if not file_path:
        return None
    
    # Load model and preprocessor
    model = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    
    # Read data
    df = pd.read_csv(file_path)
    
    # Preprocess
    X_scaled = preprocessor.transform(df)
    
    # Predict
    predictions = model.predict(X_scaled)
    
    logger.info(f"✅ Made {len(predictions)} predictions")
    logger.info(f"   Mean risk: {predictions.mean():.4f}")
    logger.info(f"   Min risk: {predictions.min():.4f}")
    logger.info(f"   Max risk: {predictions.max():.4f}")
    
    # Add predictions to dataframe
    df['predicted_accident_risk'] = predictions
    
    ti.xcom_push(key='predictions_df', value=df.to_json())
    ti.xcom_push(key='mean_risk', value=float(predictions.mean()))
    
    return len(predictions)

def save_predictions(**context):
    logger.info("💾 Saving predictions...")
    ti = context['task_instance']
    file_name = ti.xcom_pull(task_ids='read_good_file', key='file_name')
    predictions_json = ti.xcom_pull(task_ids='make_predictions', key='predictions_df')
    mean_risk = ti.xcom_pull(task_ids='make_predictions', key='mean_risk')
    n_rows = ti.xcom_pull(task_ids='read_good_file', key='n_rows')
    
    # Save predictions file
    os.makedirs(PREDICTIONS_DIR, exist_ok=True)
    df = pd.read_json(predictions_json)
    pred_file = os.path.join(PREDICTIONS_DIR, f'predictions_{file_name}')
    df.to_csv(pred_file, index=False)
    logger.info(f"✅ Saved predictions: {pred_file}")
    
    # Save to database
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO model_predictions 
                (batch_id, total_rows, mean_risk_score, min_risk_score, max_risk_score, created_at)
                VALUES (:batch_id, :total_rows, :mean_risk, :min_risk, :max_risk, NOW())
            """), {
                'batch_id': file_name,
                'total_rows': n_rows,
                'mean_risk': float(df['predicted_accident_risk'].mean()),
                'min_risk': float(df['predicted_accident_risk'].min()),
                'max_risk': float(df['predicted_accident_risk'].max())
            })
            conn.commit()
        logger.info(f"✅ Predictions saved to database")
    except Exception as e:
        logger.error(f"❌ Error: {e}")

def delete_good_file(**context):
    logger.info("🗑️  Deleting processed good file...")
    ti = context['task_instance']
    file_path = ti.xcom_pull(task_ids='read_good_file', key='file_path')
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"✅ Deleted")

with dag:
    read_good_file = PythonOperator(task_id='read_good_file', python_callable=read_good_file)
    make_predictions = PythonOperator(task_id='make_predictions', python_callable=make_predictions)
    save_predictions = PythonOperator(task_id='save_predictions', python_callable=save_predictions)
    delete_good_file = PythonOperator(task_id='delete_good_file', python_callable=delete_good_file)
    
    read_good_file >> make_predictions >> save_predictions >> delete_good_file
