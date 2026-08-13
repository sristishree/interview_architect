import pytest

from app.knowledge_base.store import QuestionStore
from app.models.plan import InterviewPlan, TopicPlan
from app.models.enums import Category, Difficulty, QuestionType
from app.models.question import InterviewSection, InterviewSet, Question
from app.models.resume import CandidateProfile, WorkExperience, Project


@pytest.fixture
def store() -> QuestionStore:
    return QuestionStore()


@pytest.fixture
def sample_candidate_profile() -> CandidateProfile:
    return CandidateProfile(
        is_resume=True,
        name="Aditya Sharma",
        role="Lead Data Scientist",
        years_of_experience=6.0,
        skills=["Python", "SQL", "XGBoost", "LangChain", "Docker", "AWS"],
        projects=[
            Project(
                title="Address Matching System",
                description="NLP-based fuzzy address deduplication across 100M records",
                tech_stack=["Python", "sentence-transformers", "AWS Lambda"],
                details=["96% precision", "50ms P95 latency", "500 RPS"],
            ),
            Project(
                title="Document Intelligence Platform",
                description="LLM extraction pipeline for financial documents",
                tech_stack=["LangChain", "OpenAI", "FAISS", "FastAPI"],
                details=["2M+ documents/month", "60% reduction in manual review"],
            ),
        ],
        work_experiences=[
            WorkExperience(
                name="Perfios",
                role="Lead Data Scientist",
                duration_years=3.0,
                responsibilities=[
                    "Led ML pipeline redesign for credit scoring serving 500K daily applications",
                    "Built feature store using Feast reducing training latency by 40%",
                    "Managed team of 4 ML engineers",
                ],
            ),
            WorkExperience(
                name="Fractal Analytics",
                role="Data Scientist",
                duration_years=2.0,
                responsibilities=[
                    "Built XGBoost models for churn prediction achieving 87% AUC",
                    "Designed A/B testing framework for model evaluation",
                ],
            ),
        ],
        seniority="Lead",
        domains=["ML Engineering", "LLMs", "Backend"],
        key_skills=["XGBoost", "Python", "LangChain", "SQL"],
        project_themes=["Production NLP", "LLM Pipelines", "Credit Risk ML"],
        interview_focus=["XGBoost", "LLM system design", "System Design", "SQL", "Leadership"],
        suggested_difficulty="Hard",
    )


@pytest.fixture
def sample_plan() -> InterviewPlan:
    return InterviewPlan(
        total_questions=18,
        resolved_difficulty="Hard",
        reasoning="Lead DS with 6yr experience — focus on depth in ML and LLMs.",
        topic_plans=[
            TopicPlan(topic="XGBoost", source="skill", n_questions=3, difficulty="Hard",
                      question_types={"implementation": 2, "theory": 1}),
            TopicPlan(topic="Python", source="skill", n_questions=2, difficulty="Hard",
                      question_types={"implementation": 1, "theory": 1}),
            TopicPlan(topic="Address Matching System", source="project", n_questions=3, difficulty="Hard",
                      question_types={"design": 1, "implementation": 2}),
            TopicPlan(topic="Leadership", source="leadership", n_questions=2, difficulty="Hard",
                      question_types={"behavioral": 2}),
        ],
    )
