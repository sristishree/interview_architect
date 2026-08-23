"""
Merge approved staging questions into the production knowledge base.

Usage:
    python -m app.knowledge_base.merge_staging [--staging data/staging_questions.json]

Reads the staging file (edit/delete entries by hand first), then calls
QuestionStore.add() which assigns IDs and persists to questions.json.

Nothing runs automatically — this is the manual gate between review and production.
"""
import argparse
import json
import logging
from collections import Counter
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

_DEFAULT_STAGING = Path(__file__).parent.parent.parent / "data" / "staging_questions.json"


def main():
    parser = argparse.ArgumentParser(description="Merge approved staging questions into KB.")
    parser.add_argument(
        "--staging", type=Path, default=_DEFAULT_STAGING,
        help="Path to staging file (default: data/staging_questions.json)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be merged without writing anything",
    )
    args = parser.parse_args()

    if not args.staging.exists():
        logger.error("Staging file not found: %s", args.staging)
        logger.error("Run `python -m app.knowledge_base.ingest` first.")
        raise SystemExit(1)

    with open(args.staging) as f:
        candidates = json.load(f)

    if not candidates:
        logger.warning("Staging file is empty — nothing to merge.")
        raise SystemExit(0)

    logger.info("Staging file contains %d questions", len(candidates))
    _print_summary(candidates)

    if args.dry_run:
        logger.info("Dry run — no changes written.")
        raise SystemExit(0)

    confirm = input(f"\nMerge all {len(candidates)} questions into questions.json? [y/N] ").strip().lower()
    if confirm != "y":
        logger.info("Aborted.")
        raise SystemExit(0)

    from app.knowledge_base.store import QuestionStore
    store = QuestionStore()
    before = len(store.questions)
    store.add(candidates)
    after = len(store.questions)

    added = after - before
    logger.info("Added %d questions (%d already existed by ID — skipped).", added, len(candidates) - added)
    logger.info("Production KB now has %d questions.", after)

    # Archive the staging file so it's not accidentally re-merged
    archive_path = args.staging.with_suffix(".merged.json")
    args.staging.rename(archive_path)
    logger.info("Staging file archived to %s", archive_path)


def _print_summary(candidates: list[dict]) -> None:
    cats = Counter(q.get("category", "Unknown") for q in candidates)
    sources = Counter(q.get("source", "?") for q in candidates)
    diffs = Counter(q.get("difficulty", "?") for q in candidates)
    logger.info("  By source:     %s", dict(sources))
    logger.info("  By category:   %s", dict(cats.most_common()))
    logger.info("  By difficulty: %s", dict(diffs))


if __name__ == "__main__":
    main()
