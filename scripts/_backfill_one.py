import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv; load_dotenv(dotenv_path=".env")
from langgraph_sdk import get_client
from app.db import SessionStore
from app.db.models import InterviewSession

THREAD_ID = "019fe00a-1fc1-7200-a0dc-af365999db8f"

async def main():
    store = SessionStore()

    # Check current DB state
    with store._Session() as s:
        row = s.query(InterviewSession).filter_by(thread_id=THREAD_ID).first()
        if row:
            print(f"DB: id={row.id}  interview_set={'present' if row.interview_set_json else 'missing'}  error={row.error}")
        else:
            print("DB: not found")
            row = None

    # Fetch from LangGraph
    client = get_client(url=os.getenv("LANGGRAPH_URL", "http://localhost:2024"))
    state = await client.threads.get_state(THREAD_ID)
    values = state.get("values") or {}
    has_set = bool(values.get("interview_set"))
    candidate = (values.get("candidate_profile") or {}).get("name", "unknown")
    print(f"LangGraph: interview_set={'present' if has_set else 'missing'}  candidate={candidate}  error={values.get('error')}")

    if row and has_set:
        # Row exists but was saved as failed — overwrite it
        with store._Session() as s:
            import json
            existing = s.query(InterviewSession).filter_by(thread_id=THREAD_ID).first()
            interview_set = values["interview_set"]
            existing.interview_set_json = json.dumps(interview_set)
            existing.candidate_name = interview_set.get("candidate_name")
            existing.resolved_difficulty = interview_set.get("resolved_difficulty")
            existing.total_questions = interview_set.get("total_questions")
            existing.estimated_duration_minutes = interview_set.get("estimated_duration_minutes")
            existing.error = None
            if values.get("candidate_profile"):
                existing.candidate_profile_json = json.dumps(values["candidate_profile"])
            if values.get("interview_plan"):
                existing.interview_plan_json = json.dumps(values["interview_plan"])
            s.commit()
            print(f"Updated DB row id={existing.id} — {candidate}")
    elif not row:
        sid = store.save_if_new(THREAD_ID, values)
        print(f"Inserted new DB row id={sid}")
    else:
        print("LangGraph state also has no interview_set — nothing to backfill")

asyncio.run(main())
