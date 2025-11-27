"""
SQLAlchemy models for the ML production system
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime
import uuid

Base = declarative_base()


class Prediction(Base):
    """Model predictions table"""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True)
    prediction_id = Column(PG_UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    features = Column(JSON, nullable=False)                  # Input features
    prediction = Column(Float, nullable=False)               # Model output
    prediction_class = Column(String(50))                    # Classification class
    probability_0 = Column(Float)                            # Class 0 probability
    probability_1 = Column(Float)                            # Class 1 probability
    confidence_score = Column(Float)                         # Prediction confidence
    source = Column(String(50), nullable=False, index=True)  # 'webapp' or 'scheduled'
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    batch_id = Column(String(100), index=True)               # Batch grouping
    api_version = Column(String(20))
    model_version = Column(String(50))
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, source={self.source}, prediction={self.prediction})>"
    
    def to_dict(self):
        return {
            'prediction_id': str(self.prediction_id),
            'prediction': self.prediction,
            'prediction_class': self.prediction_class,
            'confidence_score': self.confidence_score,
            'source': self.source,
            'created_at': self.created_at.isoformat(),
            'model_version': self.model_version
        }


class DataQualityIssue(Base):
    """Data quality issues detected during ingestion"""
    __tablename__ = "data_quality_issues"
    
    id = Column(Integer, primary_key=True)
    issue_id = Column(PG_UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False, index=True)
    error_type = Column(String(100), nullable=False, index=True)
    column_name = Column(String(100))
    affected_rows = Column(Integer)
    error_count = Column(Integer, default=1)
    error_details = Column(JSON)                             # Detailed error info
    severity = Column(String(20), index=True)                # HIGH, MEDIUM, LOW
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime)
    
    def __repr__(self):
        return f"<DataQualityIssue(type={self.error_type}, severity={self.severity})>"
    
    def to_dict(self):
        return {
            'issue_id': str(self.issue_id),
            'filename': self.filename,
            'error_type': self.error_type,
            'column_name': self.column_name,
            'affected_rows': self.affected_rows,
            'severity': self.severity,
            'created_at': self.created_at.isoformat()
        }


class IngestionStatistics(Base):
    """Statistics about each ingestion batch"""
    __tablename__ = "ingestion_statistics"
    
    id = Column(Integer, primary_key=True)
    batch_id = Column(PG_UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    total_rows = Column(Integer, nullable=False)
    valid_rows = Column(Integer, nullable=False)
    invalid_rows = Column(Integer, nullable=False)
    quality_score = Column(Float)                            # valid_rows / total_rows
    processing_time_ms = Column(Float)                       # Validation duration
    validation_status = Column(String(50))                   # PASSED, FAILED, PARTIAL
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<IngestionStatistics(file={self.filename}, status={self.validation_status})>"
    
    def to_dict(self):
        return {
            'batch_id': str(self.batch_id),
            'filename': self.filename,
            'total_rows': self.total_rows,
            'valid_rows': self.valid_rows,
            'invalid_rows': self.invalid_rows,
            'quality_score': self.quality_score,
            'validation_status': self.validation_status,
            'created_at': self.created_at.isoformat()
        }


class DataDrift(Base):
    """Data drift detection between training and serving data"""
    __tablename__ = "data_drift"
    
    id = Column(Integer, primary_key=True)
    drift_id = Column(PG_UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    feature_name = Column(String(100), nullable=False, index=True)
    train_mean = Column(Float)                               # Training data mean
    train_std = Column(Float)                                # Training data std
    serving_mean = Column(Float)                             # Serving data mean
    serving_std = Column(Float)                              # Serving data std
    drift_score = Column(Float)                              # Statistical drift measure
    drift_detected = Column(Boolean)
    threshold = Column(Float, default=0.15)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<DataDrift(feature={self.feature_name}, drift={self.drift_detected})>"
    
    def to_dict(self):
        return {
            'drift_id': str(self.drift_id),
            'feature_name': self.feature_name,
            'drift_score': self.drift_score,
            'drift_detected': self.drift_detected,
            'created_at': self.created_at.isoformat()
        }


class ModelPerformance(Base):
    """Model performance metrics over time"""
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True)
    performance_id = Column(PG_UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    batch_id = Column(String(100), index=True)
    prediction_count = Column(Integer, default=0)           # Predictions in batch
    avg_prediction = Column(Float)                           # Average prediction
    min_prediction = Column(Float)                           # Min prediction
    max_prediction = Column(Float)                           # Max prediction
    most_common_class = Column(String(50))                   # Most predicted class
    zero_predictions = Column(Integer, default=0)            # Count of predictions=0
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ModelPerformance(batch={self.batch_id}, predictions={self.prediction_count})>"
    
    def to_dict(self):
        return {
            'performance_id': str(self.performance_id),
            'batch_id': self.batch_id,
            'prediction_count': self.prediction_count,
            'avg_prediction': self.avg_prediction,
            'zero_predictions': self.zero_predictions,
            'created_at': self.created_at.isoformat()
        }