from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
import pandas as pd, numpy as np, logging, json
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

logger = logging.getLogger(__name__)

DATABASE_URL = 'postgresql://meharuu@localhost:5432/ml_production'
REPORTS_DIR = '/Users/meharuu/Desktop/work/ml-production-system/reports'

default_args = {'owner': 'ml-team', 'retries': 1, 'retry_delay': timedelta(minutes=5), 'start_date': datetime(2025, 1, 1)}

dag = DAG('analytics_dashboard_pipeline', default_args=default_args, description='Generate analytics & business reports', schedule='0 6 * * *', catchup=False, tags=['analytics', 'reporting', 'bi'])

def calculate_kpis(**context):
    logger.info("📊 Calculating KPIs...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        kpis = {}
        
        # KPI 1: Total files processed
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM ingestion_statistics
            """)).fetchone()
            kpis['total_files_processed'] = result[0] or 0
        
        # KPI 2: Total valid rows
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT SUM(valid_rows) FROM ingestion_statistics
            """)).fetchone()
            kpis['total_valid_rows'] = result[0] or 0
        
        # KPI 3: Overall data quality %
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    ROUND(100.0 * SUM(valid_rows) / NULLIF(SUM(total_rows), 0), 2)
                FROM ingestion_statistics
            """)).fetchone()
            kpis['overall_quality_percentage'] = result[0] or 0
        
        # KPI 4: Total predictions made
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT SUM(total_rows) FROM model_predictions
            """)).fetchone()
            kpis['total_predictions'] = result[0] or 0
        
        # KPI 5: Average risk score
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT AVG(mean_risk_score) FROM model_predictions
            """)).fetchone()
            kpis['avg_risk_score'] = float(result[0]) if result[0] else 0
        
        # KPI 6: High risk predictions (> 0.7)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM model_predictions 
                WHERE mean_risk_score > 0.7
            """)).fetchone()
            kpis['high_risk_batches'] = result[0] or 0
        
        # KPI 7: Model accuracy (avg R2 from monitoring)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT AVG(metric_value) FROM model_monitoring
                WHERE metric_type = 'model_risk'
            """)).fetchone()
            kpis['model_avg_risk'] = float(result[0]) if result[0] else 0
        
        # KPI 8: System uptime (% of successful DAG runs)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 2)
                FROM airflow_dag_run
                WHERE dag_id = 'data_ingestion_pipeline'
                AND execution_date > NOW() - INTERVAL '7 days'
            """)).fetchone()
            kpis['system_uptime_percentage'] = result[0] or 0
        
        logger.info(f"✅ KPIs calculated:")
        for key, val in kpis.items():
            logger.info(f"   {key}: {val}")
        
        context['task_instance'].xcom_push(key='kpis', value=json.dumps(kpis))
        return kpis
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {}

