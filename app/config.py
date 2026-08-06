"""
Central LLM factory.

All agents and tools import from here so the LiteLLM base_url and api_key
are configured in one place. Swap LITELLM_* env vars to point at any backend.
"""

import os

from langchain_openai import ChatOpenAI


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
