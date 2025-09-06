"""
Conversation service for TravelBot.

Provides a synchronous entry point for generating chatbot responses
using the configured LangChain chain. Includes a module-level logger
for lightweight observability.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optonal, Tuple

from app.config import settings
from app.chatbot.llm_chains import build_question_chain

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

def _resolve_trip_path(override: Optional[str]) -> Optional[str]:
    return override or getattr(settings, "trip_context_path", None)


async def load_trip_context(path_str: Optional[str] = None) -> str:
    if not path_str:   
        logger.warning(f"No trip_context_path provided; continuing with empty context")
        return ""
    
    p = Path(path_str)

    if not p.exists():
        logger.warning(f"Trip context file not found at {p}")
        return ""
    logger.debug(f"Loading trip context from {p}")

    try:
        return await asyncio.to_thread(p.read_text(encoding="utf-8"))
    except Exception as e:
        logger.exception(f"Failed reading trip context at {p}: {e}")
        return "" 
        

async def get_chat_response(
        message: str,
        *,
        model: str = "gpt-4o-mini", 
        temperature: float = 0.2,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        trip_context_path: Optional[str] = None    
) -> Tuple[str, str]:
    
    preview = (message or "").strip().replace("\n", " ")
    if len(preview) > 80:
        preview = preview[:77] + '...'
    logger.info(f"Generating chat response (preview={preview})")

    resolved_path = _resolve_trip_path(trip_context_path)
    context = await load_trip_context(resolved_path)

    chain = build_question_chain(
        system_prompt=system_prompt,
        model=model,
        temperature=temperature
    )
    return await chain.ainvoke({"question": message, "context": context})

# TODO(memory): In Phase 2, introduce a HistoryRepo interface:
# class ChatHistoryRepo(Protocol):
#     async def load_recent(self, chat_id: str, limit: int = 20) -> list[dict]: ...
#     async def append(self, chat_id: str, messages: list[dict]) -> None: ...
# Then wire it here (not in llm_chains.py) to keep concerns separated.