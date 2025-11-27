"""
FastAPI application for ML model serving
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import uuid
from typing import List

from .schemas import (
    PredictionRequest,
    BatchPredictionRequest,
    PredictionResponse,
    BatchPredictionResponse,
    PastPredictionsRequest,
    PastPredictionsResponse,
    ErrorResponse
)
from .model_manager import get_model_manager, ModelManager
from src.database.config import SessionLocal, get_db
from src.database.crud import PredictionCRUD, ModelPerformanceCRUD
from src.database.models import Prediction

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ML Production System API",
    description="API for serving ML predictions",
    version="1.0.0"
)


# Middleware for request logging
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ml-api"
    }


# Model info endpoint
@app.get("/model-info")
async def get_model_info(model_manager: ModelManager = Depends(get_model_manager)):
    """Get model information"""
    try:
        info = model_manager.get_model_info()
        return {
            "status": "success",
            "data": info
        }
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Single prediction endpoint
@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    model_manager: ModelManager = Depends(get_model_manager)
):
    """Make single prediction and save to database"""
    try:
        # Make prediction
        pred_result = model_manager.predict(request.features)
        
        # Create prediction record
        prediction = PredictionCRUD.create_prediction(
            db,
            features=request.features,
            prediction=pred_result['prediction'],
            prediction_class=pred_result.get('prediction_class'),
            probability_0=pred_result.get('probability_0'),
            probability_1=pred_result.get('probability_1'),
            confidence_score=pred_result.get('confidence_score'),
            source='webapp',
            model_version=pred_result['model_version']
        )
        
        logger.info(f"✅ Prediction created: {prediction.prediction_id}")
        
        return PredictionResponse.from_orm(prediction)
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prediction failed: {str(e)}"
        )


# Batch prediction endpoint
@app.post("/predict-batch", response_model=BatchPredictionResponse)
async def predict_batch(
    request: BatchPredictionRequest,
    db: Session = Depends(get_db),
    model_manager: ModelManager = Depends(get_model_manager)
):
    """Make batch predictions and save to database"""
    try:
        batch_id = str(uuid.uuid4())
        predictions_list = []
        
        # Make predictions
        pred_results = model_manager.predict_batch(request.features_list)
        
        # Save to database
        for i, pred_result in enumerate(pred_results):
            if 'error' not in pred_result:
                pred_db = PredictionCRUD.create_prediction(
                    db,
                    features=request.features_list[i],
                    prediction=pred_result['prediction'],
                    prediction_class=pred_result.get('prediction_class'),
                    probability_0=pred_result.get('probability_0'),
                    probability_1=pred_result.get('probability_1'),
                    confidence_score=pred_result.get('confidence_score'),
                    source='webapp',
                    batch_id=batch_id,
                    model_version=pred_result['model_version']
                )
                predictions_list.append(PredictionResponse.from_orm(pred_db))
        
        logger.info(f"✅ Batch predictions created: {len(predictions_list)} predictions")
        
        # Calculate performance metrics
        valid_predictions = [p.prediction for p in predictions_list]
        if valid_predictions:
            ModelPerformanceCRUD.create_performance_record(
                db,
                batch_id=batch_id,
                prediction_count=len(valid_predictions),
                avg_prediction=sum(valid_predictions) / len(valid_predictions),
                min_prediction=min(valid_predictions),
                max_prediction=max(valid_predictions),
                zero_predictions=sum(1 for p in valid_predictions if p == 0)
            )
        
        return BatchPredictionResponse(
            predictions=predictions_list,
            total_predictions=len(predictions_list),
            batch_id=batch_id,
            created_at=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch prediction failed: {str(e)}"
        )


# Get past predictions endpoint
@app.post("/past-predictions", response_model=PastPredictionsResponse)
async def get_past_predictions(
    request: PastPredictionsRequest,
    db: Session = Depends(get_db)
):
    """Get past predictions from database"""
    try:
        # Retrieve predictions
        predictions = PredictionCRUD.get_predictions_between_dates(
            db,
            start_date=request.start_date,
            end_date=request.end_date,
            source=request.source
        )[:request.limit]
        
        logger.info(f"Retrieved {len(predictions)} past predictions")
        
        return PastPredictionsResponse(
            predictions=[PredictionResponse.from_orm(p) for p in predictions],
            total_count=len(predictions),
            query_time=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error retrieving past predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve predictions: {str(e)}"
        )


# Get predictions by batch
@app.get("/predictions/{batch_id}")
async def get_predictions_by_batch(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """Get all predictions in a batch"""
    try:
        predictions = PredictionCRUD.get_predictions_by_batch(db, batch_id)
        
        if not predictions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        return {
            "batch_id": batch_id,
            "total_predictions": len(predictions),
            "predictions": [PredictionResponse.from_orm(p) for p in predictions]
        }
    
    except Exception as e:
        logger.error(f"Error retrieving batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Error handling
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation Error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)