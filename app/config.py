"""
Central LLM factory.

All agents and tools import from here so the LiteLLM base_url and api_key
are configured in one place. Swap LITELLM_* env vars to point at any backend.
"""

import os
from typing import Type, TypeVar

from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def get_llm(fast: bool = False) -> ChatOpenAI:
    """
    fast=False → LITELLM_MODEL      (default: gpt-4o)   — reasoning-heavy agents
    fast=True  → LITELLM_MODEL_FAST (default: gpt-4o-mini) — extraction + tool generation
    """
    model_env = "LITELLM_MODEL_FAST" if fast else "LITELLM_MODEL"
    default = "gpt-4o-mini" if fast else "gpt-4o"

    return ChatOpenAI(
        model=os.getenv(model_env, default),
        base_url=os.getenv("LITELLM_BASE_URL"),
        api_key=os.getenv("LITELLM_API_KEY"),
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
