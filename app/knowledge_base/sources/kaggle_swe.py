"""
Kaggle software-engineering interview questions adapter.

Downloads a Kaggle dataset via kagglehub and extracts Q&A rows from CSVs.

Configure via env vars:
    KAGGLE_DATASET_SLUG — dataset handle e.g. "syedmharis/software-engineering-interview-questions-dataset"
    KAGGLE_QUESTION_COL — CSV column name for the question text (default: "question")
    KAGGLE_ANSWER_COL   — CSV column name for the answer text (default: "answer")
"""
import csv
import logging
import os
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

_DEFAULT_SLUG = "syedmharis/software-engineering-interview-questions-dataset"
SOURCE_ID = "kaggle:syedmharis/software-engineering-interview-questions-dataset"


def fetch() -> List[dict]:
    """Returns list of {"raw_question": str, "raw_answer": str | None}."""
    try:
        import kagglehub
    except ImportError:
        logger.error("kagglehub not installed. Run: pip install kagglehub")
        return []

    slug = os.getenv("KAGGLE_DATASET_SLUG", _DEFAULT_SLUG)
    q_col = os.getenv("KAGGLE_QUESTION_COL", "question")
    a_col = os.getenv("KAGGLE_ANSWER_COL", "answer")

    logger.info("Downloading Kaggle dataset %s", slug)
    try:
        path = kagglehub.dataset_download(slug)
    except Exception as e:
        logger.error("Kaggle download failed: %s", e)
        return []

    csv_files = list(Path(path).glob("**/*.csv"))
    if not csv_files:
        logger.error("No CSV files found in dataset at %s", path)
        return []

    pairs = []
    for csv_path in csv_files:
        logger.info("Reading %s", csv_path.name)
        with open(csv_path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                continue

            fields_lower = {c.lower(): c for c in reader.fieldnames}
            q_key = fields_lower.get(q_col.lower())
            a_key = fields_lower.get(a_col.lower())

            if q_key is None:
                logger.warning(
                    "Column '%s' not found in %s. Available: %s",
                    q_col, csv_path.name, list(reader.fieldnames),
                )
                continue

            for row in reader:
                q = (row.get(q_key) or "").strip()
                a = (row.get(a_key) or "").strip() if a_key else None
                if q:
                    pairs.append({"raw_question": q, "raw_answer": a or None})

    logger.info("Kaggle adapter extracted %d Q&A pairs", len(pairs))
    return pairs
