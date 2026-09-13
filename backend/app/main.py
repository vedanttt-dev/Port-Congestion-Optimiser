"""FastAPI application entry point.

Run locally from ``backend/``::

    .venv\\Scripts\\python -m uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import api_router

app = FastAPI(
    title=settings.app_name,
    description=(
        "Congestion prediction, berth/crane optimisation, alternate routing "
        "recommendations and 72-hour shift planning for container terminals."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/", tags=["meta"])
def root() -> dict:
    """Landing payload pointing to docs and the health probe."""
    return {
        "name": settings.app_name,
        "version": app.version,
        "docs": "/docs",
        "health": "/api/health",
    }
