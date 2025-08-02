"""
Configuration settings for the TravelBot project.
Centralizes environment variables, file paths, and constants.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# -------------------------------------------------------------------
# Load environment variables from .env file (if present)
# -------------------------------------------------------------------
load_dotenv()

# -------------------------------------------------------------------
# App base and app directories (e.g., /path/to/chatbot_project)
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
APP_ROOT = BASE_DIR / "app"

# -------------------------------------------------------------------
# API Keys and Secrets
# -------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TRAVELBOT_GMAIL_CLIENT_ID = os.getenv("TRAVELBOT_GMAIL_CLIENT_ID", "")
TRAVELBOT_GMAIL_CLIENT_SECRET = os.getenv("TRAVELBOT_GMAIL_CLIENT_SECRET", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")

# -------------------------------------------------------------------
# Paths for Credentials and Data
# -------------------------------------------------------------------
CREDENTIALS_DIR = BASE_DIR / "credentials"
GMAIL_TOKEN_FILE = CREDENTIALS_DIR / "token.json"
TEST_DATA_DIR = BASE_DIR / "tests" / "test_data"

# -------------------------------------------------------------------
# Database - postgresql hosted on railway
# -------------------------------------------------------------------
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_NAME = os.getenv("PG_NAME")
DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_NAME}"

# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
