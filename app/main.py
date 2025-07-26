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
from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict, Literal, Optional

# Third-party
import gradio as gr

from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

# Local application
import app.config as config
import app.models as models
from app.services.gmail_service import (
    extract_gmail_as_json,
    get_gmail_service,
    get_latest_email_id,
)

TEST_DATA_DIR = config.TEST_DATA_DIR

load_dotenv(dotenv_path=Path.home() / ".env")
    
flight_parser = PydanticOutputParser(pydantic_object=models.FlightManifest)

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
