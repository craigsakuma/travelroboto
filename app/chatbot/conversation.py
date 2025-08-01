"""
Utility functions for managing chatbot conversation state and formatting.

This module provides helper functions to:
- Format conversation history into a user-friendly SMS-style display suitable for UI components.
- Generate chatbot responses using the configured LangChain conversation chain (`question_chain`),
  while updating and retrieving chat memory.

Functions:
    format_history(messages):
        Converts a list of LangChain message objects (HumanMessage, AIMessage, SystemMessage)
        into a readable, SMS-style conversation string.

    ask_question(question):
        Sends a question to the chatbot, updates conversation memory,
        and returns the formatted chat history along with an empty string
        (used to clear text input fields in the UI).
"""


from langchain.schema import HumanMessage, AIMessage, SystemMessage
from app.chatbot.llm_chains import question_chain

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

def get_chat_response(question):
    """
    Generates a chatbot response and formats chat history.
    Returns:
        formatted_history (str): SMS-style conversation
        "" (str): clears input box in UI
    """
    _ = question_chain.predict(question=question)
    raw_history = question_chain.memory.load_memory_variables({})["chat_history"]
    formatted_history = format_history(raw_history)
    return formatted_history, ""

