# Standard library
from pathlib import Path

# Third-party
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Local application
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()