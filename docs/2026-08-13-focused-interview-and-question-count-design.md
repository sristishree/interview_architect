# Focused Interview Mode & Question Count Control — Design Spec

**Date:** 2026-08-13
**Status:** Approved (produced via grill-me session; supersedes `2026-08-13-focused-interview-mode-design.md`)

---

## Overview

Add a **Focused Interview** mode alongside the existing Full Interview mode. Users can direct the system to generate a targeted set of questions for a specific resume section, with a question-type filter, a custom question count, and an optional free-text modifier.

Additionally, **both modes** now expose a user-adjustable question-count control, backed by a deterministic formula (already implemented in `planner.py`) instead of the old flat seniority lookup.

---

## User Flow

1. User uploads resume and sees a **mode toggle**: "Full Interview" / "Focused Interview"
2. **Full Interview** now also shows a question-count field:
   - Optional, min 5 / max 30
   - Displayed as **"Let the expert decide"** (empty/auto placeholder) — no static number is pre-filled, since the real default can't be known until the resume is parsed
   - If left untouched, the backend computes it via the deterministic formula in `planner.py` (seniority base + skill/project/experience bonuses, capped at 30)
   - If the user enters a value, it overrides the formula entirely — same override pattern as the existing `difficulty_override`
3. Selecting **"Focused Interview"** reveals additional fields:
   - **Section** (dropdown, required): Work Experience · Projects · Skills — *only these three; Education/Certifications/Summary are dropped since `CandidateProfile` never extracts them and no retrieval tool exists for them*
   - **Question type filter** (multi-select, optional): design · implementation · theory · optimization · behavioral · case_study — hard-enforced (see Graph Changes)
   - **Modifier** (text input, optional): e.g. "focus on system design aspects" — soft prompt steer only, same mechanism as `difficulty_override`, no enforcement guarantee
   - **Question count** (number input, required): min 5, max 30, default 10
   - Section and type filter are independent, composable axes — e.g. Section=Projects + Type=[design, implementation] means "questions about my projects, styled as design/implementation"
4. User submits — generation proceeds via SSE stream as today
5. **Fallback behaviors** (both surfaced via the same dismissible-banner SSE mechanism):
   - **Section not found**: if the selected section has no content in the extracted profile, silently fall back to Full Interview mode and show: *"Selected section not found in resume — generated full interview instead."*
   - **Count shortfall**: if the retrieval retry loop still can't reach the requested count (thin section and/or narrow type filter), serve what was generated and show: *"Could only generate N of M requested questions."*

---

## Data Models

**New file: `app/models/focus.py`**

```python
class InterviewMode(str, Enum):
    FULL = "full"
    FOCUSED = "focused"

class ResumeSection(str, Enum):
    WORK_EXPERIENCE = "work_experience"
    PROJECTS = "projects"
    SKILLS = "skills"

class FocusConfig(BaseModel):
    section: ResumeSection
    question_types: list[QuestionType] | None = None   # optional multi-select filter
    modifier: str | None = None                         # optional free-text soft steer
    question_count: int = Field(default=10, ge=5, le=30)
```

**Updated: `app/graph/state.py`**

Add to `InterviewState`:
- `focus_config: FocusConfig | None` — populated from the API request; `None` means full mode
- `interview_mode: InterviewMode` — resolved by `validate_focus_node`; defaults to `FULL`
- `question_count_override: Optional[int]` — full-mode-only override (min 5 / max 30); when set, bypasses `_compute_question_count()` in the planner

---

## Graph Changes

**Updated pipeline:**
```
extract_text → build_profile → validate_focus → plan_interview → retrieve_questions → curate_interview
```

### New node: `validate_focus_node`

Pure deterministic logic — no LLM call. Sits between `build_profile` and `plan_interview`.

Responsibilities:
- If `focus_config` is `None`: set `interview_mode = FULL`, pass through
- If `focus_config` is set: check whether the requested section has content in the extracted profile
  - Section present → set `interview_mode = FOCUSED`
  - Section absent → set `interview_mode = FULL`, clear `focus_config`, set a `fallback_notice` flag in state

Section-to-profile mapping (presence check = non-empty list):
| `ResumeSection` | Profile field checked |
|---|---|
| `work_experience` | `profile.work_experiences` |
| `projects` | `profile.projects` |
| `skills` | `profile.skills` |

### Modified: `plan_interview_node` (`app/agents/planner.py`)

**Question count:**
- `FULL`: use `question_count_override` if provided, else `_compute_question_count(profile)` — the existing deterministic formula (already implemented):
  `base(seniority: 8–16) + skill_bonus(≤5) + project_bonus(≤8) + experience_bonus(≤6)`, capped at 30.
  *Gap to close during implementation: the node currently always calls `_compute_question_count()` — it never reads an override from state. Needs a branch to check `state.get("question_count_override")` first.*
- `FOCUSED`: use `focus_config.question_count` exactly, as today's doc already specified.

**Section allocation (`FOCUSED` only):**
- Allocate 100% of `total_questions` to the specified `focus_config.section`'s source (`project` / `experience` / `skill`)
- Incorporate `focus_config.modifier` as a thematic constraint in the prompt if present

