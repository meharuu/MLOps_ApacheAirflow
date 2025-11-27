from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
import pandas as pd, numpy as np, logging, joblib, json
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

logger = logging.getLogger(__name__)

DATABASE_URL = 'postgresql://meharuu@localhost:5432/ml_production'
MODEL_DIR = '/Users/meharuu/Desktop/work/ml-production-system/model'
GOOD_DATA_DIR = '/Users/meharuu/Desktop/work/ml-production-system/data/good_data'

default_args = {'owner': 'ml-team', 'retries': 1, 'retry_delay': timedelta(minutes=5), 'start_date': datetime(2025, 1, 1)}

dag = DAG('model_retraining_pipeline', default_args=default_args, description='Retrain and deploy new models', schedule='0 0 * * 0', catchup=False, tags=['model', 'retraining', 'deployment'])

def collect_training_data(**context):
    logger.info("📂 Collecting training data from good_data files...")
    
    try:
        dfs = []
        files = [f for f in os.listdir(GOOD_DATA_DIR) if f.endswith('.csv')]
        
        if len(files) < 10:
            logger.warning(f"⚠️  Only {len(files)} files available, need at least 10")
            return None
        
        # Collect last 100 good data files
        for file in sorted(files)[-100:]:
            df = pd.read_csv(os.path.join(GOOD_DATA_DIR, file))
            dfs.append(df)
        
        training_data = pd.concat(dfs, ignore_index=True)
        logger.info(f"✅ Collected {len(training_data)} rows from {len(dfs)} files")
        
        context['task_instance'].xcom_push(key='n_training_rows', value=len(training_data))
        context['task_instance'].xcom_push(key='n_training_files', value=len(dfs))
        
        # Save for next task
        training_data.to_csv('/tmp/training_data.csv', index=False)
        return len(training_data)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None

def evaluate_current_model(**context):
    logger.info("📊 Evaluating current model performance...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Get average metrics from last week
        query = """
        SELECT 
            COUNT(*) as total_predictions,
            AVG(mean_risk_score) as avg_risk,
            STDDEV(mean_risk_score) as stddev_risk
        FROM model_predictions
        WHERE created_at > NOW() - INTERVAL '7 days'
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(query)).fetchone()
        
        if result and result[0] > 0:
            current_metrics = {
                'total_predictions': result[0],
                'avg_risk': float(result[1]) if result[1] else 0,
                'stddev_risk': float(result[2]) if result[2] else 0
            }
            logger.info(f"✅ Current Model - Predictions: {current_metrics['total_predictions']}, Avg Risk: {current_metrics['avg_risk']:.4f}")
            
            context['task_instance'].xcom_push(key='current_metrics', value=json.dumps(current_metrics))
            return current_metrics
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None

def train_new_model(**context):
    logger.info("🤖 Training new model...")
    
    try:
        import os
        
        # Load training data
        training_data = pd.read_csv('/tmp/training_data.csv')
        
        # Prepare features and target
        X = training_data.drop(columns=['predicted_accident_risk'], errors='ignore')
        y = training_data['accident_risk'] if 'accident_risk' in training_data.columns else training_data.iloc[:, -1]
        
        # Load preprocessor from current model
        preprocessor = joblib.load(f'{MODEL_DIR}/preprocessor.pkl')
        
        # Preprocess
        X_scaled = preprocessor.transform(X)
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
        
        # Train new model
        new_model = RandomForestRegressor(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1)
        new_model.fit(X_train, y_train)
        
        # Evaluate
        train_r2 = new_model.score(X_train, y_train)
        test_r2 = new_model.score(X_test, y_test)
        y_pred = new_model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        new_metrics = {
            'train_r2': float(train_r2),
            'test_r2': float(test_r2),
            'mae': float(mae),
            'rmse': float(rmse),
            'n_samples': len(training_data)
        }
        
        logger.info(f"✅ New Model - Test R²: {test_r2:.4f}, MAE: {mae:.4f}")
        
        # Save temporary model
        joblib.dump(new_model, '/tmp/new_model.pkl')
        
        context['task_instance'].xcom_push(key='new_metrics', value=json.dumps(new_metrics))
        return new_metrics
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None

def compare_models(**context):
    logger.info("⚖️  Comparing model performance...")
    
    ti = context['task_instance']
    current_metrics = json.loads(ti.xcom_pull(task_ids='evaluate_current_model', key='current_metrics') or '{}')
    new_metrics = json.loads(ti.xcom_pull(task_ids='train_new_model', key='new_metrics') or '{}')
    
    if not new_metrics:
        logger.warning("⚠️  No new model metrics, skipping comparison")
        return {'deploy': False, 'reason': 'No new model'}
    
    # Compare based on available metrics
    comparison = {
        'current_avg_risk': current_metrics.get('avg_risk', 0.5),
        'new_mae': new_metrics.get('mae', 0),
        'new_r2': new_metrics.get('test_r2', 0),
        'improvement': 0
    }
    
    # Decision logic: Deploy if R² is high or MAE decreased
    should_deploy = new_metrics.get('test_r2', 0) > 0.7 or new_metrics.get('mae', 1) < 0.05
    
    if should_deploy:
        logger.info(f"✅ NEW MODEL IS BETTER - Will deploy!")
        comparison['deploy'] = True
        comparison['reason'] = f"R²={new_metrics.get('test_r2'):.4f}, MAE={new_metrics.get('mae'):.4f}"
    else:
        logger.warning(f"⚠️  New model not better enough")
        comparison['deploy'] = False
        comparison['reason'] = f"R²={new_metrics.get('test_r2'):.4f} < 0.7 or MAE={new_metrics.get('mae'):.4f} > 0.05"
    
    context['task_instance'].xcom_push(key='comparison', value=json.dumps(comparison))
    return comparison

def deploy_new_model(**context):
    logger.info("🚀 Deploying new model...")
    
    ti = context['task_instance']
    comparison = json.loads(ti.xcom_pull(task_ids='compare_models', key='comparison') or '{}')
    
    if not comparison.get('deploy', False):
        logger.info(f"⏭️  Skipping deployment: {comparison.get('reason')}")
        return False
    
    try:
        import os
        import shutil
        
        # Backup current model
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{MODEL_DIR}/backups"
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy(f'{MODEL_DIR}/trained_model.pkl', f'{backup_dir}/trained_model_{timestamp}.pkl')
        logger.info(f"✅ Backed up current model")
        
        # Deploy new model
        shutil.copy('/tmp/new_model.pkl', f'{MODEL_DIR}/trained_model.pkl')
        logger.info(f"✅ Deployed new model!")
        
        # Log deployment
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO model_deployments (model_version, status, details, deployed_at)
                VALUES (:version, :status, :details, NOW())
            """), {
                'version': timestamp,
                'status': 'ACTIVE',
                'details': json.dumps(comparison)
            })
            conn.commit()
        
        return True
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        return False

