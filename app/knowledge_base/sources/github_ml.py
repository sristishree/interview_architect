"""
GitHub ML/DS Q&A adapter.

One LLM call inspects a sample of the markdown to derive a parsing spec
(question marker, answer marker, block separator). All subsequent extraction
is pure regex — no per-question LLM overhead.

Fallback: if regex yields fewer than MIN_EXPECTED pairs, falls back to a
full LLM extraction pass so we never silently lose content.

Configure via env var:
    GITHUB_ML_QA_URL — raw GitHub URL of the markdown file
                       Default: youssefHosni/Data-Science-Educational-Repo ML interview file
"""
import logging
import os
import re
from typing import List, Optional

import requests
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_DEFAULT_URL = (
    "https://raw.githubusercontent.com/youssefHosni/Data-Science-Educational-Repo"
    "/main/Interview%20Questions%20%26%20Answers"
    "/ML%20Interview%20Questions%20%26%20Answers%20for%20Data%20Scientists.md"
)

SOURCE_ID = "github:youssefHosni/Data-Science-Educational-Repo"

# How many lines to send to the LLM for format detection
_SAMPLE_LINES = 80
# Warn + fallback if regex extracts fewer than this
MIN_EXPECTED = 10


# ── Structured output from the format-detection LLM call ─────────────────────

class MDParsingSpec(BaseModel):
    """
    Describes how Q&A pairs are laid out in one markdown file.
    The LLM fills this in from a sample; we build regex from it.
    """
    question_prefix: str        # e.g. "## Q", "**Q", "#### ", "1."
    answer_prefix: Optional[str] = None   # e.g. "**A", "Answer:", "**Answer**"
    block_separator: Optional[str] = None # e.g. "---", "***", blank line between blocks
    notes: Optional[str] = None  # free-text observations (not used in parsing)


# ── Main entry point ──────────────────────────────────────────────────────────

def fetch() -> List[dict]:
    """Returns list of {"raw_question": str, "raw_answer": str | None}."""
    url = os.getenv("GITHUB_ML_QA_URL", _DEFAULT_URL)
    logger.info("Fetching GitHub MD from %s", url)

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    markdown = resp.text

    return _extract_qa(markdown)


# ── Two-stage extraction ──────────────────────────────────────────────────────

def _extract_qa(markdown: str) -> List[dict]:
    sample = "\n".join(markdown.splitlines()[:_SAMPLE_LINES])

    logger.info("Detecting markdown format via LLM (1 call) …")
    spec = _detect_format(sample)
    if spec:
        logger.info(
            "Detected — question_prefix=%r  answer_prefix=%r  separator=%r",
            spec.question_prefix, spec.answer_prefix, spec.block_separator,
        )
        pairs = _regex_extract(markdown, spec)
        if len(pairs) >= MIN_EXPECTED:
            logger.info("Regex extracted %d Q&A pairs", len(pairs))
            return pairs
        logger.warning(
            "Regex only found %d pairs (expected ≥%d) — falling back to LLM extraction",
            len(pairs), MIN_EXPECTED,
        )

    logger.info("Running LLM fallback extraction …")
    return _llm_extract_fallback(markdown)


# ── Step 1: one LLM call to understand the format ────────────────────────────

def _detect_format(sample: str) -> Optional[MDParsingSpec]:
    from app.config import get_structured_llm

    prompt = (
        "Analyse the markdown sample below and describe how Q&A pairs are structured.\n\n"
        "Identify:\n"
        "- question_prefix: the exact string that starts every question line "
        "(e.g. '## Q', '**Q', '#### ', a number like '1.')\n"
        "- answer_prefix: the exact string that starts every answer block "
        "(e.g. '**A', 'Answer:', '**Answer**') — null if answers follow the question directly\n"
        "- block_separator: a separator line between Q&A blocks (e.g. '---', '***') — "
        "null if blocks are separated only by blank lines\n\n"
        f"Sample:\n```\n{sample}\n```"
    )

    try:
        spec = get_structured_llm(MDParsingSpec, fast=True).invoke(prompt)
        return spec
    except Exception as e:
        logger.error("Format detection LLM call failed: %s", e)
        return None


# ── Step 2: regex extraction using the spec ───────────────────────────────────

def _regex_extract(markdown: str, spec: MDParsingSpec) -> List[dict]:
    q_prefix = re.escape(spec.question_prefix.strip())
    a_prefix = re.escape(spec.answer_prefix.strip()) if spec.answer_prefix else None
    separator = re.escape(spec.block_separator.strip()) if spec.block_separator else None

    # Split the document into blocks
    if separator:
        blocks = re.split(rf"^{separator}\s*$", markdown, flags=re.MULTILINE)
    else:
        # Split on double-blank-lines
        blocks = re.split(r"\n{2,}", markdown)

    pairs = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        q_match = re.search(rf"^{q_prefix}\s*(.+?)$", block, re.MULTILINE | re.IGNORECASE)
        if not q_match:
            continue
        question = q_match.group(1).strip().rstrip("?").strip() + "?"

        # Extract answer: everything after the answer prefix (or after the question line)
        answer = None
        if a_prefix:
            a_match = re.search(
                rf"^{a_prefix}\s*(.+?)(?=^{q_prefix}|\Z)",
                block,
                re.MULTILINE | re.DOTALL | re.IGNORECASE,
            )
            if a_match:
                answer = a_match.group(1).strip() or None
        else:
            # Answer is the text after the question line
            after_q = block[q_match.end():].strip()
            answer = after_q if after_q else None

        pairs.append({"raw_question": question, "raw_answer": answer})

    return pairs


# ── Fallback: full LLM extraction (original approach) ────────────────────────

def _llm_extract_fallback(markdown: str) -> List[dict]:
    from pydantic import BaseModel as PydanticBase
    from app.config import get_structured_llm

    class RawQA(PydanticBase):
        raw_question: str
        raw_answer: Optional[str] = None

    class RawQAList(PydanticBase):
        pairs: List[RawQA]

    prompt = (
        "Extract every question-answer pair from the markdown below.\n"
        "Return ALL pairs. If a question has no answer, set raw_answer to null.\n"
        "Do not paraphrase — copy verbatim.\n\n"
        f"```markdown\n{markdown[:14000]}\n```"
    )

    try:
        result = get_structured_llm(RawQAList, fast=True).invoke(prompt)
        pairs = [{"raw_question": p.raw_question, "raw_answer": p.raw_answer} for p in result.pairs]
        logger.info("LLM fallback extracted %d Q&A pairs", len(pairs))
        return pairs
    except Exception as e:
        logger.error("LLM fallback extraction also failed: %s", e)
        return []
