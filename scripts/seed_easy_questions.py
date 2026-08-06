"""Add Easy questions to balance difficulty distribution to ~30 per tier."""

import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "questions.json"

NEW_QUESTIONS = [
    # ML +2
    {
        "topic": "Machine Learning",
        "difficulty": "Easy",
        "category": "ML",
        "tags": ["confusion matrix", "classification", "evaluation"],
        "question": "What is a confusion matrix? Explain what true positives, false positives, true negatives, and false negatives mean.",
        "follow_up": "How would you derive precision and recall from a confusion matrix?",
        "question_type": "theory",
    },
    {
        "topic": "Machine Learning",
        "difficulty": "Easy",
        "category": "ML",
        "tags": ["classification", "regression", "supervised learning"],
        "question": "What is the difference between classification and regression? Give a real-world example of each.",
        "follow_up": "What type of output does each produce, and how does that affect the loss function you choose?",
        "question_type": "theory",
    },
    # SQL +2
    {
        "topic": "SQL",
        "difficulty": "Easy",
        "category": "SQL",
        "tags": ["DELETE", "TRUNCATE", "DROP", "DDL", "DML"],
        "question": "What is the difference between DELETE, TRUNCATE, and DROP in SQL?",
        "follow_up": "Which of these can be rolled back in a transaction, and why?",
        "question_type": "theory",
    },
    {
        "topic": "SQL",
        "difficulty": "Easy",
        "category": "SQL",
        "tags": ["subquery", "nested query", "filtering"],
        "question": "What is a subquery in SQL and when would you use one instead of a JOIN?",
        "follow_up": "What is a correlated subquery and how does it differ from a regular subquery?",
        "question_type": "implementation",
    },
    # LLM +2
    {
        "topic": "LLM",
        "difficulty": "Easy",
        "category": "LLM",
        "tags": ["tokenization", "tokens", "context window"],
        "question": "What is tokenization in the context of LLMs and how does it affect what you can send to a model?",
        "follow_up": "Why might the same text have a different token count depending on the model?",
        "question_type": "theory",
    },
    {
        "topic": "LLM",
        "difficulty": "Easy",
        "category": "LLM",
        "tags": ["temperature", "sampling", "inference", "randomness"],
        "question": "What does the temperature parameter control in LLM inference? What happens at temperature 0 vs a high value like 1.5?",
        "follow_up": "When would you want a low temperature and when would you want a high one?",
        "question_type": "theory",
    },
    # SystemDesign +2
    {
        "topic": "System Design",
        "difficulty": "Easy",
        "category": "SystemDesign",
        "tags": ["monolith", "microservices", "architecture"],
        "question": "What is the difference between a monolithic and a microservices architecture? What are the trade-offs of each?",
        "follow_up": "At what point would you consider breaking a monolith into microservices?",
        "question_type": "design",
    },
    {
        "topic": "System Design",
        "difficulty": "Easy",
        "category": "SystemDesign",
        "tags": ["REST", "API", "HTTP", "stateless"],
        "question": "What is a REST API and what constraints make an API RESTful?",
        "follow_up": "How does REST differ from GraphQL, and when might you prefer one over the other?",
        "question_type": "theory",
    },
    # General +2
    {
        "topic": "General",
        "difficulty": "Easy",
        "category": "General",
        "tags": ["SQL", "NoSQL", "databases", "storage"],
        "question": "What is the difference between a relational (SQL) and a non-relational (NoSQL) database? When would you choose each?",
        "follow_up": "Give a concrete example of a use case where a document store like MongoDB would outperform PostgreSQL.",
        "question_type": "theory",
    },
    {
        "topic": "General",
        "difficulty": "Easy",
        "category": "General",
        "tags": ["git", "version control", "reproducibility"],
        "question": "What is version control and why is it important in a data science or ML project?",
        "follow_up": "How would you handle large binary files like trained model artifacts in git?",
        "question_type": "theory",
    },
    # Python +1
    {
        "topic": "Python",
        "difficulty": "Easy",
        "category": "Python",
        "tags": ["list", "tuple", "immutability", "data structures"],
        "question": "What is the difference between a list and a tuple in Python? When would you choose one over the other?",
        "follow_up": "Can a tuple contain mutable objects? What are the implications?",
        "question_type": "theory",
    },
    # Leadership +1
    {
        "topic": "Leadership",
        "difficulty": "Easy",
        "category": "Leadership",
        "tags": ["conflict resolution", "collaboration", "communication"],
        "question": "Describe a time you disagreed with a teammate or manager about a technical decision. How did you handle it?",
        "follow_up": "What would you do differently if you had to make the same decision today?",
        "question_type": "behavioral",
    },
    # Cloud +1
    {
        "topic": "Cloud",
        "difficulty": "Easy",
        "category": "Cloud",
        "tags": ["IaaS", "PaaS", "SaaS", "cloud models"],
        "question": "What is the difference between IaaS, PaaS, and SaaS? Give an ML-relevant example of each.",
        "follow_up": "Where would a managed training service like SageMaker or Vertex AI sit in this taxonomy?",
        "question_type": "theory",
    },
]


def main() -> None:
    questions = json.loads(DATA_FILE.read_text())
    next_id = max(q["id"] for q in questions) + 1

    added = 0
    for q in NEW_QUESTIONS:
        q["id"] = next_id
        questions.append(q)
        next_id += 1
        added += 1

    DATA_FILE.write_text(json.dumps(questions, indent=2))
    print(f"Added {added} questions. Total: {len(questions)}")

    from collections import Counter
    diff = Counter(q["difficulty"] for q in questions)
    for d in ["Easy", "Medium", "Hard"]:
        print(f"  {d}: {diff[d]}")


if __name__ == "__main__":
    main()
