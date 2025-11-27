"""
Train ML regression model and save for serving
Using OneHotEncoder for categorical features
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelTrainer:
    def __init__(self, dataset_path, model_dir='model'):
        self.dataset_path = dataset_path
        self.model_dir = model_dir
        self.model = None
        self.preprocessor = None
        self.feature_columns = None
        self.categorical_columns = None
        self.numerical_columns = None
        self.target_column = None
        
        os.makedirs(model_dir, exist_ok=True)
    
    def load_and_prepare_data(self, target_column):
        """Load and prepare dataset"""
        logger.info(f"Loading dataset from {self.dataset_path}")
        df = pd.read_csv(self.dataset_path)
        
        # Drop rows with missing values
        df = df.dropna()
        
        self.target_column = target_column
        X = df.drop(columns=[target_column])
        y = df[target_column].astype(float)
        
        self.feature_columns = X.columns.tolist()
        logger.info(f"Features: {self.feature_columns}")
        logger.info(f"Target: {target_column}")
        logger.info(f"Dataset shape: {X.shape}")
        
        # Identify categorical and numerical columns
        self.categorical_columns = X.select_dtypes(include=['object']).columns.tolist()
        self.numerical_columns = X.select_dtypes(include=[np.number]).columns.tolist()
        
        logger.info(f"Categorical columns: {self.categorical_columns}")
        logger.info(f"Numerical columns: {self.numerical_columns}")
        
        return X, y
    
    def create_preprocessor(self):
        """Create preprocessing pipeline with OneHotEncoder"""
        logger.info("Creating preprocessing pipeline with OneHotEncoder...")
        
        # OneHotEncoder for categorical features
        categorical_transformer = OneHotEncoder(
            sparse_output=False,
            handle_unknown='ignore',
            drop='first'  # Drop first category to avoid multicollinearity
        )
        
        # StandardScaler for numerical features
        numerical_transformer = StandardScaler()
        
        # Combine transformers
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', numerical_transformer, self.numerical_columns),
                ('cat', categorical_transformer, self.categorical_columns)
            ]
        )
        
        logger.info("✅ Preprocessor created")
        return self.preprocessor
    
    def train(self, target_column, test_size=0.2, random_state=42):
        """Train regression model with OneHotEncoder"""
        logger.info("=" * 60)
        logger.info("TRAINING REGRESSION MODEL (OneHotEncoder)")
        logger.info("=" * 60)
        
        X, y = self.load_and_prepare_data(target_column)
        
        # Create preprocessor
        self.create_preprocessor()
        
        # Split data BEFORE preprocessing
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        logger.info(f"Training set: {X_train.shape}")
        logger.info(f"Test set: {X_test.shape}")
        
        # Fit preprocessor on training data
        logger.info("Fitting preprocessor on training data...")
        X_train_processed = self.preprocessor.fit_transform(X_train)
        X_test_processed = self.preprocessor.transform(X_test)
        
        logger.info(f"Processed training set shape: {X_train_processed.shape}")
        logger.info(f"Processed test set shape: {X_test_processed.shape}")
        
        # Train Random Forest model
        logger.info("Training Random Forest Regressor...")
        self.model = RandomForestRegressor(
            n_estimators=500,
            max_depth=10,
            random_state=random_state,
            n_jobs=-1,
            verbose=1
        )
        self.model.fit(X_train_processed, y_train)
        
        # Predictions
        y_pred_train = self.model.predict(X_train_processed)
        y_pred_test = self.model.predict(X_test_processed)
        
        # Metrics
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        mae = mean_absolute_error(y_test, y_pred_test)
        mse = mean_squared_error(y_test, y_pred_test)
        rmse = np.sqrt(mse)
        
        logger.info(f"✅ Model trained successfully")
        logger.info(f"   Training R²: {train_r2:.4f}")
        logger.info(f"   Test R²: {test_r2:.4f}")
        logger.info(f"   MAE: {mae:.4f}")
        logger.info(f"   MSE: {mse:.4f}")
        logger.info(f"   RMSE: {rmse:.4f}")
        
        # Feature importances (after OneHotEncoding)
        importances = self.model.feature_importances_
        
        # Get feature names from preprocessor
        feature_names = []
        
        # Add numerical feature names
        feature_names.extend(self.numerical_columns)
        
        # Add categorical feature names (after OneHotEncoding)
        if hasattr(self.preprocessor, 'named_transformers_'):
            cat_encoder = self.preprocessor.named_transformers_['cat']
            if hasattr(cat_encoder, 'get_feature_names_out'):
                cat_feature_names = cat_encoder.get_feature_names_out(self.categorical_columns)
                feature_names.extend(cat_feature_names)
        
        logger.info("\nTop 10 Feature Importances:")
        top_features = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:10]
        for feature, importance in top_features:
            logger.info(f"   {feature}: {importance:.4f}")
        
        return self.model, train_r2, test_r2, mae, rmse
    
    def save_model(self):
        """Save model, preprocessor, and metadata"""
        if self.model is None:
            logger.error("Model not trained yet!")
            return False
        
        if self.preprocessor is None:
            logger.error("Preprocessor not created yet!")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Save model
            model_path = os.path.join(self.model_dir, 'trained_model.pkl')
            joblib.dump(self.model, model_path)
            logger.info(f"✅ Model saved: {model_path}")
            
            # Save preprocessor (includes scaler and encoder)
            preprocessor_path = os.path.join(self.model_dir, 'preprocessor.pkl')
            joblib.dump(self.preprocessor, preprocessor_path)
            logger.info(f"✅ Preprocessor saved: {preprocessor_path}")
            
            # Save metadata
            metadata = {
                'feature_columns': self.feature_columns,
                'categorical_columns': self.categorical_columns,
                'numerical_columns': self.numerical_columns,
                'target_column': self.target_column,
                'model_type': 'RandomForestRegressor',
                'encoder_type': 'OneHotEncoder',
                'trained_at': timestamp,
                'n_features': len(self.feature_columns),
                'n_categorical': len(self.categorical_columns),
                'n_numerical': len(self.numerical_columns)
            }
            
            metadata_path = os.path.join(self.model_dir, 'metadata.pkl')
            joblib.dump(metadata, metadata_path)
            logger.info(f"✅ Metadata saved: {metadata_path}")
            
            # Also save as JSON for human readability
            import json
            metadata_json_path = os.path.join(self.model_dir, 'metadata.json')
            with open(metadata_json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"✅ Metadata (JSON) saved: {metadata_json_path}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Error saving model: {e}")
            return False


if __name__ == "__main__":
    trainer = ModelTrainer(
        dataset_path='data/original_dataset.csv',
        model_dir='model'
    )
    
    # Train the model with your target column
    trainer.train(target_column='accident_risk')
    
    # Save the model
    trainer.save_model()