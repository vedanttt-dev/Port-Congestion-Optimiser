"""Aggregated API router: every feature router mounts here (plan.md §7)."""

from fastapi import APIRouter

from app.routers import health, data, predict, optimize, plan, kpis, live, export, scenario, ws

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(data.router)
api_router.include_router(predict.router)
api_router.include_router(optimize.router)
api_router.include_router(plan.router)
api_router.include_router(kpis.router)
api_router.include_router(live.router)
api_router.include_router(export.router)
api_router.include_router(scenario.router)
api_router.include_router(ws.router)
