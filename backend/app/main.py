"""
RegShift FastAPI application — main entry point.
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.models import *  # ensure all models are registered
from app.routers import documents, analysis, impact, tickets, audit, demo, overview

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and upload directory on startup."""
    logger.info("RegShift backend starting up...")
    os.makedirs(settings.upload_dir, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")
    logger.info(f"Upload directory: {os.path.abspath(settings.upload_dir)}")
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        logger.warning(
            "No OpenAI API key configured. AI extraction will run in demo mode. "
            "Set OPENAI_API_KEY in backend/.env to enable real AI analysis."
        )
    yield
    logger.info("RegShift backend shutting down.")


app = FastAPI(
    title="RegShift API",
    description="Insurance regulatory intelligence platform. Transforms regulatory bulletins into evidence-backed implementation plans.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — narrowly configured for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(impact.router)
app.include_router(tickets.router)
app.include_router(audit.router)
app.include_router(demo.router)
app.include_router(overview.router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "regshift-api",
        "version": "1.0.0",
        "llm_configured": bool(settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here"),
    }


@app.get("/")
def root():
    return {
        "message": "RegShift API",
        "docs": "/docs",
        "health": "/health",
    }
