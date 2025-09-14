"""
Conversation service for TravelBot (stateless for Pass 1).

- Loads trip context on demand (safe if missing, non-blocking).
- Builds the chain via factories on demand.
- Returns a single string response.

TODO(memory, Pass 2): introduce a ChatHistoryRepo interface:
  class ChatHistoryRepo(Protocol):
      async def load_recent(self, chat_id: str, limit: int = 20) -> list[dict]: ...
      async def append(self, chat_id: str, messages: list[dict]) -> None: ...
Then wire it here (not in llm_chains.py) to keep concerns separated.
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional, Tuple

from app.config import settings
from app.chatbot.llm_chains import build_question_chain
from app.logging_utils import (  
    get_logger,
    log_with_id,
    log_context,
    truncate_msg,
)

logger = get_logger(__name__)

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
    """
    Resolve which trip context path to use, preferring an explicit override.

    Args:
        override: Optional explicit file path to a trip context.

    Returns:
        The string path to use, or None if not provided/configured.
    """
    return override or getattr(settings, "trip_context_path", None)


async def load_trip_context(path_str: Optional[str] = None) -> str:
    """
    Load the trip itinerary context text from disk without blocking the event loop.

    Args:
        path_str: Optional explicit path. If None or empty, returns an empty string.

    Returns:
        The file contents as a string, or an empty string if not found / not provided.
    """
    if not path_str:   
        logger.warning(f"No trip_context_path provided; continuing with empty context")
        return ""
    
    p = Path(path_str)
    if not p.exists():
        log_with_id(logger, level=logging.WARNING, event="trip_context_not_found", path=str(p))  
        return ""

    log_with_id(logger, level=logging.DEBUG, event="trip_context_load", path=str(p))  
    try:
        return await asyncio.to_thread(p.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.exception("Failed reading trip context at %s: %s", p, exc)
        log_with_id(
            logger,
            level=logging.ERROR,
            event="trip_context_read_failed",
            path=str(p),
            error=str(exc),
        )
        return ""

        
@lru_cache(maxsize=8)    
def _get_cached_chain(system_prompt: str, model: str, temperature: float):
    """
    Build (or reuse) a question chain keyed by its main configuration.

    Notes:
        - system_prompt, model, and temperature are hashable; this enables simple caching.
        - If you rotate keys or change prompts frequently, consider a more explicit cache.
    """
    log_with_id(
        logger,
        level=logging.DEBUG,
        event="chain_cache_build",
        model=model,
        temperature=temperature,
        prompt_hash=hash(system_prompt),
    )
    return build_question_chain(
        system_prompt=system_prompt,
        model=model,
        temperature=temperature,
    )

def dump_chain_cache_stats() -> str:
    """
    Return a human-readable string of LRU cache statistics.

    Useful for monitoring cache efficiency (hits vs. misses) and debugging
    performance when multiple prompt/model/temperature combos are used.

    Returns:
        str: formatted stats string (e.g. "hits=5 misses=2 currsize=3 maxsize=8")
    """
    info = _get_cached_chain.cache_info()
    return (
        f"hits={info.hits} "
        f"misses={info.misses} "
        f"currsize={info.currsize} "
        f"maxsize={info.maxsize}"
    )

def clear_chain_cache() -> None:
    """
    Clear all entries from the cached question-chain factory.

    Use this when:
      - Updating the default system prompt,
      - Switching models globally,
      - Or during debugging to reset cache state.
    """
    _get_cached_chain.cache_clear()


async def get_chat_response(
        message: str,
        *,
        model: str = "gpt-4o-mini", 
        temperature: float = 0.2,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        trip_context_path: Optional[str] = None    
) -> Tuple[str, str]:
    """
    Stateless ask: build/reuse the chain and call LLM with provided message + optional context.

    Args:
        message: User's question text.
        model: OpenAI model name to use.
        temperature: Sampling temperature (typically 0.0 - 2.0).
        system_prompt: System instructions for the LLM.
        trip_context_path: Optional file path to itinerary text; overrides settings.trip_context_path.

    Returns:
        str: LLM-generated response

    Raises:
        ValueError: If `message` is empty/whitespace.
        RuntimeError: If LLM invocation fails.
    """    
    if not message or not message.strip():
        log_with_id(logger, level=logging.ERROR, event="chat_empty_message") 
        raise ValueError("Message must not be empty")
    
    preview_base = (message or "").strip().replace("\n", " ")
    preview = truncate_msg(preview_base, max_length=80)
    log_with_id(logger, level=logging.INFO, event="chat_generate", preview=preview)

    resolved_path = _resolve_trip_path(trip_context_path)
    context = await load_trip_context(resolved_path)

    chain = _get_cached_chain(
        system_prompt=system_prompt,
        model=model,
        temperature=temperature
    )

    # Time the LLM call with a scoped log
    with log_context(
        logger,
        event="chain_invoke",
        model=model,
        temperature=temperature,
    ):
        try:
            # IMPORTANT: pass the variable name that your prompt expects (trip_context)
            return await chain.ainvoke({"question": message, "trip_context": context})
        except Exception as exc:  
            logger.exception("Error during chain invocation for message=%s: %s", message, exc)
            log_with_id(
                logger,
                level=logging.ERROR,  
                event="chain_invoke_error",
                model=model,
                temperature=temperature,
                err=str(exc),
            )
            raise RuntimeError(
                f"Chat response generation failed (model={model}, temp={temperature})"
            ) from exc

if __name__ == "__main__":
    import sys

    async def _demo():
        q = " ".join(sys.argv[1:]) or "What time is our flight to Banff"
        try:
            response = await get_chat_response(q)
            print(response)
        except Exception as err:
            print(f"[error] {err}", file=sys.stderr)
            sys.exit(1)
    
    asyncio.run(_demo())

# TODO(memory): In Phase 2, introduce a HistoryRepo interface:
# class ChatHistoryRepo(Protocol):
#     async def load_recent(self, chat_id: str, limit: int = 20) -> list[dict]: ...
#     async def append(self, chat_id: str, messages: list[dict]) -> None: ...
# Then wire it here (not in llm_chains.py) to keep concerns separated.