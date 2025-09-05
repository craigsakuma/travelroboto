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