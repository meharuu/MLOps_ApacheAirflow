from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import pandas as pd
import joblib
import json

# Initialize FastAPI
app = FastAPI(title="Accident Risk Predictor API")

# Load model
model = joblib.load("/Users/mugundan/Documents/dsp/calamity-main/models/model.pkl")

# Setup DB connection (Postgres)
engine = create_engine("postgresql://postgres:yourpassword@localhost/data_monitoring")

# Define input schema (matches your training features)
class AccidentFeatures(BaseModel):
    road_type_highway: int
    road_type_rural: int
    road_type_urban: int
    lighting_daylight: int
    lighting_dim: int
    lighting_night: int
    weather_clear: int
    weather_foggy: int
    weather_rainy: int
    speed_limit: float
    curvature: float


@app.post("/predict")
def predict(features: AccidentFeatures):
    # Convert input to DataFrame
    df = pd.DataFrame([features.dict()])

    # Run model prediction
    pred = model.predict(df)[0]

    # Save prediction into PostgreSQL
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO predictions(model_name, input_features, prediction_result)
                VALUES (:model_name, :input_features, :prediction_result)
            """),
            {
                "model_name": "accident_risk_model",
                "input_features": json.dumps(features.dict()),
                "prediction_result": json.dumps({"prediction": float(pred)})
            }
        )
        conn.commit()

    return {"prediction": float(pred)}


@app.get("/past-predictions")
def get_past_predictions():
    # Fetch recent predictions
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM predictions ORDER BY created_at DESC LIMIT 20")
        )
        rows = result.mappings().all()   # returns list of dictionaries
    return [dict(r) for r in rows]
