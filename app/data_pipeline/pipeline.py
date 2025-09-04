# placeholder for pipeline orchestration
 
# Standard librarty
from pathlib import Path

# Third-party
from dotenv import load_dotenv
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

#Local application
from app.config import settings
from app.schemas.flight_manifest import FlightManifest
from app.data_pipeline.extract.gmail_extractor import (
    extract_gmail_as_json,      
    get_gmail_service, 
    get_inbox_email_ids
)

# --- Model client ---
client = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)

# --- Flight manifest parser ---
flight_parser = PydanticOutputParser(pydantic_object=FlightManifest)

# --- Extract flight info from most recent Gmail ---
msg_id = get_inbox_email_ids()
print(msg_id)
data = extract_gmail_as_json(get_gmail_service(), msg_id[-1])
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
print(flight_response)