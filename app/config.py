"""
Central LLM factory.

All agents and tools import from here. Configured via env vars:
    OPENROUTER_API_KEY  — required
    OPENROUTER_MODEL      — default: openai/gpt-4o
    OPENROUTER_MODEL_FAST — default: openai/gpt-4o-mini  (extraction + tool calls)
"""

import os
from typing import Type, TypeVar

from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def get_llm(fast: bool = False) -> ChatOpenAI:
    """
    fast=False → OPENROUTER_MODEL      (default: openai/gpt-4o)      — reasoning-heavy agents
    fast=True  → OPENROUTER_MODEL_FAST (default: openai/gpt-4o-mini) — extraction + tool generation
    """
    model_env = "OPENROUTER_MODEL_FAST" if fast else "OPENROUTER_MODEL"
    default = "openai/gpt-4o-mini" if fast else "openai/gpt-4o"

    return ChatOpenAI(
        model=os.getenv(model_env, default),
        base_url=_OPENROUTER_BASE_URL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )


def get_structured_llm(model_class: Type[T], fast: bool = False):
    """
    Returns a runnable chain: LLM → validated Pydantic model instance.

    Passes the JSON schema as a dict (not the Pydantic class) to force
    langchain_openai onto the regular response_format path instead of the
    beta completions.parse() endpoint — which OpenRouter does not support.
    """
    schema = model_class.model_json_schema()
    llm = get_llm(fast=fast).with_structured_output(schema, method="json_schema")
    return llm | RunnableLambda(model_class.model_validate)
