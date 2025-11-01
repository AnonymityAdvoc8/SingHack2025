"""
TravelMate AI - Claims Database Connection
PostgreSQL database connection for MSIG historical claims data
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from app.config import get_settings
import structlog

logger = structlog.get_logger()


class ClaimsDatabase:
    """PostgreSQL database manager for MSIG claims data"""
    
    def __init__(self):
        """Initialize PostgreSQL connection"""
        settings = get_settings()
        
        # Create engine with NullPool for serverless/short-lived connections
        self.engine = create_engine(
            settings.claims_database_url,
            poolclass=NullPool,
            echo=False  # Set to True for SQL debugging
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(
            "claims_db_initialized",
            host=settings.claims_db_host,
            database=settings.claims_db_name,
            schema=settings.claims_db_schema
        )
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            from sqlalchemy import text
            session = self.get_session()
            session.execute(text("SELECT 1"))
            session.close()
            logger.info("claims_db_connection_test_success")
            return True
        except Exception as e:
            logger.error("claims_db_connection_test_failed", error=str(e))
            return False


# Global instance
_claims_db = None


def get_claims_db() -> ClaimsDatabase:
    """Get global claims database instance"""
    global _claims_db
    if _claims_db is None:
        _claims_db = ClaimsDatabase()
    return _claims_db


def get_claims_session() -> Session:
    """Get a new claims database session (for dependency injection)"""
    db = get_claims_db()
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()

