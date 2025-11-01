"""
TravelMate AI - Database Initialization Script
Creates all database tables
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db, engine
from app.models.policy import Policy, GeneralCondition, Benefit, OperationalDetail
from app.models.claims import Claim
from app.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """Initialize database tables"""
    try:
        logger.info("initializing_database")
        
        # Create all tables
        init_db()
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info("database_initialized", tables=tables)
        
        print("✅ Database initialized successfully!")
        print(f"📊 Tables created: {', '.join(tables)}")
        
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

