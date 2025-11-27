"""
CRUD operations for database models
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .models import Prediction, DataQualityIssue, IngestionStatistics, DataDrift, ModelPerformance
import logging

logger = logging.getLogger(__name__)


class PredictionCRUD:
    """Operations for Prediction model"""
    
    @staticmethod
    def create_prediction(db: Session, **kwargs) -> Prediction:
        """Create new prediction record"""
        prediction = Prediction(**kwargs)
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        logger.info(f"Created prediction: {prediction.prediction_id}")
        return prediction
    
    @staticmethod
    def create_batch_predictions(db: Session, predictions_list: List[Dict]) -> List[Prediction]:
        """Create multiple prediction records"""
        predictions = [Prediction(**pred_data) for pred_data in predictions_list]
        db.add_all(predictions)
        db.commit()
        logger.info(f"Created {len(predictions)} predictions")
        return predictions
    
    @staticmethod
    def get_prediction_by_id(db: Session, prediction_id: str) -> Optional[Prediction]:
        """Get prediction by ID"""
        return db.query(Prediction).filter(Prediction.prediction_id == prediction_id).first()
    
    @staticmethod
    def get_predictions_by_source(db: Session, source: str, limit: int = 100) -> List[Prediction]:
        """Get recent predictions by source"""
        return db.query(Prediction)\
            .filter(Prediction.source == source)\
            .order_by(desc(Prediction.created_at))\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_predictions_between_dates(
        db: Session,
        start_date: datetime,
        end_date: datetime,
        source: Optional[str] = None
    ) -> List[Prediction]:
        """Get predictions within date range"""
        query = db.query(Prediction).filter(
            and_(
                Prediction.created_at >= start_date,
                Prediction.created_at <= end_date
            )
        )
        
        if source and source != 'all':
            query = query.filter(Prediction.source == source)
        
        return query.order_by(desc(Prediction.created_at)).all()
    
    @staticmethod
    def get_predictions_by_batch(db: Session, batch_id: str) -> List[Prediction]:
        """Get all predictions from a batch"""
        return db.query(Prediction).filter(Prediction.batch_id == batch_id).all()


class QualityIssueCRUD:
    """Operations for DataQualityIssue model"""
    
    @staticmethod
    def create_issue(db: Session, **kwargs) -> DataQualityIssue:
        """Create new quality issue record"""
        issue = DataQualityIssue(**kwargs)
        db.add(issue)
        db.commit()
        db.refresh(issue)
        logger.info(f"Created quality issue: {issue.error_type} in {issue.filename}")
        return issue
    
    @staticmethod
    def create_batch_issues(db: Session, issues_list: List[Dict]) -> List[DataQualityIssue]:
        """Create multiple issue records"""
        issues = [DataQualityIssue(**issue_data) for issue_data in issues_list]
        db.add_all(issues)
        db.commit()
        logger.info(f"Created {len(issues)} quality issues")
        return issues
    
    @staticmethod
    def get_issues_by_severity(db: Session, severity: str) -> List[DataQualityIssue]:
        """Get issues by severity level"""
        return db.query(DataQualityIssue)\
            .filter(DataQualityIssue.severity == severity)\
            .order_by(desc(DataQualityIssue.created_at))\
            .all()
    
    @staticmethod
    def get_unresolved_issues(db: Session, limit: int = 100) -> List[DataQualityIssue]:
        """Get unresolved issues"""
        return db.query(DataQualityIssue)\
            .filter(DataQualityIssue.is_resolved == False)\
            .order_by(desc(DataQualityIssue.created_at))\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_issues_in_last_n_minutes(db: Session, minutes: int = 30) -> List[DataQualityIssue]:
        """Get issues from last N minutes"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return db.query(DataQualityIssue)\
            .filter(DataQualityIssue.created_at >= cutoff_time)\
            .order_by(desc(DataQualityIssue.created_at))\
            .all()
    
    @staticmethod
    def get_error_type_distribution(db: Session, minutes: int = 60) -> Dict:
        """Get count of each error type in last N minutes"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        issues = db.query(DataQualityIssue)\
            .filter(DataQualityIssue.created_at >= cutoff_time)\
            .all()
        
        distribution = {}
        for issue in issues:
            distribution[issue.error_type] = distribution.get(issue.error_type, 0) + 1
        
        return distribution


class IngestionStatisticsCRUD:
    """Operations for IngestionStatistics model"""
    
    @staticmethod
    def create_statistics(db: Session, **kwargs) -> IngestionStatistics:
        """Create new ingestion statistics record"""
        stats = IngestionStatistics(**kwargs)
        db.add(stats)
        db.commit()
        db.refresh(stats)
        logger.info(f"Created ingestion statistics for {stats.filename}")
        return stats
    
    @staticmethod
    def get_statistics_by_filename(db: Session, filename: str) -> Optional[IngestionStatistics]:
        """Get statistics for specific file"""
        return db.query(IngestionStatistics)\
            .filter(IngestionStatistics.filename == filename)\
            .first()
    
    @staticmethod
    def get_recent_statistics(db: Session, limit: int = 50) -> List[IngestionStatistics]:
        """Get recent ingestion statistics"""
        return db.query(IngestionStatistics)\
            .order_by(desc(IngestionStatistics.created_at))\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_statistics_in_last_n_minutes(db: Session, minutes: int = 60) -> List[IngestionStatistics]:
        """Get statistics from last N minutes"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return db.query(IngestionStatistics)\
            .filter(IngestionStatistics.created_at >= cutoff_time)\
            .order_by(desc(IngestionStatistics.created_at))\
            .all()


class DataDriftCRUD:
    """Operations for DataDrift model"""
    
    @staticmethod
    def create_drift_record(db: Session, **kwargs) -> DataDrift:
        """Create new data drift record"""
        drift = DataDrift(**kwargs)
        db.add(drift)
        db.commit()
        db.refresh(drift)
        logger.info(f"Created drift record for {drift.feature_name}")
        return drift
    
    @staticmethod
    def get_detected_drifts(db: Session) -> List[DataDrift]:
        """Get features with detected drift"""
        return db.query(DataDrift)\
            .filter(DataDrift.drift_detected == True)\
            .order_by(desc(DataDrift.created_at))\
            .all()


class ModelPerformanceCRUD:
    """Operations for ModelPerformance model"""
    
    @staticmethod
    def create_performance_record(db: Session, **kwargs) -> ModelPerformance:
        """Create new model performance record"""
        perf = ModelPerformance(**kwargs)
        db.add(perf)
        db.commit()
        db.refresh(perf)
        return perf
    
    @staticmethod
    def get_recent_performance(db: Session, limit: int = 100) -> List[ModelPerformance]:
        """Get recent performance records"""
        return db.query(ModelPerformance)\
            .order_by(desc(ModelPerformance.created_at))\
            .limit(limit)\
            .all()