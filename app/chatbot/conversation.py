"""
Utility functions for managing chatbot conversation state and formatting.

This module provides helper functions to:
- Generate chatbot responses using the configured LangChain conversation chain (`question_chain`),


Functions:
    get_chat_response(question):
        Sends a question to the chatbot, and returns the formatted chat
        question and response along with an empty string (used to clear text
        input fields in the UI).
"""


from langchain.schema import HumanMessage, AIMessage, SystemMessage
from app.chatbot.llm_chains import question_chain

def get_chat_response(question):
    """
    Generates a chatbot response and formats chat history.
    Returns:
        formatted_history (str): SMS-style conversation
        "" (str): clears input box in UI
    """
    response = question_chain.predict(question=question)
    return f"You: {question}\nTravelbot: {response}\n----------", ""

# TODO(memory): In Phase 2, introduce a HistoryRepo interface:
# class ChatHistoryRepo(Protocol):
#     async def load_recent(self, chat_id: str, limit: int = 20) -> list[dict]: ...
#     async def append(self, chat_id: str, messages: list[dict]) -> None: ...
# Then wire it here (not in llm_chains.py) to keep concerns separated.