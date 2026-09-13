"""Aggregated API router: every feature router mounts here (plan.md §7)."""

from fastapi import APIRouter

from app.routers import health

api_router = APIRouter()
api_router.include_router(health.router)
