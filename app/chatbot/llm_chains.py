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

# --- Load itinerary text ---
itinerary_path = config.TEST_DATA_DIR / "test_itinerary.txt"
itinerary_txt = itinerary_path.read_text()

# --- System prompt for chat ---
chat_system_instructions = f"""You are a chatbot for a travel app that answers questons about the travel itinerary. You have a trip itinerary for a family vacation to Banff. The following text in triple quotes contains the travel itinerary for all the family members that are traveling. Reference the trip itinerary for information to answer questions.  If there isn't enough details in the question, ask for additional information. If the information doesn't exist in the itinerary, let the user know that not enough informatioon was in the travel itinerary to answer their question. If the question can be accurately answered, respond with an answer.

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

# Dictionary to hold session-specific chains
_sessions = {}

def get_chat_session_chain(session_id: str):
    """
    Retrieve or create a ConversationChain with memory for the given session.
    """
    if session_id not in _sessions:
        memory = ConversationBufferMemory(memory_key="history", return_messages=True)
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", "{chat_system_instructions}"),
            # ("human", "{history}"),
            ("human", "{message}"),
        ])
    
        client = ChatOpenAI(model="gpt-4o-mini")

        chain = ConversationChain(
            llm=client,
            prompt=chat_prompt.partial(chat_system_instructions=chat_system_instructions),
            input_key="message",
            memory=memory,
            verbose=True
        )
        _sessions[session_id] = chain
    return _sessions[session_id]



def get_chat_response(session_id: str, message: str) -> list[dict]:
    """Run chat and return entire history as [{'sender': 'human'|'ai', 'content': str}, ...]."""
    chain = get_chat_session_chain(session_id)
    chain.invoke(message)

    # Retrieve memory as structured message list
    messages = chain.memory.chat_memory.messages
    history = []
    for msg in messages:
        if msg.type == "human":
            history.append({"sender": "human", "content": msg.content})
        elif msg.type == "ai":
            history.append({"sender": "ai", "content": msg.content})
    return history


# def get_chat_response(message: str, session_id: str, instructions: str = "You are a helpful travel assistant"):
#     """
#     Generate a chat response for a given session.
#     """
#     chain = get_session_chain(session_id)
#     # Pass only the new message and system instructions
#     return chain.invoke(message=message, chat_system_instructions=instructions)


def clear_session_memory(session_id: str):
    """
    Clears chatbot conversation memory.
    Returns:
        str: confirmation message
        str: clears input box in UI
    """
    if session_id in _sessions:
        _sessions[session_id].memory.clear()
    return "Chat memory cleared. Starting a new conversation!", "" # empty string for clearing input text box
