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

# Intialize database
def init_db():
    """
    Initialize the database.
    - For SQLite: creates the database file if it doesn't exist.
    - For other backends (PostgreSQL, MySQL): ensures tables exist.
    """
    from app.db.tables import Base

    if DATABASE_URL.startswith("sqlite"):
        # Ensure the data folder exists if using a relative SQLite path
        db_path = DATABASE_URL.replace("sqlite:///", "")
        db_file = Path(db_path)

        if not db_file.parent.exists():
            db_file.parent.mkdir(parents=True, exist_ok=True)

        if not db_file.exists():
            print(f"SQLite database not found. Creating new database at: {db_file}")
            Base.metadata.create_all(bind=engine)
        else:
            print(f"SQLite database already exists at: {db_file}, skipping table creation.")
    else:
        # Safe to always run for Postgres/other backends (won't overwrite data)
        print("Ensuring tables exist in non-SQLite database...")
        Base.metadata.create_all(bind=engine)