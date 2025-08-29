"""
Utility functions for managing chatbot conversation state and formatting.

This module provides helper functions to:
- Format conversation history into a user-friendly SMS-style display suitable for UI components.
- Generate chatbot responses using the configured LangChain conversation chain (`get_chat_response`),
  while updating and retrieving chat memory from individual sessions.
"""


from langchain.schema import HumanMessage, AIMessage, SystemMessage
from app.chatbot.llm_chains import get_chat_session_chain

def format_history(messages):
    """
    Converts ConversationBufferMemory messages into an SMS-style string.
    Example:
    You: Hello
    TravelBot: Hi there!
    """
    lines = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            lines.append(f"You: {msg.content}")
        elif isinstance(msg, AIMessage):
            lines.append(f"TravelBot: {msg.content}\n----------")
        elif isinstance(msg, SystemMessage):
            # Optional: handle system messages if desired
            pass
        else:
            lines.append(f"{msg.type.capitalize()}: {msg.content}")
    return "\n".join(lines)


def get_chat_response(message, session_id: str):
    """
    Generates a chatbot response and formats chat history for a given session.
        Returns:
        formatted_history (str): SMS-style conversation
        "" (str): clears input box in UI
    """
    chain = get_chat_session_chain(session_id)
    _ = chain.predict(message=message)
    raw_history = chain.memory.load_memory_variables({})["history"]
    formatted_history = format_history(raw_history)
    return formatted_history, ""