import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import requests
import json

st.set_page_config(page_title="ML Production Dashboard", layout="wide", initial_sidebar_state="expanded")

DATABASE_URL = 'postgresql://meharuu@localhost:5432/ml_production'
API_URL = 'http://localhost:8000'

st.title("🚀 ML Production System Dashboard")

# Sidebar
st.sidebar.header("Dashboard Navigation")
page = st.sidebar.radio("Select Page", [
    "📊 Overview",
    "📈 Data Quality",
    "🤖 Predictions",
    "⚠️ Alerts",
    "🔮 Make Prediction",
    "📋 Reports"
])

# Helper function to get database data
def get_db_data(query):
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

# PAGE 1: OVERVIEW
if page == "📊 Overview":
    st.header("System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI 1: Files Processed
    try:
        df = get_db_data("SELECT COUNT(*) as count FROM ingestion_statistics")
        val = df['count'].values[0] if df is not None and len(df) > 0 else 0
        col1.metric("📁 Files Processed", int(val) if val else 0)
    except:
        col1.metric("📁 Files Processed", "N/A")
    
    # KPI 2: Valid Rows
    try:
        df = get_db_data("SELECT COALESCE(SUM(valid_rows), 0) as count FROM ingestion_statistics")
        val = df['count'].values[0] if df is not None and len(df) > 0 else 0
        col2.metric("✅ Valid Rows", f"{int(val) if val else 0:,}")
    except:
        col2.metric("✅ Valid Rows", "N/A")
    
    # KPI 3: Data Quality %
    try:
        df = get_db_data("""
            SELECT COALESCE(ROUND(100.0 * SUM(valid_rows) / NULLIF(SUM(total_rows), 0), 2), 0) as pct 
            FROM ingestion_statistics
        """)
        val = df['pct'].values[0] if df is not None and len(df) > 0 else 0
        col3.metric("📊 Quality %", f"{float(val) if val else 0:.1f}%")
    except:
        col3.metric("📊 Quality %", "N/A")
    
    # KPI 4: Predictions Made
    try:
        df = get_db_data("SELECT COALESCE(SUM(total_rows), 0) as count FROM model_predictions")
        val = df['count'].values[0] if df is not None and len(df) > 0 else 0
        col4.metric("🎯 Predictions", f"{int(val) if val else 0:,}")
    except:
        col4.metric("🎯 Predictions", "N/A")
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Processing Volume (Last 7 Days)")
        df = get_db_data("""
            SELECT DATE(processed_at) as date, COUNT(*) as batches
            FROM ingestion_statistics
            WHERE processed_at > NOW() - INTERVAL '7 days'
            GROUP BY DATE(processed_at)
            ORDER BY date
        """)
        if df is not None and len(df) > 0:
            st.bar_chart(df.set_index('date')['batches'])
        else:
            st.info("No data available")
    
    with col2:
        st.subheader("Data Quality Trend (Last 7 Days)")
        df = get_db_data("""
            SELECT DATE(processed_at) as date,
                   COALESCE(ROUND(100.0 * SUM(valid_rows) / NULLIF(SUM(total_rows), 0), 2), 0) as quality
            FROM ingestion_statistics
            WHERE processed_at > NOW() - INTERVAL '7 days'
            GROUP BY DATE(processed_at)
            ORDER BY date
        """)
        if df is not None and len(df) > 0:
            st.line_chart(df.set_index('date')['quality'])
        else:
            st.info("No data available")

# PAGE 2: DATA QUALITY
elif page == "📈 Data Quality":
    st.header("Data Quality Metrics")
    
    df = get_db_data("""
        SELECT 
            COUNT(*) as batches,
            COALESCE(SUM(total_rows), 0) as total_rows,
            COALESCE(SUM(valid_rows), 0) as valid_rows,
            COALESCE(SUM(invalid_rows), 0) as invalid_rows,
            COALESCE(ROUND(100.0 * SUM(valid_rows) / NULLIF(SUM(total_rows), 0), 2), 0) as quality_pct
        FROM ingestion_statistics
        WHERE processed_at > NOW() - INTERVAL '24 hours'
    """)
    
    if df is not None and len(df) > 0:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Batches", int(df['batches'].values[0]) if df['batches'].values[0] else 0)
        col2.metric("Valid Rows", f"{int(df['valid_rows'].values[0]) if df['valid_rows'].values[0] else 0:,}")
        col3.metric("Invalid Rows", f"{int(df['invalid_rows'].values[0]) if df['invalid_rows'].values[0] else 0:,}")
        col4.metric("Quality %", f"{float(df['quality_pct'].values[0]) if df['quality_pct'].values[0] else 0:.1f}%")
    
    st.divider()
    
    st.subheader("Error Summary (Last 24 Hours)")
    st.info("Track data quality issues and error patterns")

# PAGE 3: PREDICTIONS
elif page == "🤖 Predictions":
    st.header("Model Predictions")
    
    df = get_db_data("""
        SELECT 
            COUNT(*) as total,
            COALESCE(AVG(mean_risk_score), 0) as avg_risk,
            COALESCE(MIN(min_risk_score), 0) as min_risk,
            COALESCE(MAX(max_risk_score), 0) as max_risk
        FROM model_predictions
        WHERE created_at > NOW() - INTERVAL '24 hours'
    """)
    
    if df is not None and len(df) > 0:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Predictions", int(df['total'].values[0]) if df['total'].values[0] else 0)
        col2.metric("Avg Risk", f"{float(df['avg_risk'].values[0]) if df['avg_risk'].values[0] else 0:.4f}")
        col3.metric("Min Risk", f"{float(df['min_risk'].values[0]) if df['min_risk'].values[0] else 0:.4f}")
        col4.metric("Max Risk", f"{float(df['max_risk'].values[0]) if df['max_risk'].values[0] else 0:.4f}")
    
    st.divider()
    
    st.subheader("Risk Distribution")
    st.info("Track prediction distribution across risk levels")

# PAGE 4: ALERTS
elif page == "⚠️ Alerts":
    st.header("System Alerts")
    
    alerts = []
    
    # Check data quality
    df_quality = get_db_data("""
        SELECT COALESCE(ROUND(100.0 * SUM(valid_rows) / NULLIF(SUM(total_rows), 0), 2), 0) as pct
        FROM ingestion_statistics
        WHERE processed_at > NOW() - INTERVAL '1 hour'
    """)
    if df_quality is not None and len(df_quality) > 0 and df_quality['pct'].values[0] < 80:
        alerts.append(("🔴 HIGH", "Low Data Quality", f"Quality: {df_quality['pct'].values[0]}%"))
    
    # Check high risk
    df_risk = get_db_data("""
        SELECT COUNT(*) as count FROM model_predictions
        WHERE mean_risk_score > 0.7 AND created_at > NOW() - INTERVAL '1 hour'
    """)
    if df_risk is not None and len(df_risk) > 0 and df_risk['count'].values[0] > 10:
        alerts.append(("🟡 MEDIUM", "High Risk Batches", f"Found {df_risk['count'].values[0]} high-risk batches"))
    
    if alerts:
        for severity, title, message in alerts:
            st.warning(f"{severity} - **{title}**: {message}")
    else:
        st.success("✅ No alerts - System healthy!")

# PAGE 5: MAKE PREDICTION
elif page == "🔮 Make Prediction":
    st.header("Make a Prediction")
    
    st.info("Enter road data to get accident risk prediction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        road_type = st.selectbox("Road Type", ["highway", "local_road", "motorway", "roundabout", "urban"])
        num_lanes = st.slider("Number of Lanes", 1, 10, 3)
        speed_limit = st.slider("Speed Limit (km/h)", 20, 130, 70)
        lighting = st.selectbox("Lighting", ["daylight", "street_lit", "dark"])
    
    with col2:
        weather = st.selectbox("Weather", ["clear", "rain", "fog", "snow", "storm"])
        time_of_day = st.selectbox("Time of Day", ["day", "night", "dawn", "dusk"])
        curvature = st.slider("Curvature (0-10)", 0, 10, 3)
        num_reported_accidents = st.slider("Reported Accidents", 0, 100, 0)
    
    if st.button("🚀 Get Prediction", use_container_width=True):
        try:
            # Prepare payload with only the features the model expects
            payload = {
                "road_type": road_type,
                "num_lanes": num_lanes,
                "curvature": curvature,
                "speed_limit": speed_limit,
                "lighting": lighting,
                "weather": weather,
                "time_of_day": time_of_day,
                "num_reported_accidents": num_reported_accidents
            }
            
            st.json(payload)  # Debug: show what we're sending
            
            response = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
            
            st.write(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                prediction = result.get('prediction', 0)
                
                if prediction < 0.3:
                    color = "🟢"
                    risk_level = "LOW"
                elif prediction < 0.6:
                    color = "🟡"
                    risk_level = "MEDIUM"
                else:
                    color = "🔴"
                    risk_level = "HIGH"
                
                st.success(f"✅ Prediction: {color} **{risk_level}** Risk\n\n**Score: {prediction:.4f}**")
            else:
                st.error(f"API Error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"Error: {e}")

# PAGE 6: REPORTS
elif page == "📋 Reports":
    st.header("System Reports")
    
    st.subheader("Executive Summary")
    df_summary = get_db_data("""
        SELECT 
            COUNT(*) as total_batches,
            COALESCE(SUM(valid_rows), 0) as total_valid,
            COALESCE(SUM(invalid_rows), 0) as total_invalid,
            COALESCE(ROUND(100.0 * SUM(valid_rows) / NULLIF(SUM(total_rows), 0), 2), 0) as quality
        FROM ingestion_statistics
    """)
    
    if df_summary is not None and len(df_summary) > 0:
        st.json({
            "Total Batches Processed": int(df_summary['total_batches'].values[0]) if df_summary['total_batches'].values[0] else 0,
            "Total Valid Rows": int(df_summary['total_valid'].values[0]) if df_summary['total_valid'].values[0] else 0,
            "Total Invalid Rows": int(df_summary['total_invalid'].values[0]) if df_summary['total_invalid'].values[0] else 0,
            "Overall Quality": f"{float(df_summary['quality'].values[0]) if df_summary['quality'].values[0] else 0:.1f}%"
        })
    
    st.divider()
    
    st.subheader("Recent Statistics")
    df_recent = get_db_data("""
        SELECT batch_id, total_rows, valid_rows, invalid_rows, processed_at
        FROM ingestion_statistics
        ORDER BY processed_at DESC
        LIMIT 10
    """)
    
    if df_recent is not None and len(df_recent) > 0:
        st.dataframe(df_recent, use_container_width=True)

st.sidebar.divider()
st.sidebar.info("🚀 ML Production System - Phases 1-9 Complete!")
