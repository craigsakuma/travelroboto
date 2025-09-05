"""
LLM Chain factory for TravelBot.
"""

from __future__ import annotations
import logging
import math

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable

from app.config import settings

logger = logging.getLogger(__name__)


def get_llm(
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    timeout: int | float = 30,
    max_retries: int = 2,
) -> ChatOpenAI:
    
    if not settings.openai_api_key:
        logger.error("OPENAI_API_KEY is not set")
        raise RuntimeError("OPENAI_API_KEY is not set. Configure it in Railway or your .env.")

    # validate temperature early (shared logic can also live here)
    if not (
        isinstance(temperature, (int, float))
        and math.isfinite(temperature)
        and 0.0 <= temperature <= 2.0
    ):
        raise ValueError("temperature must be a finite number between 0.0 and 2.0")

    msg = (
        f"Creating ChatOpenAI client: model={model}, temp={temperature}, "
        f"timeout={timeout}, retries={max_retries}"
    )
    logger.debug(msg)

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=settings.openai_api_key,
        timeout=timeout,
        max_retries=max_retries,
    )

def get_prompt(system_prompt: str) -> ChatPromptTemplate:
    if not isinstance(system_prompt, str) or not system_prompt.strip():
        raise ValueError("system_prompt must not be empty")
    sys_prompt = system_prompt.strip()  # normalize whitespace once
    
    logger.debug("Building ChatPromptTemplate")
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

    logger.debug("Building question chain (model={model}, temp={temperature})", model, temperature)
    prompt = get_prompt(system_prompt)
    llm = get_llm(model=model, temperature=temperature, timeout=timeout, max_retries=max_retries)
    chain: Runnable[dict, str] = prompt | llm | StrOutputParser()

    return chain.with_config({"run_name": run_name})