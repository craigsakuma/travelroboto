#!/usr/bin/env python3
"""
Main entry point for the Travel Itinerary SMS Chatbot API.

This app:
- Initializes the database
- Mounts the Twilio SMS webhook endpoint
- Provides a root health-check endpoint
"""

# Standard library
import base64
import json
import os
from datetime import datetime, date, time
from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

# Third-party
import gradio as gr
from bs4 import BeautifulSoup  
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from google.auth.transport.requests import Request
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Local application
import app.config as config

APP_ROOT = config.APP_ROOT
GMAIL_TOKEN_FILE = config.GMAIL_TOKEN_FILE
SCOPES = config.SCOPES
TEST_DATA_DIR = config.TEST_DATA_DIR
TRAVELBOT_GMAIL_CLIENT_ID = config.TRAVELBOT_GMAIL_CLIENT_ID 
TRAVELBOT_GMAIL_CLIENT_SECRET = config.TRAVELBOT_GMAIL_CLIENT_SECRET 

load_dotenv(dotenv_path=Path.home() / ".env")

# Data model for flight parser
class Passenger(BaseModel):
    first_name: str
    last_name: str

class FlightDetails(BaseModel):
    flight_number: str
    airline_name: str
    departure_date: Optional[date] = None
    departure_time: Optional[time] = None
    arrival_date: Optional[datetime] = None
    arrival_time: Optional[str] = None
    origin: str
    destination: str
    passengers: List[Passenger]

class FlightManifest(BaseModel):
    flights: List[FlightDetails]
    
flight_parser = PydanticOutputParser(pydantic_object=FlightManifest)

