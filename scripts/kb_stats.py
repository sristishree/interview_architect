"""Distribution of topics, tags, categories, and difficulty in questions.json."""

import json
from collections import Counter
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "questions.json"


def bar(count: int, total: int, width: int = 30) -> str:
    filled = round(count / total * width)
    return "█" * filled + "░" * (width - filled)


def section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def print_table(counter: Counter, total: int, label_width: int = 20) -> None:
    for name, count in counter.most_common():
        pct = count / total * 100
        b = bar(count, total)
        print(f"  {name:<{label_width}} {b}  {count:>3}  ({pct:4.1f}%)")


def main() -> None:
    questions = json.loads(DATA_FILE.read_text())
    n = len(questions)

    topics = Counter(q["topic"] for q in questions)
    tags = Counter(tag for q in questions for tag in q.get("tags", []))
    categories = Counter(q["category"] for q in questions)
    difficulties = Counter(q["difficulty"] for q in questions)
    qtypes = Counter(q.get("question_type", "unknown") for q in questions)

    print(f"\n  Knowledge Base — {n} questions total")

    section("Category")
    print_table(categories, n)

    section("Difficulty")
    print_table(difficulties, n, label_width=10)

    section("Question Type")
    print_table(qtypes, n, label_width=16)

    section("Topic  (top 20)")
    print_table(Counter(dict(topics.most_common(20))), n)

    section("Tag  (top 30)")
    print_table(Counter(dict(tags.most_common(30))), n, label_width=24)

    print()


if __name__ == "__main__":
    main()
