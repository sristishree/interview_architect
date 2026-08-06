# Interview Architect

A multi-agent LangGraph pipeline that reads a resume and produces a structured, interviewer-ready question set. Each run is fully traced in LangSmith.

## How it works

```
parse_resume → extract_profile → plan_interview → retrieve_questions → curate_interview
                                                         ↑                     │
                                                         └── shortfall > 0 ────┘
```

| Node | Role |
|---|---|
| **parse_resume** | Extracts raw fields from PDF / DOCX / TXT (no inference) |
| **extract_profile** | Enriches into a `CandidateProfile` — seniority, domains, key skills, interview focus |
| **plan_interview** | Allocates questions per topic; ~60% sourced from actual resume projects |
| **retrieve_questions** | Deterministic node — calls KB tools per topic plan |
| **curate_interview** | Deduplicates, orders, and structures the final set; loops back if shortfall > 0 |

## Setup

```bash
pyenv virtualenv 3.11.5 venv_3.11.5_interview_architect
pyenv local venv_3.11.5_interview_architect
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your keys:

```bash
# LiteLLM proxy
LITELLM_BASE_URL=https://your-litellm-host/
LITELLM_API_KEY=your_key
LITELLM_MODEL=gemini-2.5-flash
LITELLM_MODEL_FAST=gemini-2.5-flash

# LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=interview-architect
LANGSMITH_API_KEY=your_langsmith_key

# Web search fallback (optional)
TAVILY_API_KEY=your_tavily_key
```

## Run

Edit the bottom of `main.py` and run:

```python
if __name__ == "__main__":
    run(
        resume_path="data/sample_resumes/sample_resume.txt",
        difficulty=None,       # None = auto, or "Easy" / "Medium" / "Hard"
        output_json=None,      # set to "output.json" to save
    )
```

```bash
python main.py
```

## Knowledge base

121 seed questions in `data/questions.json` across 8 categories (ML, Python, SQL, SystemDesign, LLM, Cloud, Leadership, General) with equal difficulty distribution (~30 each). The skill tool automatically falls back to Tavily web search when KB results are sparse, and persists the generated questions back to the KB.

```bash
python scripts/kb_stats.py          # distribution of topics, tags, difficulty
```

## Dataset

Train / test / eval splits prepared from [Mehyaar/Annotated_NER_PDF_Resumes](https://huggingface.co/datasets/Mehyaar/Annotated_NER_PDF_Resumes) (4,982 annotated resumes):

| Split | Samples |
|---|---|
| train | 3,487 |
| test | 747 |
| eval | 748 |

```bash
python scripts/prepare_dataset.py   # regenerate splits from data/raw/
```

## Tests

```bash
pytest                              # unit tests (no API calls)
pytest -m integration               # requires real keys in .env
```

## Project structure

```
app/
  agents/        parser, extractor, planner, curator
  graph/         state.py, workflow.py
  models/        enums, question, resume, plan
  tools/         skill_tool, project_tool, experience_tool, web_search_tool
  knowledge_base/ store.py (fuzzy search + persist)
data/
  questions.json          KB seed questions
  splits/                 train / test / eval (gitignored)
  raw/                    downloaded dataset (gitignored)
scripts/
  kb_stats.py             KB distribution
  prepare_dataset.py      HuggingFace → splits
  seed_easy_questions.py  one-off KB seeding
```
