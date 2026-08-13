"""
Recover a specific run from LangSmith and backfill it into the local DB.
The root run output in LangSmith contains the final graph state.

Usage:
    python scripts/_backfill_from_langsmith.py <run_id>
"""

import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv; load_dotenv(dotenv_path=".env")

from langsmith import Client
from app.db import SessionStore
from app.db.models import InterviewSession


def backfill(run_id: str):
    ls = Client()

    print(f"Fetching run {run_id} from LangSmith...")
    run = ls.read_run(run_id)

    print(f"  name={run.name}  status={run.status}")

    outputs = run.outputs or {}
    interview_set = outputs.get("interview_set")
    candidate_profile = outputs.get("candidate_profile")
    interview_plan = outputs.get("interview_plan")
    error = outputs.get("error")

    if not interview_set:
        print("  No interview_set in run outputs — cannot backfill result")
        return

    # Use the LangSmith run id as the thread_id key (no LangGraph thread available)
    thread_id = str(run.id)

    store = SessionStore()
    with store._Session() as s:
        existing = s.query(InterviewSession).filter_by(thread_id=thread_id).first()

    if existing:
        print(f"  Already in DB as id={existing.id} — updating...")
        with store._Session() as s:
            row = s.query(InterviewSession).filter_by(thread_id=thread_id).first()
            row.interview_set_json = json.dumps(interview_set)
            row.candidate_name = interview_set.get("candidate_name")
            row.resolved_difficulty = interview_set.get("resolved_difficulty")
            row.total_questions = interview_set.get("total_questions")
            row.estimated_duration_minutes = interview_set.get("estimated_duration_minutes")
            row.error = None
            if candidate_profile:
                row.candidate_profile_json = json.dumps(candidate_profile)
            if interview_plan:
                row.interview_plan_json = json.dumps(interview_plan)
            s.commit()
            print(f"  Updated row id={row.id} — {interview_set.get('candidate_name')}")
    else:
        state = {
            "interview_set": interview_set,
            "candidate_profile": candidate_profile,
            "interview_plan": interview_plan,
            "error": error,
            "resume_path": (run.inputs or {}).get("resume_path", ""),
        }
        sid = store.save(state, thread_id=thread_id)
        print(f"  Inserted new row id={sid} — {interview_set.get('candidate_name')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    args = parser.parse_args()
    backfill(args.run_id)
