"""
LLM Chain construction for TravelBot.

This module:
- Builds the flight extraction chain
- Builds the conversation chain with memory
"""

from pathlib import Path

from langchain.chains import ConversationChain
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings


# --- Model client ---
client = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)

# --- Conversation chain ---
question_prompt = ChatPromptTemplate.from_messages([
    ("system", "{system_instructions}"),
    ("human", "{question}"),
])
question_chain = ConversationChain(
    llm=client,
    prompt=question_prompt.partial(system_instructions=system_instructions),
    input_key="question",
    verbose=True,
)