def get_gmail_service() -> Resource:
    """
    Create and return an authenticated Gmail API service instance.

    This function handles authentication with the Gmail API using OAuth 2.0. It first checks
    for saved credentials in a local `token.json` file. If valid credentials are found, they
    are used directly. If not, the function initiates an OAuth 2.0 flow to authenticate
    the user and generates new credentials using client information stored in environment
    variables:
        - TRAVELBOT_GMAIL_CLIENT_ID
        - TRAVELBOT_GMAIL_CLIENT_SECRET

    The credentials are then saved to `token.json` for reuse in future runs.

    Returns:
        googleapiclient.discovery.Resource:
            An authorized Gmail API service instance for making Gmail API calls.

    Raises:
        google.auth.exceptions.GoogleAuthError: If authentication fails or credentials
            cannot be refreshed.
        FileNotFoundError: If `token.json` is missing and OAuth flow cannot retrieve credentials.
    """
    creds: Credentials = None
    # Load saved credentials if available
    if GMAIL_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            GMAIL_TOKEN_FILE, SCOPES)

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Get credentials from environment variables
            client_config = {
                "installed": {
                    "client_id": TRAVELBOT_GMAIL_CLIENT_ID,
                    "client_secret": TRAVELBOT_GMAIL_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"]
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for next run
        with open(GMAIL_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def get_latest_email_id(client: Optional[Resource] = None) -> Optional[str]:
    """
    Retrieve the message ID of the most recent email from the user's Gmail inbox.

    This function uses the Gmail API to fetch the most recent email for the 
    authenticated user. If a Gmail API client is not provided, one will be created 
    using `get_gmail_service()`.

    Args:
        client (Optional[googleapiclient.discovery.Resource]): 
            An authenticated Gmail API client. If not provided, a new client 
            will be created internally.

    Returns:
        Optional[str]: 
            The message ID of the most recent email if available, otherwise `None`.

    Raises:
        googleapiclient.errors.HttpError: 
            If the Gmail API request fails.# create gmail client if not provided
    """
    # create gmail client if not provided
    if not client:
        client = get_gmail_service()
    # Get list of messages
    results = client.users().messages().list(userId='me', maxResults=1).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No messages found.")
        return

    # Get the message details
    msg_id = messages[0]['id']
    return msg_id

def extract_gmail_as_json(service: Resource, message_id: str) -> Dict[str, Optional[str]]:
    """
    Extract email metadata and body content from the Gmail API and return it as JSON-like data.

    This function retrieves an email message by its ID using the Gmail API, 
    extracts key metadata fields (From, To, Date, Subject, Message ID), 
    and extracts the message body as plain text. If only HTML content 
    is available, it is converted to plain text using BeautifulSoup.

    Args:
        service (googleapiclient.discovery.Resource):
            An authenticated Gmail API service client.
        message_id (str):
            The unique Gmail message ID of the email to retrieve.

    Returns:
        Dict[str, Optional[str]]:
            A dictionary containing the email metadata and body content:
            {
                "from": str or None,
                "to": str or None,
                "date": str or None,
                "subject": str or None,
                "message_id": str,
                "body": str or None
            }

    Raises:
        googleapiclient.errors.HttpError:
            If the Gmail API request fails.

    Example:
        >>> service = get_gmail_service()
        >>> email_data = extract_email_as_json(service, "17c6932b2b4f1a2c")
        >>> print(email_data["subject"])
        'Your Flight Itinerary'
    """
    msg: Dict[str, Any] = service.users().messages().get(userId='me', id=message_id, format='full').execute()

    payload = msg.get("payload", {})
    headers = payload.get("headers", [])

    def get_header(name):
        return next((h['value'] for h in headers if h['name'].lower() == name.lower()), None)

    # Extract headers
    email_data = {
        "from": get_header("From"),
        "to": get_header("To"),
        "date": get_header("Date"),
        "subject": get_header("Subject"),
        "message_id": message_id,
        "body": None  # populated below
    }

    # Extract body (prefer text/plain over text/html)
    def extract_body(payload):
        if payload.get("mimeType") == "text/plain":
            return base64.urlsafe_b64decode(payload["body"].get("data", "")).decode("utf-8", errors="ignore")
        elif payload.get("mimeType") == "text/html":
            html = base64.urlsafe_b64decode(payload["body"].get("data", "")).decode("utf-8", errors="ignore")
            return BeautifulSoup(html, "html.parser").get_text()
        elif "parts" in payload:
            for part in payload["parts"]:
                body = extract_body(part)
                if body:
                    return body
        return None

    email_data["body"] = extract_body(payload)
    return email_data

# Extract flight info from most recent gmail
msg_id = get_latest_email_id()
data = extract_gmail_as_json(get_gmail_service(), msg_id)
flight_email = data.get('body', '')

# Uses environment variable to authenticate 
client = ChatOpenAI(model="gpt-4o-mini")

# Create chain for extracting flight data from email in JSON format
extract_flight = """I am building a trip itinerary for a family vacation. The following text in triple quotes contains flight information from the email confirmation I received from the airline.  There can be multiple passengers and flights in a single email confirmation. Extract the following relevant passenger and flight information.

The following pieces of information should be collected for each passenger that is traveling. Remember, there can be multiple passengers on each flight
- first_name 
- last_name 

The following pieces of information should be collected for each flight. There are usually multiple flights per email. 
- departure_date
- departure_time
- arrival_date
- arrival_time 
- origin
- destination
- flight_number
- airline_name

 ```{email}```

{format_instructions}
"""

extract_flight_prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract structured flight and passenger information from the text and convert it to JSON using ISO 8601 format for all datetime fields."),
    ("human", extract_flight)
])
flight_chain = extract_flight_prompt | client | flight_parser

# Extract flight info using chain
flight_chainparams = {'email': flight_email,
                      'format_instructions': flight_parser.get_format_instructions()}
flight_response = flight_chain.invoke(flight_chainparams)
flight_response.dict()

# Read sample itinerary
itinerary_path = TEST_DATA_DIR / "itinerary.txt"
itinerary_txt = itinerary_path.read_text()

# Create system prompt that uses CAG to insert reference info
system_instructions = f"""You are a chatbot for a travel app that answers questons about the travel itinerary. You have a trip itinerary for a family vacation to Banff. The following text in triple quotes contains the travel itinerary for all the family members that are traveling. Reference the trip itinerary for information to answer questions.  If there isn't enough details in the question, ask for additional information. If the information doesn't exist in the itinerary, let the user know that not enough informatioon was in the travel itinerary to answer their question. If the question can be accurately answered, respond with an answer.

The following pieces of information might be useful to extract from the travel itinerary:
Traveler Info
- first_name 
- last_name
- email 

Flight Info
- departure_date
- departure_time
- arrival_date
- arrival_time 
- origin
- destination
- flight_number
- airline_name

Activity Info
- activity name
- activity description
- date
- start time
- url

Hotels and Restaurants
- business_name
- address
- url
- date or date range
- business_description

Here is a travel itinerary for the group vacation. Reference information from this itinerary to answer questions.

Use a polite and concise tone when responding. Format the responses so it is intuitive and easy for users to read from a text messaging app.  Organize the information in an easy to read format (e.g., use bulllet points, format as outlines, include url links, format data in tables when appropriate.)
```{itinerary_txt}```
"""

# Create memory for chat
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Create chain for chat
question_prompt = ChatPromptTemplate.from_messages([
    ("system", "{system_instructions}"),
    ("ai", "{chat_history}"),
    ("human", "{question}")
])
question_chain = ConversationChain(
    llm=client, 
    prompt=question_prompt.partial(system_instructions=system_instructions),
    input_key='question',
    memory=memory,
    verbose=True
)

# Create chat response 
def ask_question(question):
    response = question_chain.predict(question=question)
    raw_history = question_chain.memory.load_memory_variables({})["chat_history"]
    formatted_history = format_history(raw_history)
    return formatted_history, ""

# Converts instances of messages into single str for displaying
def format_history(messages):
    """
    Converts ConversationBufferMemory messages into a formatted SMS-style string.
    Example output:
    You: Hello
    Bot: Hi there!
    You: What's the weather?
    Bot: It's sunny and 75°F.
    """
    lines = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            lines.append(f"You: {msg.content}")
        elif isinstance(msg, AIMessage):
            lines.append(f"TravelBot: {msg.content}\n----------")
        elif isinstance(msg, SystemMessage):
            # optional: include system messages if desired
            pass
        else:
            lines.append(f"{msg.type.capitalize()}: {msg.content}")
    return "\n".join(lines)

def clear_memory():
    """Clear the chatbot memory."""
    memory.clear()
    return "Chat memory cleared. Starting a new conversation!",""

# --- Gradio Interface ---
with gr.Blocks() as demo:
    gr.Markdown("## 📱 TravelBot (Prototype)")
    
    with gr.Row():
        chat_display = gr.Textbox(
            label="Conversation",
            interactive=False,
            value="",
            lines=15,
            elem_id="chat-history-box"
        )
    
    with gr.Row():
        user_input = gr.Textbox(label="Type your message")
    
    with gr.Row():
        send_btn = gr.Button("Send")
        clear_btn = gr.Button("Clear Memory")
    
    send_btn.click(
        ask_question, 
        inputs=user_input, 
        outputs=chat_display
    )
    user_input.submit(
        ask_question, 
        inputs=user_input, 
        outputs=[chat_display,user_input]
    )
    clear_btn.click(
        clear_memory, 
        outputs=[chat_display,user_input]        
    )


if __name__ == "__main__":
    demo.launch(share=True)
