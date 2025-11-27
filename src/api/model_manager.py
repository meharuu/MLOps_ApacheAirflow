"""
Model manager for serving predictions with OneHotEncoder
"""

import os
import joblib
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages model and preprocessing pipeline"""
    
    def __init__(self, model_dir='model'):
        self.model_dir = model_dir
        self.model = None
        self.preprocessor = None
        self.metadata = None
        self.model_version = None
        self._load_model()
    
    def _load_model(self):
        """Load model, preprocessor, and metadata"""
        try:
            logger.info("Loading model from disk...")
            
            # Load model
            model_path = os.path.join(self.model_dir, 'trained_model.pkl')
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found at {model_path}")
            
            self.model = joblib.load(model_path)
            logger.info(f"✅ Model loaded: {model_path}")
            
            # Load preprocessor (includes scaler and OneHotEncoder)
            preprocessor_path = os.path.join(self.model_dir, 'preprocessor.pkl')
            if not os.path.exists(preprocessor_path):
                raise FileNotFoundError(f"Preprocessor not found at {preprocessor_path}")
            
            self.preprocessor = joblib.load(preprocessor_path)
            logger.info(f"✅ Preprocessor loaded: {preprocessor_path}")
            
            # Load metadata
            metadata_path = os.path.join(self.model_dir, 'metadata.pkl')
            if not os.path.exists(metadata_path):
                raise FileNotFoundError(f"Metadata not found at {metadata_path}")
            
            self.metadata = joblib.load(metadata_path)
            logger.info(f"✅ Metadata loaded: {metadata_path}")
            
            self.model_version = self.metadata.get('trained_at', 'v1.0.0')
            logger.info(f"✅ Model version: {self.model_version}")
            
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            raise RuntimeError(f"Failed to load model: {e}")
    
    def preprocess_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Preprocess features using the preprocessor pipeline"""
        try:
            # Create DataFrame for single sample
            df = pd.DataFrame([features])
            
            # Use preprocessor (handles OneHotEncoding and scaling)
            X_scaled = self.preprocessor.transform(df)
            
            return X_scaled
        
        except Exception as e:
            logger.error(f"Error preprocessing features: {e}")
            raise ValueError(f"Feature preprocessing failed: {e}")
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Make single prediction"""
        try:
            # Preprocess
            X_scaled = self.preprocess_features(features)
            
            # Predict
            prediction = self.model.predict(X_scaled)[0]
            
            # Prepare response
            response = {
                'prediction': float(prediction),
                'model_version': self.model_version,
                'preprocessor_type': 'OneHotEncoder + StandardScaler'
            }
            
            return response
        
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise RuntimeError(f"Prediction failed: {e}")
    
    def predict_batch(self, features_list: list) -> Dict[str, Any]:
        """Make batch predictions"""
        try:
            # Create DataFrame
            df = pd.DataFrame(features_list)
            
            # Preprocess all at once
            X_scaled = self.preprocessor.transform(df)
            
            # Predict
            predictions = self.model.predict(X_scaled)
            
            response = {
                'predictions': [float(p) for p in predictions],
                'n_samples': len(predictions),
                'model_version': self.model_version
            }
            
            return response
        
        except Exception as e:
            logger.error(f"Batch prediction error: {e}")
            raise RuntimeError(f"Batch prediction failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            'model_version': self.model_version,
            'model_type': self.metadata.get('model_type'),
            'encoder_type': self.metadata.get('encoder_type'),
            'n_features': self.metadata.get('n_features'),
            'n_categorical': self.metadata.get('n_categorical'),
            'n_numerical': self.metadata.get('n_numerical'),
            'feature_columns': self.metadata.get('feature_columns'),
            'categorical_columns': self.metadata.get('categorical_columns'),
            'numerical_columns': self.metadata.get('numerical_columns'),
            'target_column': self.metadata.get('target_column')
        }


# Global instance
_model_manager = None


def get_model_manager() -> ModelManager:
    """Get or create model manager instance (dependency injection)"""
    global _model_manager
    
    if _model_manager is None:
        logger.info("Initializing model manager...")
        _model_manager = ModelManager(model_dir='model')
    
    return _model_manager