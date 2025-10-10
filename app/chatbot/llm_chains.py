"""
Helpers for constructing chat LLM chains.

Provides thin wrappers around LangChain primitives to:
- Validate and instantiate ChatOpenAI clients.
- Build parameterized system/user prompts.
- Compose Prompt → LLM → StrOutputParser pipelines.
"""

from __future__ import annotations

import logging
import math

from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.config import settings
from app.logging_utils import (
    get_logger,
    log_context,
    log_with_id,
    truncate_msg,
)

logger = get_logger(__name__)


def get_llm(
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    timeout: int | float = 30,
    max_retries: int = 2,
) -> ChatOpenAI:
    """
    Create a ChatOpenAI client with basic validation.

    Raises:
        RuntimeError: if OPENAI_API_KEY is unset.
        ValueError: if temperature is not within [0.0, 2.0].
    """
    if not settings.openai_api_key:
        log_with_id(logger, logging.ERROR, "missing_api_key")
        raise RuntimeError("OPENAI_API_KEY is not set. Configure it in Railway or your .env.")

    # validate temperature early (shared logic can also live here)
    if not (
        isinstance(temperature, (int, float))
        and math.isfinite(temperature)
        and 0.0 <= temperature <= 2.0
    ):
        raise ValueError("temperature must be a finite number between 0.0 and 2.0")

    with log_context(
        logger,
        "create_llm_client",
        model=model,
        temperature=temperature,
        timeout=timeout,
        retries=max_retries,
    ):
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=settings.openai_api_key,
            timeout=timeout,
            max_retries=max_retries,
        )


def get_prompt(system_prompt: str) -> ChatPromptTemplate:
    """
    Build the chat prompt.

    Expects template variables:
      - {question} : user input
      - {context}  : optional itinerary/RAG context (provided by service layer)
    """
    if not isinstance(system_prompt, str) or not system_prompt.strip():
        raise ValueError("system_prompt must not be empty")

    sys_prompt = system_prompt.strip()
    log_with_id(
        logger,
        logging.DEBUG,
        "build_prompt",
        sys_preview=truncate_msg(sys_prompt, 120),
    )

    return ChatPromptTemplate.from_messages(
        [
            ("system", sys_prompt),
            ("human", "{question}"),
        ]
    )


def build_question_chain(
    *,
    system_prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    run_name: str = "travelbot_qna_v1",
    timeout: int | float = 30,
    max_retries: int = 2,
) -> Runnable[dict, str]:
    """
    Compose LCEL: Prompt → LLM → StrOutputParser, tagged with `run_name`.
    """
    with log_context(
        logger,
        "build_question_chain",
        model=model,
        temperature=temperature,
        run_name=run_name,
    ):
        prompt = get_prompt(system_prompt)
        llm = get_llm(
            model=model,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries,
        )
        chain: Runnable[dict, str] = prompt | llm | StrOutputParser()
        log_with_id(logger, logging.INFO, "chain_built")
        return chain.with_config({"run_name": run_name})
