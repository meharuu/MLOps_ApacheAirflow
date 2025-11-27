from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
import os, pandas as pd, logging, json
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

RAW_DATA_DIR = '/Users/meharuu/Desktop/work/ml-production-system/data/raw_data'
GOOD_DATA_DIR = '/Users/meharuu/Desktop/work/ml-production-system/data/good_data'
BAD_DATA_DIR = '/Users/meharuu/Desktop/work/ml-production-system/data/bad_data'
DATABASE_URL = 'postgresql://meharuu@localhost:5432/ml_production'

VALID_ROAD_TYPES = ['highway', 'rural', 'urban']

default_args = {'owner': 'ml-team', 'retries': 1, 'retry_delay': timedelta(minutes=1), 'start_date': datetime(2025, 1, 1)}

dag = DAG('data_ingestion_pipeline', default_args=default_args, description='Ingest and validate data', schedule='* * * * *', catchup=False, tags=['data-pipeline'])

def read_next_file(**context):
    logger.info("📖 Reading next file...")
    files = sorted([f for f in os.listdir(RAW_DATA_DIR) if f.endswith('.csv')])
    if not files: return None
    file_path = os.path.join(RAW_DATA_DIR, files[0])
    df = pd.read_csv(file_path)
    logger.info(f"✅ Loaded: {files[0]} ({len(df)} rows)")
    context['task_instance'].xcom_push(key='file_path', value=file_path)
    context['task_instance'].xcom_push(key='file_name', value=files[0])
    context['task_instance'].xcom_push(key='total_rows', value=len(df))
    return file_path

def validate_data(**context):
    logger.info("🔍 Validating...")
    ti = context['task_instance']
    file_path = ti.xcom_pull(task_ids='read_file', key='file_path')
    if not file_path: return None
    df = pd.read_csv(file_path)
    invalid_rows = pd.Series([False] * len(df), index=df.index)
    errors = {}
    if 'road_type' in df.columns:
        bad = df['road_type'].notna() & ~df['road_type'].isin(VALID_ROAD_TYPES)
        if bad.sum() > 0:
            errors['road_type'] = int(bad.sum())
            invalid_rows = invalid_rows | bad
    if 'speed_limit' in df.columns:
        bad = df['speed_limit'] < 0
        if bad.sum() > 0:
            errors['speed_limit'] = int(bad.sum())
            invalid_rows = invalid_rows | bad
    valid_count = (~invalid_rows).sum()
    invalid_count = invalid_rows.sum()
    logger.info(f"✅ Valid: {valid_count}, Invalid: {invalid_count}")
    ti.xcom_push(key='valid_rows', value=valid_count)
    ti.xcom_push(key='invalid_rows', value=invalid_count)
    ti.xcom_push(key='errors', value=errors)
    ti.xcom_push(key='invalid_mask', value=invalid_rows.tolist())

def split_data(**context):
    logger.info("✂️  Splitting...")
    ti = context['task_instance']
    file_path = ti.xcom_pull(task_ids='read_file', key='file_path')
    file_name = ti.xcom_pull(task_ids='read_file', key='file_name')
    invalid_mask = ti.xcom_pull(task_ids='validate_data', key='invalid_mask')
    if not file_path: return None
    df = pd.read_csv(file_path)
    good_df = df[~pd.Series(invalid_mask)]
    bad_df = df[pd.Series(invalid_mask)]
    os.makedirs(GOOD_DATA_DIR, exist_ok=True)
    os.makedirs(BAD_DATA_DIR, exist_ok=True)
    if len(good_df) > 0:
        good_df.to_csv(os.path.join(GOOD_DATA_DIR, f'good_{file_name}'), index=False)
    if len(bad_df) > 0:
        bad_df.to_csv(os.path.join(BAD_DATA_DIR, f'bad_{file_name}'), index=False)

def save_stats(**context):
    logger.info("💾 Saving...")
    ti = context['task_instance']
    file_name = ti.xcom_pull(task_ids='read_file', key='file_name')
    total = ti.xcom_pull(task_ids='read_file', key='total_rows')
    valid = ti.xcom_pull(task_ids='validate_data', key='valid_rows')
    invalid = ti.xcom_pull(task_ids='validate_data', key='invalid_rows')
    errors = ti.xcom_pull(task_ids='validate_data', key='errors')
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("INSERT INTO ingestion_statistics (batch_id, total_rows, valid_rows, invalid_rows, error_types, processed_at) VALUES (:batch_id, :total_rows, :valid_rows, :invalid_rows, :error_types, NOW())"), {'batch_id': file_name, 'total_rows': total, 'valid_rows': valid, 'invalid_rows': invalid, 'error_types': json.dumps(errors) if errors else '{}'})
            conn.commit()
        logger.info(f"✅ Saved")
    except Exception as e:
        logger.error(f"❌ {e}")

def delete_file(**context):
    logger.info("🗑️  Deleting...")
    ti = context['task_instance']
    file_path = ti.xcom_pull(task_ids='read_file', key='file_path')
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

with dag:
    read_file = PythonOperator(task_id='read_file', python_callable=read_next_file)
    validate_data = PythonOperator(task_id='validate_data', python_callable=validate_data)
    split_data = PythonOperator(task_id='split_data', python_callable=split_data)
    save_stats = PythonOperator(task_id='save_statistics', python_callable=save_stats)
    delete_file = PythonOperator(task_id='delete_processed_file', python_callable=delete_file)
    read_file >> validate_data >> split_data >> save_stats >> delete_file
