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

from langchain_openai import ChatOpenAI

#Local application
import app.config as config

# --- Load environment variables ---
load_dotenv(dotenv_path=config.BASE_DIR / ".env")

# --- Model client ---
client = ChatOpenAI(model="gpt-4o-mini")

# --- Load itinerary text ---
itinerary_path = config.TEST_DATA_DIR / "test_itinerary.txt"
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
