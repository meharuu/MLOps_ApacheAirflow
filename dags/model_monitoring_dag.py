from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
import pandas as pd, logging, json
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

DATABASE_URL = 'postgresql://meharuu@localhost:5432/ml_production'

default_args = {'owner': 'ml-team', 'retries': 1, 'retry_delay': timedelta(minutes=5), 'start_date': datetime(2025, 1, 1)}

dag = DAG('model_monitoring_pipeline', default_args=default_args, description='Monitor model performance and detect drift', schedule='0 * * * *', catchup=False, tags=['monitoring', 'drift-detection'])

def calculate_data_quality(**context):
    logger.info("📊 Calculating data quality metrics...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        query = """
        SELECT 
            COUNT(*) as total_batches,
            COALESCE(SUM(total_rows), 0) as total_rows,
            COALESCE(SUM(valid_rows), 0) as valid_rows,
            COALESCE(SUM(invalid_rows), 0) as invalid_rows,
            ROUND(100.0 * COALESCE(SUM(valid_rows), 0) / NULLIF(COALESCE(SUM(total_rows), 0), 0), 2) as quality_percentage
        FROM ingestion_statistics
        WHERE processed_at > NOW() - INTERVAL '1 hour'
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(query)).fetchone()
        
        if result:
            stats = {
                'total_batches': int(result[0]) or 0,
                'total_rows': int(result[1]) or 0,
                'valid_rows': int(result[2]) or 0,
                'invalid_rows': int(result[3]) or 0,
                'quality_percentage': float(result[4]) or 0
            }
            logger.info(f"✅ Quality: {stats['quality_percentage']}% | Batches: {stats['total_batches']}")
            
            if stats['quality_percentage'] < 80:
                logger.warning(f"⚠️  LOW DATA QUALITY: {stats['quality_percentage']}%")
            
            context['task_instance'].xcom_push(key='quality_stats', value=json.dumps(stats))
            return stats
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None

def detect_model_drift(**context):
    logger.info("🔍 Detecting model drift...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        query = """
        SELECT 
            COUNT(*) as total_predictions,
            COALESCE(AVG(mean_risk_score), 0) as avg_risk,
            COALESCE(MIN(min_risk_score), 0) as min_risk,
            COALESCE(MAX(max_risk_score), 0) as max_risk,
            COALESCE(STDDEV(mean_risk_score), 0) as stddev_risk
        FROM model_predictions
        WHERE created_at > NOW() - INTERVAL '1 hour'
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(query)).fetchone()
        
        if result and result[0] > 0:
            drift_stats = {
                'total_predictions': int(result[0]),
                'avg_risk': float(result[1]) if result[1] else 0,
                'min_risk': float(result[2]) if result[2] else 0,
                'max_risk': float(result[3]) if result[3] else 0,
                'stddev_risk': float(result[4]) if result[4] else 0
            }
            logger.info(f"✅ Avg Risk: {drift_stats['avg_risk']:.4f} | Predictions: {drift_stats['total_predictions']}")
            
            if drift_stats['avg_risk'] > 0.7:
                logger.warning(f"⚠️  HIGH RISK DETECTED: {drift_stats['avg_risk']:.4f}")
            
            context['task_instance'].xcom_push(key='drift_stats', value=json.dumps(drift_stats))
            return drift_stats
        else:
            logger.info("ℹ️  No predictions yet")
            context['task_instance'].xcom_push(key='drift_stats', value=json.dumps({}))
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None

def check_error_patterns(**context):
    logger.info("🔴 Checking error patterns...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Just count batches with errors
        query = """
        SELECT COUNT(*) as error_count
        FROM ingestion_statistics
        WHERE invalid_rows > 0
        AND processed_at > NOW() - INTERVAL '1 hour'
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(query)).fetchone()
        
        errors = {'batches_with_errors': int(result[0]) if result[0] else 0}
        
        logger.info(f"✅ Error Summary: {errors}")
        context['task_instance'].xcom_push(key='error_patterns', value=json.dumps(errors))
        return errors
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None

def save_monitoring_metrics(**context):
    logger.info("💾 Saving monitoring metrics...")
    
    ti = context['task_instance']
    quality_stats = json.loads(ti.xcom_pull(task_ids='calculate_data_quality', key='quality_stats') or '{}')
    drift_stats = json.loads(ti.xcom_pull(task_ids='detect_model_drift', key='drift_stats') or '{}')
    error_patterns = json.loads(ti.xcom_pull(task_ids='check_error_patterns', key='error_patterns') or '{}')
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO model_monitoring 
                (metric_type, metric_value, details, created_at)
                VALUES 
                (:metric_type1, :metric_value1, :details1, NOW()),
                (:metric_type2, :metric_value2, :details2, NOW()),
                (:metric_type3, :metric_value3, :details3, NOW())
            """), {
                'metric_type1': 'data_quality',
                'metric_value1': quality_stats.get('quality_percentage', 0),
                'details1': json.dumps(quality_stats),
                'metric_type2': 'model_risk',
                'metric_value2': drift_stats.get('avg_risk', 0),
                'details2': json.dumps(drift_stats),
                'metric_type3': 'error_rate',
                'metric_value3': error_patterns.get('batches_with_errors', 0),
                'details3': json.dumps(error_patterns)
            })
            conn.commit()
        logger.info(f"✅ Metrics saved")
    except Exception as e:
        logger.error(f"❌ Error: {e}")

def generate_alerts(**context):
    logger.info("🚨 Generating alerts...")
    
    ti = context['task_instance']
    quality_stats = json.loads(ti.xcom_pull(task_ids='calculate_data_quality', key='quality_stats') or '{}')
    drift_stats = json.loads(ti.xcom_pull(task_ids='detect_model_drift', key='drift_stats') or '{}')
    
    alerts = []
    
    if quality_stats.get('quality_percentage', 100) < 80:
        alerts.append({
            'severity': 'HIGH',
            'type': 'LOW_DATA_QUALITY',
            'message': f"Data quality dropped to {quality_stats.get('quality_percentage')}%"
        })
    
    if drift_stats.get('avg_risk', 0) > 0.7:
        alerts.append({
            'severity': 'MEDIUM',
            'type': 'HIGH_MODEL_RISK',
            'message': f"Average risk score high: {drift_stats.get('avg_risk'):.4f}"
        })
    
    if drift_stats.get('total_predictions', 0) == 0:
        alerts.append({
            'severity': 'LOW',
            'type': 'NO_PREDICTIONS',
            'message': "No predictions generated in last hour"
        })
    
    if alerts:
        logger.warning(f"🚨 {len(alerts)} alert(s) generated:")
        for alert in alerts:
            logger.warning(f"   [{alert['severity']}] {alert['type']}: {alert['message']}")
    else:
        logger.info("✅ No alerts - all metrics normal")
    
    return len(alerts)

with dag:
    calculate_quality = PythonOperator(task_id='calculate_data_quality', python_callable=calculate_data_quality)
    detect_drift = PythonOperator(task_id='detect_model_drift', python_callable=detect_model_drift)
    check_errors = PythonOperator(task_id='check_error_patterns', python_callable=check_error_patterns)
    save_metrics = PythonOperator(task_id='save_monitoring_metrics', python_callable=save_monitoring_metrics)
    alerts = PythonOperator(task_id='generate_alerts', python_callable=generate_alerts)
    
    [calculate_quality, detect_drift, check_errors] >> save_metrics >> alerts
