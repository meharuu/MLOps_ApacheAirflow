import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/predict"

st.set_page_config(page_title="Accident Risk Predictor", layout="centered")
st.title("🚦 Accident Risk Prediction App")

st.subheader("Road Type (choose one)")
road_type = st.radio("Select road type:", ["Highway", "Rural", "Urban"])

st.subheader("Lighting Conditions (choose one)")
lighting = st.radio("Select lighting:", ["Daylight", "Dim", "Night"])

st.subheader("Weather (choose one)")
weather = st.radio("Select weather:", ["Clear", "Foggy", "Rainy"])

st.subheader("Other Features")
speed_limit = st.number_input("Speed Limit (km/h)", min_value=10, max_value=150, step=10)
curvature = st.slider("Road Curvature (0 = straight, 1 = sharp curve)", 0.0, 1.0, 0.1)

# One-hot encode selections exactly as in training
payload = {
    "road_type_highway": 1 if road_type == "Highway" else 0,
    "road_type_rural": 1 if road_type == "Rural" else 0,
    "road_type_urban": 1 if road_type == "Urban" else 0,
    "lighting_daylight": 1 if lighting == "Daylight" else 0,
    "lighting_dim": 1 if lighting == "Dim" else 0,
    "lighting_night": 1 if lighting == "Night" else 0,
    "weather_clear": 1 if weather == "Clear" else 0,
    "weather_foggy": 1 if weather == "Foggy" else 0,
    "weather_rainy": 1 if weather == "Rainy" else 0,
    "speed_limit": speed_limit,
    "curvature": curvature
}

if st.button("Predict Accident Risk"):
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            result = response.json()
            st.success(f"✅ Predicted Risk: {result['prediction']}")
        else:
            st.error(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"🚨 Could not connect to API: {e}")
