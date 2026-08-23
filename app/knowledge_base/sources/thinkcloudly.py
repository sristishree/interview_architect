"""
ThinkCloudly blog adapter.

Scrapes Q&A pairs from thinkcloudly.com interview-question blog posts.

Configure via env var:
    THINKCLOUDLY_URLS — comma-separated list of page URLs to scrape
                        Defaults to the known cloud-AI interview Q&A pages.
"""
import logging
import os
from typing import List

import requests

logger = logging.getLogger(__name__)

SOURCE_ID = "blog:thinkcloudly.com"

_DEFAULT_URLS = [
    "https://thinkcloudly.com/blogs/artificial-intelligence/ai-interview-questions-and-answers/",
    "https://thinkcloudly.com/blogs/cloud-computing/aws-interview-questions-and-answers/",
    "https://thinkcloudly.com/blogs/cloud-computing/azure-interview-questions-and-answers/",
    "https://thinkcloudly.com/blogs/cloud-computing/gcp-interview-questions-and-answers/",
]

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; interview-architect-ingest/1.0)"}


def fetch() -> List[dict]:
    """Returns list of {"raw_question": str, "raw_answer": str | None}."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("beautifulsoup4 not installed. Run: pip install beautifulsoup4")
        return []

    env_urls = os.getenv("THINKCLOUDLY_URLS")
    urls = [u.strip() for u in env_urls.split(",")] if env_urls else _DEFAULT_URLS

    all_pairs = []
    for url in urls:
        try:
            pairs = _scrape_page(url, BeautifulSoup)
            logger.info("ThinkCloudly: %d pairs from %s", len(pairs), url)
            all_pairs.extend(pairs)
        except Exception as e:
            logger.warning("Failed to scrape %s: %s", url, e)

    logger.info("ThinkCloudly adapter total: %d Q&A pairs", len(all_pairs))
    return all_pairs


def _scrape_page(url: str, BeautifulSoup) -> List[dict]:
    resp = requests.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    pairs = []

    # Pattern 1: <h3> or <strong> question followed by <p> answer
    # ThinkCloudly typically uses numbered headings for questions
    for tag in soup.find_all(["h2", "h3", "h4"]):
        text = tag.get_text(strip=True)
        if not _looks_like_question(text):
            continue

        answer_parts = []
        for sib in tag.find_next_siblings():
            if sib.name in ("h2", "h3", "h4"):
                break
            if sib.name in ("p", "ul", "ol"):
                answer_parts.append(sib.get_text(separator=" ", strip=True))
            if len(answer_parts) >= 3:
                break

        pairs.append({
            "raw_question": _strip_numbering(text),
            "raw_answer": " ".join(answer_parts) or None,
        })

    # Pattern 2: definition-list style or FAQ schema markup
    if not pairs:
        for item in soup.find_all(attrs={"itemtype": True}):
            q_el = item.find(attrs={"itemprop": "name"})
            a_el = item.find(attrs={"itemprop": "acceptedAnswer"})
            if q_el:
                pairs.append({
                    "raw_question": q_el.get_text(strip=True),
                    "raw_answer": a_el.get_text(separator=" ", strip=True) if a_el else None,
                })

    return pairs


def _looks_like_question(text: str) -> bool:
    t = text.lower().strip()
    return (
        "?" in t
        or t.startswith(("what ", "how ", "why ", "when ", "which ", "explain ", "describe "))
        or (len(t) > 10 and any(char.isdigit() for char in t[:4]))
    )


def _strip_numbering(text: str) -> str:
    import re
    return re.sub(r"^\d+[\.\)]\s*", "", text).strip()
