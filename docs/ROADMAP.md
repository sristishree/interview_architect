# Interview Architect — Roadmap

Decisions that are explicitly deferred from the current deployment milestone, plus larger feature ideas for future phases.

---

## Phase 1 — Launch (current)

See [deployment design spec](superpowers/specs/2026-08-24-deployment-design.md) for full details.

Shipped:
- Remove PaddleOCR, migrate to Neon Postgres, deploy two Render services + Cloudflare Pages
- Admin-only history access via HTTP Basic Auth
- Rate limiting (3 runs/IP/day, 1 concurrent), cold start UX, CORS lockdown

---

## Phase 2 — Post-Launch Improvements

### Multi-Tenant Auth (Option B)

**What:** Replace admin-only HTTP Basic Auth with full user accounts. Any visitor can register, log in, and see only their own session history.

**Why deferred:** Adds significant scope (user table, password hashing or OAuth, JWT, per-user DB scoping). Not needed for a portfolio demo with a single owner.

**When to pick up:** When the app is shared with external users who need private history.

**Integration points:**
- Add `users` table to Neon Postgres
- OAuth providers: Google and/or GitHub (via `authlib` or a managed provider like Clerk/Auth0 on free tier)
- JWT issued by FastAPI, validated per-request
- `user_id` foreign key on `interview_sessions` — all session queries scoped to `current_user.id`
- Frontend: login/register pages, token stored in `localStorage`, sent as `Authorization: Bearer`

---

### BYOK — Bring Your Own Key

**What:** Let users supply their own OpenRouter API key so LLM costs are not borne by the server.

**Why deferred:** Requires multi-tenant auth first (keys must be scoped to a user). Also increases UX complexity.

**Integration point:** LangGraph `RunnableConfig` — `config={"configurable": {"user_api_key": "sk-or-..."}}` — passed through from FastAPI to the graph.

---

### Alembic for Schema Migrations

**What:** Add Alembic to manage Postgres schema changes without dropping and recreating tables.

**Why deferred:** Postgres is greenfield at launch; `Base.metadata.create_all()` is sufficient until the schema needs to evolve post-launch.

---

### Custom Domain

**What:** Replace `interview-architect.pages.dev` and `*.onrender.com` with a proper domain.

**Notes:** Cloudflare Pages custom domain is free. Render custom domain requires the paid plan — could proxy via Cloudflare instead.

---

## Phase 3 — Intelligence Features

### Job Trend Analyser

**What:** A new module that fetches live job descriptions from job portals (Naukri, LinkedIn, etc.), extracts trending skills and requirements for a given role, and surfaces two things:

1. **Trend Dashboard** — show users what skills are currently in demand for a role they care about (e.g. "Senior Backend Engineer in India"). Updated periodically or on-demand.

2. **Resume Gap Analysis** — given a user's uploaded resume and a target role, compare their skill set against the current job market trends and report:
   - Skills they already have that are in demand
   - Skills that are trending but missing from their resume
   - Skills on their resume that are declining in relevance

**Why this is valuable:** Interview Architect already knows the candidate's profile (domains, skills, seniority). Adding market awareness turns it from an interview prep tool into a career intelligence tool.

**High-level architecture:**

```
Job Trend Analyser
├── Scraper / Fetcher
│   ├── LinkedIn Jobs API or scraper
│   ├── Naukri scraper (no official API)
│   └── Optional: Indeed, Glassdoor
│
├── JD Processor (LLM-based)
│   ├── Extract: required skills, preferred skills, tech stack, role level
│   └── Normalize: deduplicate and canonicalize skill names
│
├── Trend Store (Postgres)
│   ├── raw_job_postings (role, location, source, fetched_at, raw_text)
│   └── skill_trends (role, skill, mention_count, period, updated_at)
│
├── Trend API (FastAPI routes)
│   ├── GET /trends?role=...&location=... → top skills + counts
│   └── POST /trends/gap-analysis (resume profile + role → gap report)
│
└── Frontend
    ├── Trend Dashboard page — bar/bubble chart of in-demand skills
    └── Gap Analysis panel — shown alongside or after interview generation
```

**Dependencies / blockers:**
- Naukri has no public API — scraping requires rate limiting, anti-bot handling, and may break on site changes. LinkedIn has a public job search API but is rate-limited; scraping violates ToS. Start with what's feasible (e.g. a curated set via their respective APIs or partner access) and expand.
- LLM cost per JD extraction: one fast-model call per JD. Need to batch and cache aggressively.
- Scheduling: scraping runs on a cron schedule (daily or weekly), not per user request.
- Multi-tenant auth (Phase 2) is a prerequisite if gap analysis results are to be persisted per user.

**Open questions to resolve before building:**
- Which portals are in scope at v1? (Recommendation: start with LinkedIn Jobs API only — has official access.)
- How fresh does trend data need to be? Daily vs. weekly vs. on-demand.
- Is the trend dashboard public (no login) or gated?
- Role taxonomy: free-text input or a predefined list of roles?

---

## Phase 4 — Scale & Monetisation (if needed)

- Upgrade Render to paid tier to eliminate cold starts
- Upgrade Neon to paid tier for more connections and storage
- Stripe integration for usage-based billing (per-run or subscription)
- BYOK as a free-tier gate (server key for paid users, own key for free)
