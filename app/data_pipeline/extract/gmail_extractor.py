"""
Gmail Service Module
--------------------

This module handles Gmail API authentication, email retrieval, and email parsing.
It is separated from the main application to keep Gmail-specific functionality modular
and reusable for different parts of the TravelBot application.

Functions:
    get_gmail_service() -> googleapiclient.discovery.Resource:
        Returns an authenticated Gmail API service.

    get_latest_email_id(client: Optional[googleapiclient.discovery.Resource]) -> Optional[str]:
        Returns the message ID of the most recent email.

    extract_gmail_as_json(service: googleapiclient.discovery.Resource, message_id: str) -> dict[str, Optional[str]]:
        Extracts email metadata and body text as structured JSON.
"""

# Standard library
import base64
from typing import Any

# Third-party
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

# Local application
from app.config import settings
from app.utils.secrets import secret_to_str


def get_gmail_service() -> Resource:
    """
    Authenticate and return a Gmail API service resource.
    Uses OAuth 2.0 and saves credentials to a local token file.

    Returns:
        googleapiclient.discovery.Resource: Authenticated Gmail API client.
    """
    creds: Credentials = None

    # Load saved credentials if available
    if settings.gmail_token_file.exists():
        creds = Credentials.from_authorized_user_file(settings.gmail_token_file, settings.scopes)

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_config = {
                "installed": {
                    "client_id": settings.travelbot_gmail_client_id,
                    "client_secret": secret_to_str(settings.travelbot_gmail_client_secret),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"],
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, settings.scopes)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open(settings.gmail_token_file, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_inbox_email_ids(
    client: Resource | None = None, max_results: int | None = 10
) -> list[str] | None:
    """
    Retrieve message IDs from the user's Gmail inbox.

    Args:
        service (object): Authorized Gmail API service instance.
        max_results (int, optional): Maximum number of email IDs to retrieve.
            Defaults to 100 to limit API requests.

    Returns:
        list[str]: A list of message IDs from the inbox, limited to max_results.
    """
    if not client:
        client = get_gmail_service()

    results = client.users().messages().list(userId="me", maxResults=max_results).execute()
    messages = results.get("messages", [])

    if not messages:
        print("No messages found.")
        return None

    return [m["id"] for m in messages]


def extract_gmail_as_json(service: Resource, message_id: str) -> dict[str, str | None]:
    """
    Extract email metadata and body content from Gmail and return as a dictionary.

    Args:
        service (googleapiclient.discovery.Resource): Authenticated Gmail API client.
        message_id (str): Gmail message ID.

    Returns:
        dict[str, Optional[str]]: Dictionary containing email metadata and body text.
    """
    msg: dict[str, Any] = (
        service.users().messages().get(userId="me", id=message_id, format="full").execute()
    )

    payload = msg.get("payload", {})
    headers = payload.get("headers", [])

    def get_header(name):
        return next((h["value"] for h in headers if h["name"].lower() == name.lower()), None)

    email_data = {
        "from": get_header("From"),
        "to": get_header("To"),
        "date": get_header("Date"),
        "subject": get_header("Subject"),
        "message_id": message_id,
        "body": None,
    }

    def extract_body(payload):
        if payload.get("mimeType") == "text/plain":
            return base64.urlsafe_b64decode(payload["body"].get("data", "")).decode(
                "utf-8", errors="ignore"
            )
        elif payload.get("mimeType") == "text/html":
            html = base64.urlsafe_b64decode(payload["body"].get("data", "")).decode(
                "utf-8", errors="ignore"
            )
            return BeautifulSoup(html, "html.parser").get_text()
        elif "parts" in payload:
            for part in payload["parts"]:
                body = extract_body(part)
                if body:
                    return body
        return None

    email_data["body"] = extract_body(payload)
    return email_data
