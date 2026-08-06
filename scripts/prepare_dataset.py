"""
Prepare train / test / eval splits from the Mehyaar/Annotated_NER_PDF_Resumes dataset.

Source: data/raw/ResumesJsonAnnotated/  (5,029 annotated JSON files)
Output: data/splits/{train,test,eval}.json

Each output record:
  {
    "id":          int,           # stable index across all splits
    "resume_text": str,           # full resume text
    "skills":      List[str],     # unique skills extracted from NER spans (lowercased, sorted)
    "source_file": str            # original filename for traceability
  }

Split ratios: 70 / 15 / 15  (train / test / eval)
Random seed : 42
"""

import json
import random
from pathlib import Path

RANDOM_SEED = 42
SPLIT_RATIOS = {"train": 0.70, "test": 0.15, "eval": 0.15}

RAW_DIR = Path(__file__).parent.parent / "data" / "raw" / "ResumesJsonAnnotated"
OUT_DIR = Path(__file__).parent.parent / "data" / "splits"


def _extract_skills(text: str, annotations: list) -> list[str]:
    """Extract unique skill strings from character-span annotations."""
    skills: set[str] = set()
    for ann in annotations:
        if not (isinstance(ann, (list, tuple)) and len(ann) == 3):
            continue
        start, end, label = ann
        if not isinstance(label, str) or not label.startswith("SKILL:"):
            continue
        # Use the annotated span text; fall back to the label suffix
        span = text[start:end].strip()
        if span:
            skills.add(span.lower())
        else:
            name = label.split(":", 1)[1].strip()
            if name:
                skills.add(name.lower())
    return sorted(skills)


def _clean(s: str) -> str:
    """Remove surrogate characters that break JSON serialisation."""
    return s.encode("utf-8", errors="ignore").decode("utf-8")


def load_all(raw_dir: Path) -> list[dict]:
    records = []
    for i, path in enumerate(sorted(raw_dir.glob("*.json"))):
        try:
            data = json.loads(path.read_text(errors="replace"))
        except json.JSONDecodeError:
            continue
        text = _clean(data.get("text", "")).strip()
        if not text:
            continue
        skills = _extract_skills(text, data.get("annotations", []))
        records.append({
            "id": i,
            "resume_text": _clean(text),
            "skills": skills,
            "source_file": path.name,
        })
    return records


def split(records: list[dict], ratios: dict, seed: int) -> dict[str, list[dict]]:
    rng = random.Random(seed)
    shuffled = records[:]
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_train = round(n * ratios["train"])
    n_test = round(n * ratios["test"])

    return {
        "train": shuffled[:n_train],
        "test":  shuffled[n_train : n_train + n_test],
        "eval":  shuffled[n_train + n_test :],
    }


def main() -> None:
    print(f"Reading from {RAW_DIR} …")
    records = load_all(RAW_DIR)
    print(f"Loaded {len(records)} valid records")

    splits = split(records, SPLIT_RATIOS, RANDOM_SEED)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in splits.items():
        out = OUT_DIR / f"{name}.json"
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        skill_counts = [len(r["skills"]) for r in data]
        avg_skills = sum(skill_counts) / len(skill_counts) if skill_counts else 0
        print(f"  {name:5s}: {len(data):4d} samples  |  avg {avg_skills:.1f} skills/resume  →  {out}")


if __name__ == "__main__":
    main()
