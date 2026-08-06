import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def run(resume_path: str, difficulty: str | None = None, output_json: str | None = None):
    if not os.getenv("LITELLM_API_KEY"):
        sys.exit("Error: LITELLM_API_KEY is not set. Add it to your .env file.")
    if not os.path.exists(resume_path):
        sys.exit(f"Error: resume file not found — {resume_path}")

    from app.graph.workflow import build_graph

    print(f"\nProcessing resume: {resume_path}")
    if difficulty:
        print(f"Difficulty override: {difficulty}")
    print("Running interview architect pipeline…\n")

    resume_name = os.path.splitext(os.path.basename(resume_path))[0]
    graph = build_graph()
    result = graph.invoke(
        {
            "resume_path": resume_path,
            "difficulty_override": difficulty,
            "parsed_resume": None,
            "candidate_profile": None,
            "interview_plan": None,
            "retrieved_questions": [],
            "retrieval_attempts": 0,
            "interview_set": None,
            "shortfall": 0,
            "error": None,
        },
        config={
            "run_name": f"interview-architect/{resume_name}",
            "metadata": {
                "resume": resume_path,
                "difficulty_override": difficulty or "auto",
            },
        },
    )

    if result.get("error"):
        sys.exit(f"Pipeline error: {result['error']}")

    from app.db import SessionStore
    session_id = SessionStore().save(result)
    print(f"Session saved (id={session_id})")

    interview_set = result["interview_set"]
    _print_interview(interview_set)

    if output_json:
        with open(output_json, "w") as f:
            json.dump(interview_set, f, indent=2)
        print(f"Saved to {output_json}")


def _print_interview(interview_set: dict):
    print("\n" + "=" * 70)
    print(f"  INTERVIEW SET — {interview_set['candidate_name'].upper()}")
    print(f"  Difficulty: {interview_set['resolved_difficulty']}  |  "
          f"Questions: {interview_set['total_questions']}  |  "
          f"~{interview_set['estimated_duration_minutes']} min")
    print("=" * 70)

    for section in interview_set["sections"]:
        print(f"\n── {section['name'].upper()} ──")
        for i, q in enumerate(section["questions"], 1):
            print(f"\n  {i}. [{q['difficulty']} / {q['question_type']}]")
            print(f"     {q['question']}")
            if q.get("follow_up"):
                print(f"     ↳  {q['follow_up']}")

    print(f"\n── CURATOR NOTES ──")
    print(f"  {interview_set['curator_notes']}")
    print()


if __name__ == "__main__":
    run(
        resume_path="data/sample_resumes/sample_resume.txt",
        difficulty=None,          # auto-inferred from experience years
        output_json=None,         # set to a path like "output.json" to save
    )
