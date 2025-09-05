"""
Conversation service for TravelBot.

Provides a synchronous entry point for generating chatbot responses
using the configured LangChain chain. Includes a module-level logger
for lightweight observability.
"""

import logging
from typing import Tuple

from langchain.schema import HumanMessage, AIMessage, SystemMessage
from app.chatbot.llm_chains import question_chain

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are a chatbot for a travel app that answers questions about the travel itinerary. "
    "You have a trip itinerary for a family vacation to Banff. The following text in triple "
    "quotes contains the travel itinerary for all the family members that are traveling. "
    "Reference the trip itinerary for information to answer questions. If there isn't enough "
    "detail in the question, ask for additional information. If the information doesn't exist "
    "in the itinerary, let the user know.\n\n"
    "Format responses for a text messaging UI: be concise, use bullet points or tables where helpful, "
    "and include URLs when relevant.\n\n"
    "Trip itinerary:\n```{trip_context}```"
)

trip_context = Path(settings.trip_context_path).read_text(encoding="utf-8")

def get_chat_response(question: str) -> Tuple[str, str]:
    """
    Generates a chatbot response using the configured LangChain conversation chain.

    Args:
        question (str): The user's question text.

    Returns:
        tuple[str, str]: A tuple of:
            - formatted_history: Minimal SMS-style one-turn transcript
            - ""               : Placeholder to clear input boxes in UI flows

    Notes:
        - Logging is intentionally light and avoids printing sensitive data.
    """
    preview = (question or "").strip().replace("\n", " ")
    if len(preview) > 80:
        preview = preview[:77] + '...'
    logger.info(f"Generating chat response (preview={preview})")

    response = question_chain.predict(question=question)
    return f"You: {question}\nTravelbot: {response}\n----------", ""

# TODO(memory): In Phase 2, introduce a HistoryRepo interface:
# class ChatHistoryRepo(Protocol):
#     async def load_recent(self, chat_id: str, limit: int = 20) -> list[dict]: ...
#     async def append(self, chat_id: str, messages: list[dict]) -> None: ...
# Then wire it here (not in llm_chains.py) to keep concerns separated.