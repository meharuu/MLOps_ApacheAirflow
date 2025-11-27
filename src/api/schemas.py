"""
Pydantic schemas for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class PredictionRequest(BaseModel):
    """Single prediction request"""
    features: Dict[str, Any] = Field(..., description="Feature dictionary")
    
    class Config:
        schema_extra = {
            "example": {
                "features": {
                    "age": 30,
                    "salary": 50000,
                    "country": "US"
                }
            }
        }


class BatchPredictionRequest(BaseModel):
    """Batch prediction request"""
    features_list: List[Dict[str, Any]] = Field(..., description="List of feature dictionaries")
    
    class Config:
        schema_extra = {
            "example": {
                "features_list": [
                    {"age": 30, "salary": 50000},
                    {"age": 35, "salary": 60000}
                ]
            }
        }


class PredictionResponse(BaseModel):
    """Prediction response"""
    prediction_id: str
    prediction: float
    prediction_class: Optional[str] = None
    confidence_score: Optional[float] = None
    probability_0: Optional[float] = None
    probability_1: Optional[float] = None
    model_version: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class BatchPredictionResponse(BaseModel):
    """Batch prediction response"""
    predictions: List[PredictionResponse]
    total_predictions: int
    batch_id: str
    created_at: datetime


class PastPredictionsRequest(BaseModel):
    """Request for past predictions"""
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    source: str = Field(default="all", description="Source: webapp, scheduled, or all")
    limit: int = Field(default=100, description="Max results")


class PastPredictionsResponse(BaseModel):
    """Response with past predictions"""
    predictions: List[PredictionResponse]
    total_count: int
    query_time: datetime


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime