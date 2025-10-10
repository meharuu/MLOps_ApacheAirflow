from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib
import json
from sqlalchemy import create_engine, text

# Connect to your PostgreSQL database
engine = create_engine("postgresql://samaladileepgoud@localhost/postgres")

# Load trained model
model = joblib.load("model/model.pkl")

# Initialize FastAPI app
app = FastAPI(title="Road Accident Prediction API")

# Define input schema
class RoadFeatures(BaseModel):
    Number_of_Lanes: float
    Road_Type: float
    Road_Curvature: float
    Speed_Limit: float
    Lightning: float
    Weather: float
    Number_of_Reported_Accidents: float
    Road_Surface_Type: float
    Traffic_Density: float
    Pedestrian_Crossings: float

# Predict endpoint
@app.post("/predict")
def predict_accident(features: RoadFeatures):
    df = pd.DataFrame([features.dict()])
    pred = model.predict(df)[0]

    # Save prediction in database
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO predictions (model_name, input_features, prediction_result)
                VALUES (:model_name, :input_features, :prediction_result)
            """),
            {
                "model_name": "demo_model",
                "input_features": json.dumps(features.dict()),
                "prediction_result": json.dumps({"prediction": float(pred)})
            }
        )

    return {"prediction": float(pred)}

# Fetch past predictions
@app.get("/past-predictions")
def get_past_predictions():
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM predictions ORDER BY created_at DESC LIMIT 20")
        )
        return [dict(r._mapping) for r in rows]