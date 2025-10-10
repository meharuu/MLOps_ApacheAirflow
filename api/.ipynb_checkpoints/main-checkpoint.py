from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib
import json
from sqlalchemy import create_engine, text

# NO import from app.py or streamlit!