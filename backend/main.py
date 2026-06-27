from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from db.database import init_db
from api.auth import router as auth_router
from api.projects import router as projects_router
from api.reports import router as reports_router
from api.profile import router as profile_router
from api.prompt_agent_api import router as prompt_agent_router
from api.social import router as social_router
from api.analytics import router as analytics_router
from api.notifications import router as notifications_router
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SEO Growth AI Agent",
    description="Autonomous SEO assistant powered by LangGraph and Groq",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(reports_router)
app.include_router(profile_router)
app.include_router(prompt_agent_router)
app.include_router(social_router)
app.include_router(analytics_router)
app.include_router(notifications_router)


@app.get("/")
def root():
    return {"message": "SEO Growth AI Agent API", "status": "running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
