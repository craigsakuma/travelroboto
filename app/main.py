#!/usr/bin/env python3
"""
Main entry point for the Travel Itinerary SMS Chatbot API.

This app:
- Launches the Gradio UI
- Connects to LLM chains
"""
# Standard library
import os

# Third-party
from dotenv import load_dotenv

# Local application
import app.config as config
from app.interfaces.web_ui import launch_web_ui

load_dotenv(config.APP_ROOT / ".env")

if __name__ == "__main__":
    mode = os.getenv("APP_MODE", "web")  # default to web interface
    if mode == "sms":
        # launch_sms_ui()  # Placeholder for Twilio-based SMS interface
        print("SMS interface not implemented yet.")
    else:
        launch_web_ui(share=True)