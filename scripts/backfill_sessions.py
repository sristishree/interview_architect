"""
Backfill sessions from LangGraph into the local DB.

Fetches all threads from the LangGraph server, checks which ones are missing
from the DB, and saves them. Useful after bugs that prevented saving on stream end.

Usage:
    python scripts/backfill_sessions.py
    python scripts/backfill_sessions.py --limit 20   # only check most recent N threads
"""

import asyncio
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from langgraph_sdk import get_client
from app.db import SessionStore


LANGGRAPH_URL = os.getenv("LANGGRAPH_URL", "http://localhost:2024")
ASSISTANT_ID = "interview_architect"


async def backfill(limit: int):
    client = get_client(url=LANGGRAPH_URL)
    store = SessionStore()

    print(f"Fetching threads from {LANGGRAPH_URL} (limit={limit})...")
    threads = await client.threads.search(limit=limit)
    print(f"Found {len(threads)} threads.")

    saved = 0
    skipped = 0

    for thread in threads:
        thread_id = thread["thread_id"]

        try:
            state = await client.threads.get_state(thread_id)
            values = state.get("values") or {}
        except Exception as e:
            print(f"  [{thread_id[:8]}] Could not fetch state: {e}")
            continue

        if not values.get("resume_path"):
            skipped += 1
            continue

        result = store.save_if_new(thread_id, values)
        if result is None:
            skipped += 1
            print(f"  [{thread_id[:8]}] Already in DB — skipped")
        else:
            saved += 1
            name = (values.get("candidate_profile") or {}).get("name") or "unknown"
            interview_set = values.get("interview_set")
            status = "ok" if interview_set else f"failed: {values.get('error', 'no interview set')}"
            print(f"  [{thread_id[:8]}] Saved (id={result}) — {name} — {status}")

    print(f"\nDone. Saved: {saved}, Skipped: {skipped}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50, help="Max threads to check")
    args = parser.parse_args()
    asyncio.run(backfill(args.limit))
