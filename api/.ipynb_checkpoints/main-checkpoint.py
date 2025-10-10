from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib
import json
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://samaladileepgoud@localhost/postgres")

model = joblib.load("model/model.pkl")

app = FastAPI(title="Road Accident Prediction API")

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
@app.post("/predict")
def predict_accident(features: RoadFeatures):
    df = pd.DataFrame([features.dict()])
    pred = model.predict(df)[0]

    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO predictions(model_name, input_features, prediction_result) "
                "VALUES (:model_name, :input_features, :prediction_result)"
            ),
            {
                "model_name": "demo_model",
                "input_features": json.dumps(features.dict()),
                "prediction_result": json.dumps({"prediction": float(pred)})
            }
        )
        conn.commit()
    
    return {"prediction": float(pred)}

@app.get("/past-predictions")
def get_past_predictions():
    with engine.connect() as conn:
        rows = conn.execute("SELECT * FROM predictions ORDER BY created_at DESC LIMIT 20")
        return [dict(r) for r in rows]
