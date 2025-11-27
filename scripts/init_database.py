"""
Initialize PostgreSQL database with schema and tables
Fixed version that handles import paths correctly
"""

import logging
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.database.config import create_all_tables, test_connection
from src.database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_database():
    """Initialize database"""
    logger.info("Starting database initialization...")
    
    # Test connection
    if not test_connection():
        logger.error("Cannot connect to database. Check your connection settings.")
        return False
    
    # Create tables
    try:
        create_all_tables()
        logger.info("✅ Database initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error during initialization: {e}")
        return False


if __name__ == "__main__":
    initialize_database()