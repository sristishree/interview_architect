from fastapi import FastAPI
from api.routes.interview import router as interview_router
from api.routes.sessions import router as sessions_router

app = FastAPI(
    title="Interview Architect API",
    version="1.0.0",
    description="Generate structured interview question sets from a resume.",
)

app.include_router(interview_router)
app.include_router(sessions_router)
