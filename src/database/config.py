"""
Database configuration and connection management
FIXED VERSION
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/ml_production'
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Disable connection pooling for Airflow
    echo=False,  # Set to True for SQL logging
    connect_args={
        "connect_timeout": 10,
        "application_name": "ml_production_system"
    }
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """Create all tables"""
    from .models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("✅ All database tables created")


def drop_all_tables():
    """Drop all tables (use with caution!)"""
    from .models import Base
    Base.metadata.drop_all(bind=engine)
    logger.warning("⚠️  All database tables dropped")


def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            # FIX: Use text() to wrap raw SQL
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_connection()
    create_all_tables()