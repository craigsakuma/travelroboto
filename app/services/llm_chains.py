"""
LLM Chain construction for TravelBot.

This module:
- Builds the flight extraction chain
- Builds the conversation chain with memory
"""

# Standard librarty
from pathlib import Path

# Third-party
from dotenv import load_dotenv
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
# from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

#Local application
import app.config as config
import app.models as models
from app.services.gmail_service import (
    extract_gmail_as_json,      
    get_gmail_service, 
    get_latest_email_id
)

# --- Load environment variables ---
load_dotenv(dotenv_path=Path.home() / ".env")

# --- Model client ---
client = ChatOpenAI(model="gpt-4o-mini")

# --- Flight manifest parser ---
flight_parser = PydanticOutputParser(pydantic_object=models.FlightManifest)

# --- Extract flight info from most recent Gmail ---
msg_id = get_latest_email_id()
data = extract_gmail_as_json(get_gmail_service(), msg_id)
flight_email = data.get("body", "")

# --- Flight extraction prompt and chain ---
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
    ("system", "Extract structured flight and passenger information as JSON (ISO 8601 datetime format)."),
    ("human", extract_flight),
])
flight_chain = extract_flight_prompt | client | flight_parser

# --- Run flight extraction (optional) ---
flight_chain_params = {
    "email": flight_email,
    "format_instructions": flight_parser.get_format_instructions(),
}
flight_response = flight_chain.invoke(flight_chain_params)
_ = flight_response.dict()

# --- Load itinerary text ---
itinerary_path = config.TEST_DATA_DIR / "itinerary.txt"
itinerary_txt = itinerary_path.read_text()

# --- System prompt for chat ---
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

def clear_memory():
    """
    Clears chatbot conversation memory.
    Returns:
        str: confirmation message
        str: clears input box in UI
    """
    question_chain.memory.clear()
    return "Chat memory cleared. Starting a new conversation!", ""

# --- Memory for conversation ---
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# --- Conversation chain ---
question_prompt = ChatPromptTemplate.from_messages([
    ("system", "{system_instructions}"),
    ("ai", "{chat_history}"),
    ("human", "{question}"),
])
question_chain = ConversationChain(
    llm=client,
    prompt=question_prompt.partial(system_instructions=system_instructions),
    input_key="question",
    memory=memory,
    verbose=True,
)
