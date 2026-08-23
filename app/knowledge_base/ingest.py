"""
Knowledge base ingestion pipeline.

Usage:
    python -m app.knowledge_base.ingest [--threshold 0.85] [--sources github kaggle thinkcloudly]

Flow per source:
    adapter.fetch()  →  normalize_batch()  →  dedup_candidates()  →  staging_questions.json

Nothing is written to questions.json here. Review the staging file, then run:
    python -m app.knowledge_base.merge_staging
"""
import argparse
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

_STAGING_PATH = Path(__file__).parent.parent.parent / "data" / "staging_questions.json"
_KB_PATH = Path(__file__).parent.parent.parent / "data" / "questions.json"


def _load_existing() -> list[dict]:
    with open(_KB_PATH) as f:
        return json.load(f)


def _run_source(source_id: str, fetch_fn, existing: list[dict], threshold: float) -> list[dict]:
    from app.knowledge_base.normalize import normalize_batch
    from app.knowledge_base.dedup import dedup_candidates

    logger.info("=" * 60)
    logger.info("SOURCE: %s", source_id)

    logger.info("  [1/3] Fetching raw Q&A …")
    try:
        raw = fetch_fn()
    except Exception as e:
        logger.error("  Fetch failed: %s", e)
        return []

    if not raw:
        logger.warning("  No Q&A pairs returned from adapter.")
        return []
    logger.info("  Fetched %d raw pairs", len(raw))

    logger.info("  [2/3] Normalizing via LLM (batch size 8) …")
    normalized = normalize_batch(raw, source_id)
    logger.info("  Normalized %d questions", len(normalized))

    logger.info("  [3/3] Deduplicating (threshold=%.2f) …", threshold)
    accepted, n_dropped = dedup_candidates(normalized, existing, threshold=threshold)
    logger.info("  Accepted %d, dropped %d duplicates", len(accepted), n_dropped)

    return accepted


def main():
    parser = argparse.ArgumentParser(description="Ingest questions into staging.")
    parser.add_argument(
        "--threshold", type=float, default=0.85,
        help="Cosine similarity threshold for dedup (default: 0.85)",
    )
    parser.add_argument(
        "--sources", nargs="+",
        choices=["github", "kaggle", "thinkcloudly"],
        default=["github", "kaggle", "thinkcloudly"],
        help="Which sources to run (default: all)",
    )
    args = parser.parse_args()

    from app.knowledge_base.sources import ALL_SOURCES

    source_map = {
        "github": ALL_SOURCES[0],
        "kaggle": ALL_SOURCES[1],
        "thinkcloudly": ALL_SOURCES[2],
    }

    existing = _load_existing()
    logger.info("Loaded %d existing questions from KB", len(existing))

    all_candidates: list[dict] = []

    for key in args.sources:
        source_id, fetch_fn = source_map[key]
        candidates = _run_source(source_id, fetch_fn, existing + all_candidates, args.threshold)
        all_candidates.extend(candidates)

    if not all_candidates:
        logger.warning("No new candidates produced. Staging file not written.")
        sys.exit(0)

    _STAGING_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_STAGING_PATH, "w") as f:
        json.dump(all_candidates, f, indent=2, ensure_ascii=False)

    logger.info("=" * 60)
    logger.info("Wrote %d candidates to %s", len(all_candidates), _STAGING_PATH)
    _print_summary(all_candidates)
    logger.info("")
    logger.info("Review / edit the staging file, then run:")
    logger.info("  python -m app.knowledge_base.merge_staging")


def _print_summary(candidates: list[dict]) -> None:
    from collections import Counter
    cats = Counter(q.get("category", "Unknown") for q in candidates)
    diffs = Counter(q.get("difficulty", "?") for q in candidates)
    types = Counter(q.get("question_type", "?") for q in candidates)
    sources = Counter(q.get("source", "?") for q in candidates)

    logger.info("--- Staging summary ---")
    logger.info("By source:     %s", dict(sources))
    logger.info("By category:   %s", dict(cats.most_common()))
    logger.info("By difficulty: %s", dict(diffs))
    logger.info("By type:       %s", dict(types))


if __name__ == "__main__":
    main()
