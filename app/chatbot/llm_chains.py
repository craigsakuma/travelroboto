"""
LLM Chain factory for TravelBot.
"""

from pathlib import Path

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable

from app.config import settings


def get_llm(
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    timeout: int | float = 30,
    max_retries: int = 2,
) -> ChatOpenAI:
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=settings.openai_api_key,
        timeout=timeout,
        max_retries=max_retries,
    )

def get_prompt(system_prompt: str) -> ChatPromptTemplate:
    sys_prompt = system_prompt.strip()  # normalize whitespace once

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

    prompt = get_prompt(system_prompt)
    llm = get_llm(model=model, temperature=temperature, timeout=timeout, max_retries=max_retries)
    chain: Runnable[dict, str] = prompt | llm | StrOutputParser()
    
    return chain.with_config({"run_name": run_name})