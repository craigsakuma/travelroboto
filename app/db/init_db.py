"""
Initialize the PostgreSQL database for the Travel Itinerary project.

This script:
- Loads the database URL from app.config
- Imports all table models from the tables subpackage
- Creates all tables defined in the SQLAlchemy models
"""

import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError


# Local application imports
from app.config import RAILWAY_DATABASE_URL
from app.db.base import Base

def init_db() -> None:
    """
    Initializes the PostgreSQL database by creating all tables.

    Uses SQLAlchemy Base.metadata to generate all tables defined in models.
    """
    try:
        engine = create_engine(RAILWAY_DATABASE_URL, echo=True, future=True)
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully.")
    except SQLAlchemyError as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()