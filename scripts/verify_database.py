"""
Verify database setup and test CRUD operations
"""

from src.database.config import SessionLocal
from src.database.models import Prediction, DataQualityIssue, IngestionStatistics
from src.database.crud import PredictionCRUD, QualityIssueCRUD
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database():
    """Test database operations"""
    db = SessionLocal()
    
    try:
        # Test 1: Create prediction
        logger.info("Test 1: Creating prediction record...")
        pred = PredictionCRUD.create_prediction(
            db,
            features={'age': 30, 'salary': 50000},
            prediction=0.85,
            prediction_class='positive',
            confidence_score=0.92,
            source='test'
        )
        logger.info(f"✅ Created prediction: {pred.prediction_id}")
        
        # Test 2: Retrieve prediction
        logger.info("Test 2: Retrieving prediction...")
        retrieved = PredictionCRUD.get_prediction_by_id(db, str(pred.prediction_id))
        logger.info(f"✅ Retrieved: {retrieved.prediction}")
        
        # Test 3: Create quality issue
        logger.info("Test 3: Creating quality issue...")
        issue = QualityIssueCRUD.create_issue(
            db,
            filename='test_file.csv',
            error_type='Missing Values',
            column_name='salary',
            affected_rows=10,
            severity='MEDIUM'
        )
        logger.info(f"✅ Created issue: {issue.issue_id}")
        
        logger.info("\n✅ All tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Error during testing: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    test_database()