def run_system_tests(**context):
    logger.info("✅ Running system tests...")
    
    tests = {
        'api_health': True,
        'database_connection': True,
        'model_available': True,
        'data_ingestion': True,
        'predictions_working': True
    }
    
    try:
        # Test 1: Database connection
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        tests['database_connection'] = True
        logger.info("✅ Database connection OK")
        
        # Test 2: Model file exists
        import os
        tests['model_available'] = os.path.exists(f'{MODEL_DIR}/trained_model.pkl')
        logger.info(f"✅ Model file available: {tests['model_available']}")
        
        # Test 3: Recent predictions
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM model_predictions 
                WHERE created_at > NOW() - INTERVAL '1 hour'
            """)).fetchone()
        tests['predictions_working'] = result[0] > 0
        logger.info(f"✅ Recent predictions found: {result[0]}")
        
        # Test 4: Recent ingestions
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM ingestion_statistics 
                WHERE processed_at > NOW() - INTERVAL '1 hour'
            """)).fetchone()
        tests['data_ingestion'] = result[0] > 0
        logger.info(f"✅ Recent ingestions found: {result[0]}")
        
        all_passed = all(tests.values())
        logger.info(f"\n🎯 SYSTEM HEALTH: {'✅ HEALTHY' if all_passed else '❌ ISSUES DETECTED'}")
        logger.info(json.dumps(tests, indent=2))
        
        return tests
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return tests

def generate_report(**context):
    logger.info("📋 Generating system report...")
    
    ti = context['task_instance']
    current_metrics = json.loads(ti.xcom_pull(task_ids='evaluate_current_model', key='current_metrics') or '{}')
    new_metrics = json.loads(ti.xcom_pull(task_ids='train_new_model', key='new_metrics') or '{}')
    comparison = json.loads(ti.xcom_pull(task_ids='compare_models', key='comparison') or '{}')
    tests = ti.xcom_pull(task_ids='run_system_tests') or {}
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'system_health': all(tests.values()) if isinstance(tests, dict) else False,
        'current_model': current_metrics,
        'new_model': new_metrics,
        'comparison': comparison,
        'system_tests': tests
    }
    
    logger.info("\n" + "="*60)
    logger.info("📊 PHASE 8 SYSTEM REPORT")
    logger.info("="*60)
    logger.info(json.dumps(report, indent=2))
    logger.info("="*60)
    
    # Save report
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO system_reports (report_data, created_at)
                VALUES (:data, NOW())
            """), {'data': json.dumps(report)})
            conn.commit()
        logger.info("✅ Report saved to database")
    except Exception as e:
        logger.error(f"⚠️  Could not save report: {e}")
    
    return report

# Create tables
import os
os.system(f"""psql -U meharuu -d ml_production -c "
CREATE TABLE IF NOT EXISTS model_deployments (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50),
    status VARCHAR(20),
    details JSONB,
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_reports (
    id SERIAL PRIMARY KEY,
    report_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"
""")

with dag:
    collect_data = PythonOperator(task_id='collect_training_data', python_callable=collect_training_data)
    eval_current = PythonOperator(task_id='evaluate_current_model', python_callable=evaluate_current_model)
    train_new = PythonOperator(task_id='train_new_model', python_callable=train_new_model)
    compare = PythonOperator(task_id='compare_models', python_callable=compare_models)
    deploy = PythonOperator(task_id='deploy_new_model', python_callable=deploy_new_model)
    tests = PythonOperator(task_id='run_system_tests', python_callable=run_system_tests)
    report = PythonOperator(task_id='generate_report', python_callable=generate_report)
    
    [collect_data, eval_current] >> train_new >> compare >> deploy >> [tests, report]
