import streamlit as st
import requests
import pandas as pd

FASTAPI_URL = "http://127.0.0.1:8000"
st.set_page_config(page_title="Road Accident Prediction Dashboard", layout="wide")
st.title("Road Accident Prediction & Monitoring Dashboard")
st.sidebar.header("Input Road Features")
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
    user_input[key] = st.sidebar.number_input(key.replace("_", " "), value=float(default))

if st.sidebar.button("Make Prediction"):
    try:
        response = requests.post(f"{FASTAPI_URL}/predict", json=user_input)
        if response.status_code == 200:
            result = response.json()
            st.success(f"Predicted Value: {result['prediction']:.4f}")
        else:
            st.error(f"Error: {response.text}")
    except Exception as e:
        st.error(f"Failed to connect to backend: {e}")

st.subheader("Past Predictions")
try:
    resp = requests.get(f"{FASTAPI_URL}/past-predictions")
    if resp.status_code == 200:
        data = resp.json()
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No past predictions yet.")
    else:
        st.error("Could not retrieve past predictions.")
except Exception as e:
    st.error(f"Failed to connect to backend: {e}")