def analyze_data_quality(**context):
    logger.info("📈 Analyzing data quality trends...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Get daily quality metrics
        query = """
        SELECT 
            DATE(processed_at) as date,
            COUNT(*) as batches,
            SUM(total_rows) as total_rows,
            SUM(valid_rows) as valid_rows,
            ROUND(100.0 * SUM(valid_rows) / NULLIF(SUM(total_rows), 0), 2) as quality_pct
        FROM ingestion_statistics
        WHERE processed_at > NOW() - INTERVAL '30 days'
        GROUP BY DATE(processed_at)
        ORDER BY date DESC
        LIMIT 30
        """
        
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        
        analysis = {
            'avg_daily_quality': float(df['quality_pct'].mean()),
            'min_daily_quality': float(df['quality_pct'].min()),
            'max_daily_quality': float(df['quality_pct'].max()),
            'trend': 'improving' if df['quality_pct'].iloc[-1] > df['quality_pct'].iloc[0] else 'declining',
            'days_analyzed': len(df)
        }
        
        logger.info(f"✅ Quality Analysis:")
        for key, val in analysis.items():
            logger.info(f"   {key}: {val}")
        
        context['task_instance'].xcom_push(key='quality_analysis', value=json.dumps(analysis))
        return analysis
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {}

def analyze_predictions(**context):
    logger.info("🎯 Analyzing prediction distribution...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Get prediction distribution
        query = """
        SELECT 
            CASE 
                WHEN mean_risk_score < 0.3 THEN 'Low'
                WHEN mean_risk_score < 0.6 THEN 'Medium'
                ELSE 'High'
            END as risk_category,
            COUNT(*) as count,
            AVG(mean_risk_score) as avg_score
        FROM model_predictions
        WHERE created_at > NOW() - INTERVAL '30 days'
        GROUP BY risk_category
        """
        
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        
        distribution = df.to_dict('records')
        
        logger.info(f"✅ Prediction Distribution:")
        for item in distribution:
            logger.info(f"   {item['risk_category']}: {item['count']} predictions")
        
        context['task_instance'].xcom_push(key='predictions_dist', value=json.dumps(distribution))
        return distribution
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {}

def identify_error_patterns(**context):
    logger.info("🔴 Identifying error patterns...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Get top error types
        query = """
        SELECT error_types, COUNT(*) as count
        FROM ingestion_statistics
        WHERE error_types IS NOT NULL AND error_types != '{}'
        AND processed_at > NOW() - INTERVAL '30 days'
        GROUP BY error_types
        ORDER BY count DESC
        LIMIT 5
        """
        
        with engine.connect() as conn:
            results = conn.execute(text(query)).fetchall()
        
        error_summary = {}
        for error_json, count in results:
            try:
                errors = json.loads(error_json)
                for key, val in errors.items():
                    error_summary[key] = error_summary.get(key, 0) + val
            except:
                pass
        
        # Sort by frequency
        top_errors = sorted(error_summary.items(), key=lambda x: x[1], reverse=True)[:5]
        
        logger.info(f"✅ Top Error Types:")
        for error, count in top_errors:
            logger.info(f"   {error}: {count} occurrences")
        
        context['task_instance'].xcom_push(key='error_patterns', value=json.dumps(dict(top_errors)))
        return dict(top_errors)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {}

def generate_visualizations(**context):
    logger.info("📊 Generating visualizations...")
    
    try:
        Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
        
        engine = create_engine(DATABASE_URL)
        
        # Chart 1: Quality trend
        query = """
        SELECT 
            DATE(processed_at) as date,
            ROUND(100.0 * SUM(valid_rows) / NULLIF(SUM(total_rows), 0), 2) as quality_pct
        FROM ingestion_statistics
        WHERE processed_at > NOW() - INTERVAL '30 days'
        GROUP BY DATE(processed_at)
        ORDER BY date
        """
        
        with engine.connect() as conn:
            df_quality = pd.read_sql(text(query), conn)
        
        plt.figure(figsize=(12, 5))
        plt.plot(df_quality['date'], df_quality['quality_pct'], marker='o', linewidth=2)
        plt.title('Data Quality Trend (Last 30 Days)', fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Quality %')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{REPORTS_DIR}/01_quality_trend.png', dpi=100, bbox_inches='tight')
        plt.close()
        logger.info("✅ Saved: quality_trend.png")
        
        # Chart 2: Risk distribution
        query = """
        SELECT 
            CASE 
                WHEN mean_risk_score < 0.3 THEN 'Low (0-0.3)'
                WHEN mean_risk_score < 0.6 THEN 'Medium (0.3-0.6)'
                ELSE 'High (0.6+)'
            END as category,
            COUNT(*) as count
        FROM model_predictions
        WHERE created_at > NOW() - INTERVAL '30 days'
        GROUP BY category
        """
        
        with engine.connect() as conn:
            df_risk = pd.read_sql(text(query), conn)
        
        plt.figure(figsize=(10, 6))
        plt.bar(df_risk['category'], df_risk['count'], color=['green', 'orange', 'red'])
        plt.title('Risk Score Distribution (Last 30 Days)', fontsize=14, fontweight='bold')
        plt.ylabel('Number of Predictions')
        plt.tight_layout()
        plt.savefig(f'{REPORTS_DIR}/02_risk_distribution.png', dpi=100, bbox_inches='tight')
        plt.close()
        logger.info("✅ Saved: risk_distribution.png")
        
        # Chart 3: Processing volume
        query = """
        SELECT 
            DATE(processed_at) as date,
            COUNT(*) as batches
        FROM ingestion_statistics
        WHERE processed_at > NOW() - INTERVAL '30 days'
        GROUP BY DATE(processed_at)
        ORDER BY date
        """
        
        with engine.connect() as conn:
            df_volume = pd.read_sql(text(query), conn)
        
        plt.figure(figsize=(12, 5))
        plt.bar(df_volume['date'], df_volume['batches'], color='skyblue')
        plt.title('Daily Processing Volume (Last 30 Days)', fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Number of Batches')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{REPORTS_DIR}/03_processing_volume.png', dpi=100, bbox_inches='tight')
        plt.close()
        logger.info("✅ Saved: processing_volume.png")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

def create_executive_summary(**context):
    logger.info("📋 Creating executive summary...")
    
    ti = context['task_instance']
    kpis = json.loads(ti.xcom_pull(task_ids='calculate_kpis', key='kpis') or '{}')
    quality_analysis = json.loads(ti.xcom_pull(task_ids='analyze_data_quality', key='quality_analysis') or '{}')
    predictions_dist = json.loads(ti.xcom_pull(task_ids='analyze_predictions', key='predictions_dist') or '[]')
    error_patterns = json.loads(ti.xcom_pull(task_ids='identify_error_patterns', key='error_patterns') or '{}')
    
    summary = {
        'generated_at': datetime.now().isoformat(),
        'key_performance_indicators': kpis,
        'data_quality': quality_analysis,
        'prediction_insights': {
            'distribution': predictions_dist,
            'top_errors': error_patterns
        },
        'recommendations': [
            f"Data Quality: {quality_analysis.get('trend', 'stable')}",
            f"Focus on: {list(error_patterns.keys())[0] if error_patterns else 'No major issues'}" if error_patterns else "All systems nominal",
            f"Model Status: {f'High Risk Detected ({kpis.get(\"high_risk_batches\", 0)} batches)' if kpis.get('high_risk_batches', 0) > 10 else 'Healthy'}"
        ]
    }
    
    logger.info("\n" + "="*80)
    logger.info("📊 EXECUTIVE SUMMARY - PHASE 9")
    logger.info("="*80)
    logger.info(json.dumps(summary, indent=2))
    logger.info("="*80)
    
    # Save summary
    try:
        with open(f'{REPORTS_DIR}/executive_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"✅ Saved: executive_summary.json")
    except Exception as e:
        logger.error(f"⚠️  Could not save summary: {e}")
    
    return summary

with dag:
    kpis = PythonOperator(task_id='calculate_kpis', python_callable=calculate_kpis)
    quality = PythonOperator(task_id='analyze_data_quality', python_callable=analyze_data_quality)
    predictions = PythonOperator(task_id='analyze_predictions', python_callable=analyze_predictions)
    errors = PythonOperator(task_id='identify_error_patterns', python_callable=identify_error_patterns)
    viz = PythonOperator(task_id='generate_visualizations', python_callable=generate_visualizations)
    summary = PythonOperator(task_id='create_executive_summary', python_callable=create_executive_summary)
    
    [kpis, quality, predictions, errors] >> viz >> summary
