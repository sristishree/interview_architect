"""
Deduplication via local sentence-transformers embeddings.

Compares candidates against the existing KB within the same category subset.
Also deduplicates new candidates against each other.

No vector database needed — all embeddings fit in memory at this scale.
"""
import logging
from collections import defaultdict
from typing import List, Tuple

import numpy as np

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_THRESHOLD = 0.85


def dedup_candidates(
    candidates: List[dict],
    existing: List[dict],
    threshold: float = DEFAULT_THRESHOLD,
) -> Tuple[List[dict], int]:
    """
    Filter out candidates too similar to existing KB questions or to each other.

    Returns (accepted, n_dropped).
    Similarity is cosine within same-category subsets.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError(
            "sentence-transformers is required for dedup. "
            "Run: pip install sentence-transformers"
        )

    if not candidates:
        return [], 0

    logger.info("Loading embedding model %s …", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)

    # Build per-category existing embeddings (only for categories we actually need)
    needed_cats = {c.get("category", "") for c in candidates}
    existing_by_cat: dict[str, list[str]] = defaultdict(list)
    for q in existing:
        cat = q.get("category", "")
        if cat in needed_cats:
            existing_by_cat[cat].append(q["question"])

    existing_embeddings: dict[str, np.ndarray] = {}
    for cat, texts in existing_by_cat.items():
        existing_embeddings[cat] = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    accepted: List[dict] = []
    accepted_embeddings_by_cat: dict[str, list[np.ndarray]] = defaultdict(list)
    n_dropped = 0

    for cand in candidates:
        cat = cand.get("category", "")
        emb = model.encode([cand["question"]], normalize_embeddings=True, show_progress_bar=False)[0]

        # Check against existing KB in same category
        if cat in existing_embeddings and existing_embeddings[cat].shape[0] > 0:
            sims = existing_embeddings[cat] @ emb
            if float(sims.max()) >= threshold:
                logger.debug("Dropping duplicate (vs existing): %s", cand["question"][:80])
                n_dropped += 1
                continue

        # Check against already-accepted candidates in same category
        if accepted_embeddings_by_cat[cat]:
            acc_matrix = np.array(accepted_embeddings_by_cat[cat])
            sims = acc_matrix @ emb
            if float(sims.max()) >= threshold:
                logger.debug("Dropping duplicate (vs staged): %s", cand["question"][:80])
                n_dropped += 1
                continue

        accepted.append(cand)
        accepted_embeddings_by_cat[cat].append(emb)

    return accepted, n_dropped
