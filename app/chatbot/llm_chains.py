"""
LLM Chain factory for TravelBot.
"""

from pathlib import Path

from langchain.chains import ConversationChain
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

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


# --- Conversation chain ---
question_prompt = ChatPromptTemplate.from_messages([
    ("system", "{system_instructions}"),
    ("human", "{question}"),
])
question_chain = ConversationChain(
    llm=get_llm(),
    prompt=question_prompt.partial(system_instructions=system_instructions),
    input_key="question",
    verbose=True,
)