**Type filter (`FOCUSED` only, when `focus_config.question_types` is set):**
- Constrain every `TopicPlan.question_types` breakdown to only the allowed types
- Pass the allowed type set down to the retrieval tools (see below) for hard enforcement, not just prompt guidance

### Modified: `retrieve_questions_node` (`app/graph/workflow.py`)

Passes `focus_config.question_types` (if set) through to whichever tool it calls, so filtering happens at the source rather than being a planner-only hint.

### Modified: `app/knowledge_base/store.py`

`QuestionStore.search()` gains a `question_type: Optional[QuestionType]` (or list) filter parameter, alongside the existing `difficulty` and `category` filters. The `question_type` field already exists on stored questions (`app/models/question.py`) — it's just not filtered on today.

### Modified: `app/tools/skill_tool.py`, `project_tool.py`, `experience_tool.py`

Each tool (`get_skill_questions`, `get_project_questions`, `get_experience_questions`) gains a `question_type` parameter:
- Passed into the KB `_store.search()` call
- Passed into the LLM-generation prompt so generated questions are also constrained to the allowed type(s)

### Modified: `curate_interview_node`

Safety net: if any retrieved question's type doesn't match the active filter (e.g. an LLM ignored the constraint), drop it and count the drop toward `shortfall`, which feeds the existing retry loop (`_MAX_RETRIEVAL_ATTEMPTS = 2` in `workflow.py`). If shortfall remains after max retries, surface the count-shortfall notice.

---

## API Changes

**`api/schemas.py`** — add to the generate request:

```python
class GenerateRequest(BaseModel):
    # existing fields unchanged
    focus_config: FocusConfig | None = None
    question_count_override: int | None = None   # Full mode only, ge=5, le=30
```

Backward-compatible — existing clients omit both fields and get today's full-interview behavior.

**`api/routes/interview.py`** — pass `focus_config` and `question_count_override` into the initial graph state (`_graph_input`).

**SSE stream** — add a `fallback_notice` event type (used for both the section-not-found fallback and the count-shortfall notice) so the frontend can surface the banner.

**`app/db/store.py`** — store `interview_mode` and `focus_config` alongside each session so the History tab can display context.

---

## UI Changes

### Generate form

- Mode toggle above the submit button: "Full Interview" (default) / "Focused Interview"
- **Full Interview**: question-count field, optional, min 5/max 30, shown as "Let the expert decide" until the user types a value
- **Focused Interview** reveals:
  - Section dropdown (required): Work Experience · Projects · Skills
  - Question type filter (multi-select, optional)
  - Modifier text input (optional, placeholder: "e.g. focus on system design aspects")
  - Question count number input (required, min 5, max 30, default 10)
- On submit, `focus_config` (focused mode) or `question_count_override` (full mode, if set) is included in the request body

### History tab

Each session row shows a mode badge:
- Full mode: `Full · 18 Qs`
- Focused mode: `Focused: Projects · design+implementation · 20 Qs`

### Fallback / shortfall banner

Dismissible inline banner shown when a `fallback_notice` event is received in the SSE stream:
- Section not found: *"Selected section not found in resume — generated full interview instead."*
- Count shortfall: *"Could only generate N of M requested questions."*

---

## Files Touched

| File | Change |
|---|---|
| `app/models/focus.py` | New — `FocusConfig` (section, question_types filter, modifier, question_count), `InterviewMode`, `ResumeSection` (3 values) |
| `app/graph/state.py` | Add `focus_config`, `interview_mode`, `question_count_override` |
| `app/graph/workflow.py` | Insert `validate_focus_node`; `retrieve_questions_node` passes `question_types` filter through to tools |
| `app/agents/validate_focus.py` | New — deterministic section-presence check |
| `app/agents/planner.py` | Read `question_count_override` (currently missing) before falling back to `_compute_question_count()`; focused-mode branch: force 100% allocation to one source, constrain `question_types` to the filter set if present |
| `app/agents/curator.py` | Drop type-mismatched questions, report as shortfall |
| `app/knowledge_base/store.py` | `search()` gains `question_type` filter |
| `app/tools/skill_tool.py`, `project_tool.py`, `experience_tool.py` | Accept and honor `question_type` param, both in KB search and LLM-generation prompt |
| `api/schemas.py` | Add `focus_config`, `question_count_override` to generate request schema |
| `api/routes/interview.py` | Pass both into graph state |
| `app/db/store.py` | Persist `interview_mode`/`focus_config` per session |
| `frontend/src/` | Mode toggle, full-mode count field ("Let the expert decide"), section dropdown, type multi-select, modifier input, focused-mode count input, History badge, fallback/shortfall banner |

---

## Known Risks

- **KB type-tagging quality**: many of the 76 seeded KB questions likely default to `question_type = theory` (the model default) since seeding probably didn't backfill it accurately. A hard type filter may starve KB hits and lean heavily on LLM generation until the KB is re-tagged.

---

## Out of Scope

- Dynamic section detection (populating the dropdown from the parsed resume) — deferred; fixed options + fallback covers the use case
- Per-section question count breakdown (e.g. 5 from projects + 3 from skills) — single section only in this version
- Saving focus preferences across sessions
- Two-phase upload flow (extract-then-confirm-count) — full mode's count field stays a blind override on top of today's single-shot request/response flow
