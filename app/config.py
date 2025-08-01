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
# Database
# -------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'travel.db'}")

# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
