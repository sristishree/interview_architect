"""
Agent tests — all marked @pytest.mark.integration since they make LLM calls.
Run with: pytest -m integration tests/test_agents.py
"""
import pytest

from app.models.plan import InterviewPlan
from app.models.resume import CandidateProfile


@pytest.mark.integration
def test_build_profile_returns_candidate_profile(tmp_path):
    """build_profile_node produces a valid CandidateProfile from raw resume text."""
    from app.agents.profile_builder import build_profile_node

    resume_text = """
John Smith
Senior Data Scientist | 5 years experience

Skills: Python, SQL, XGBoost, scikit-learn, AWS

Work Experience:
Acme Corp — Senior Data Scientist (2021–present, 3yr)
- Built credit scoring model using XGBoost serving 200K daily predictions
- Reduced model training time by 35% through feature store implementation
- Led team of 3 junior data scientists

StartupXYZ — Data Scientist (2019–2021, 2yr)
- Developed NLP pipeline for document classification
- Designed A/B testing framework for model evaluation

Projects:
Credit Scoring Pipeline
Stack: XGBoost, Airflow, Python, AWS S3
- End-to-end ML pipeline for credit risk assessment
- 89% AUC on held-out test set
"""

    state = {"raw_text": resume_text}
    result = build_profile_node(state)

    assert "candidate_profile" in result
    profile = CandidateProfile.model_validate(result["candidate_profile"])
    assert profile.is_resume is True
    assert profile.name
    assert profile.years_of_experience > 0
    assert len(profile.key_skills) > 0
    assert len(profile.work_experiences) > 0
    assert profile.seniority in ("Junior", "Mid", "Senior", "Lead", "Principal")
    assert profile.suggested_difficulty in ("Easy", "Medium", "Hard")
    # responsibilities should be extracted verbatim
    all_responsibilities = [r for w in profile.work_experiences for r in w.responsibilities]
    assert len(all_responsibilities) > 0


@pytest.mark.integration
def test_build_profile_rejects_non_resume(tmp_path):
    """build_profile_node sets is_resume=False for non-resume documents."""
    from app.agents.profile_builder import build_profile_node

    state = {"raw_text": "Invoice #1234\nBill To: Acme Corp\nAmount Due: $500"}
    result = build_profile_node(state)
    profile = CandidateProfile.model_validate(result["candidate_profile"])
    assert profile.is_resume is False


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
    # should have at least one experience-sourced topic
    sources = [tp.source for tp in plan.topic_plans]
    assert "experience" in sources


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
