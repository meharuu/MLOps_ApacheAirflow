import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

FASTAPI_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Road Accident Prediction Dashboard", layout="wide")
st.title("🚗 Road Accident Prediction & Monitoring Dashboard")

# Initialize session state
if 'predictions_history' not in st.session_state:
    st.session_state.predictions_history = []

# Sidebar for inputs
st.sidebar.header("🎯 Input Road Features")

feature_inputs = {
    "Number_of_Lanes": 2.0,
    "Road_Type": 1.0,
    "Road_Curvature": 0.0,
    "Speed_Limit": 50.0,
    "Lightning": 0.0,
    "Weather": 0.0,
    "Number_of_Reported_Accidents": 0.0,
    "Road_Surface_Type": 1.0,
    "Traffic_Density": 1.0,
    "Pedestrian_Crossings": 0.0
}

user_input = {}
for key, default in feature_inputs.items():
    user_input[key] = st.sidebar.number_input(
        key.replace("_", " "), 
        value=float(default),
        step=0.1
    )

# Prediction button
if st.sidebar.button("🔮 Make Prediction", type="primary"):
    try:
        response = requests.post(f"{FASTAPI_URL}/predict", json=user_input)
        if response.status_code == 200:
            result = response.json()
            prediction_value = result['prediction']
            
            # Display prediction with color coding
            col1, col2, col3 = st.columns(3)
            with col2:
                if prediction_value < 0.3:
                    st.success(f"### ✅ Low Risk\n## {prediction_value:.4f}")
                elif prediction_value < 0.7:
                    st.warning(f"### ⚠️ Medium Risk\n## {prediction_value:.4f}")
                else:
                    st.error(f"### 🚨 High Risk\n## {prediction_value:.4f}")
            
            # Store in session state
            prediction_record = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'prediction': prediction_value,
                **user_input
            }
            st.session_state.predictions_history.insert(0, prediction_record)
            
            # Show details in expander
            with st.expander("📊 View Input Details"):
                input_df = pd.DataFrame([user_input]).T
                input_df.columns = ['Value']
                st.dataframe(input_df, use_container_width=True)
            
        else:
            st.error(f"❌ Error: {response.text}")
    except Exception as e:
        st.error(f"❌ Failed to connect to backend: {e}")

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["📈 Session History", "💾 Database Records", "📊 Analytics"])

with tab1:
    st.subheader("Current Session Predictions")
    if st.session_state.predictions_history:
        df_session = pd.DataFrame(st.session_state.predictions_history)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Predictions", len(df_session))
        with col2:
            st.metric("Average Risk", f"{df_session['prediction'].mean():.3f}")
        with col3:
            st.metric("Max Risk", f"{df_session['prediction'].max():.3f}")
        with col4:
            st.metric("Min Risk", f"{df_session['prediction'].min():.3f}")
        
        # Display table
        st.dataframe(df_session, use_container_width=True, height=300)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🗑️ Clear Session History"):
                st.session_state.predictions_history = []
                st.rerun()
        with col2:
            csv = df_session.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Visualization
        if len(df_session) > 1:
            fig = px.line(
                df_session, 
                x='timestamp', 
                y='prediction',
                title='Prediction Trend',
                markers=True
            )
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Risk Prediction",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ No predictions in current session yet. Make a prediction to get started!")

with tab2:
    st.subheader("All Past Predictions (Database)")
    try:
        resp = requests.get(f"{FASTAPI_URL}/past-predictions")
        if resp.status_code == 200:
            data = resp.json()
            if data:
                df = pd.DataFrame(data)
                
                # Show metrics if created_at exists
                if 'created_at' in df.columns:
                    df['created_at'] = pd.to_datetime(df['created_at'])
                
                st.dataframe(df, use_container_width=True, height=400)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download All Database Records",
                    data=csv,
                    file_name=f"all_predictions_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("ℹ️ No past predictions in database yet.")
        else:
            st.error("❌ Could not retrieve past predictions.")
    except Exception as e:
        st.error(f"❌ Failed to connect to backend: {e}")

with tab3:
    st.subheader("Prediction Analytics")
    
    if st.session_state.predictions_history:
        df_analytics = pd.DataFrame(st.session_state.predictions_history)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution histogram
            fig_hist = px.histogram(
                df_analytics, 
                x='prediction',
                title='Risk Distribution',
                nbins=20,
                labels={'prediction': 'Risk Score'}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Risk category pie chart
            df_analytics['risk_category'] = pd.cut(
                df_analytics['prediction'],
                bins=[0, 0.3, 0.7, 1.0],
                labels=['Low Risk', 'Medium Risk', 'High Risk']
            )
            risk_counts = df_analytics['risk_category'].value_counts()
            
            fig_pie = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                title='Risk Categories',
                color_discrete_map={
                    'Low Risk': 'green',
                    'Medium Risk': 'orange',
                    'High Risk': 'red'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Feature importance (correlation with prediction)
        st.subheader("Feature Impact on Predictions")
        numeric_cols = [col for col in df_analytics.columns if col not in ['timestamp', 'risk_category']]
        correlations = df_analytics[numeric_cols].corr()['prediction'].drop('prediction').sort_values(ascending=False)
        
        fig_bar = px.bar(
            x=correlations.values,
            y=correlations.index,
            orientation='h',
            title='Feature Correlation with Risk Prediction',
            labels={'x': 'Correlation', 'y': 'Feature'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("ℹ️ Make some predictions to see analytics!")
