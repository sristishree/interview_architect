"""
Agent tests — all marked @pytest.mark.integration since they make LLM calls.
Run with: pytest -m integration tests/test_agents.py
"""
import pytest

from app.models.plan import InterviewPlan
from app.models.resume import CandidateProfile, ParsedResume


@pytest.mark.integration
def test_extractor_returns_candidate_profile(sample_parsed_resume: ParsedResume):
    from app.agents.extractor import extract_profile_node
    state = {"parsed_resume": sample_parsed_resume.model_dump()}
    result = extract_profile_node(state)
    assert "candidate_profile" in result
    profile = CandidateProfile.model_validate(result["candidate_profile"])
    assert profile.name
    assert profile.experience_years > 0
    assert len(profile.core_skills) > 0
    assert profile.seniority in ("Junior", "Mid", "Senior", "Lead", "Principal")
    assert profile.suggested_difficulty in ("Easy", "Medium", "Hard")


@pytest.mark.integration
def test_planner_returns_valid_plan(sample_candidate_profile: CandidateProfile):
    from app.agents.planner import plan_interview_node
    state = {
        "candidate_profile": sample_candidate_profile.model_dump(),
        "difficulty_override": None,
    }
    result = plan_interview_node(state)
    assert "interview_plan" in result
    plan = InterviewPlan.model_validate(result["interview_plan"])
    assert plan.total_questions > 0
    assert len(plan.topic_plans) > 0
    assert plan.resolved_difficulty in ("Easy", "Medium", "Hard")
    total_allocated = sum(tp.n_questions for tp in plan.topic_plans)
    assert abs(total_allocated - plan.total_questions) <= 3


@pytest.mark.integration
def test_planner_respects_difficulty_override(sample_candidate_profile: CandidateProfile):
    from app.agents.planner import plan_interview_node
    state = {
        "candidate_profile": sample_candidate_profile.model_dump(),
        "difficulty_override": "Easy",
    }
    result = plan_interview_node(state)
    plan = InterviewPlan.model_validate(result["interview_plan"])
    assert plan.resolved_difficulty == "Easy"


@pytest.mark.integration
def test_curator_returns_interview_set(sample_candidate_profile, sample_plan):
    from app.knowledge_base.store import QuestionStore
    from app.agents.curator import curate_interview_node

    store = QuestionStore()
    questions = store.search("XGBoost", n=5) + store.search("Python", n=3) + store.search("Leadership", n=3)

    state = {
        "candidate_profile": sample_candidate_profile.model_dump(),
        "interview_plan": sample_plan.model_dump(),
        "retrieved_questions": questions,
    }
    result = curate_interview_node(state)
    assert "interview_set" in result
    interview_set = result["interview_set"]
    assert "sections" in interview_set
    assert len(interview_set["sections"]) > 0
    assert interview_set["total_questions"] > 0
