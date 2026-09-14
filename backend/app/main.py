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

print(f"Registered routes: {[r.path for r in app.routes]}")


@app.on_event("startup")
def _startup_generate_presets() -> None:
    """Pre-generate default scenarios so they're available immediately."""
    try:
        from app.services.scenario_manager import scenario_manager
        from app.services.scenario import svc

        # Ensure the default scenario exists
        scenario_manager._scenarios["default"] = svc.scenario

        # Generate preset scenarios
        presets = [
            {"name": "light_traffic", "seed": 123, "weeks": 2, "num_berths": 6, "num_cranes": 18},
            {"name": "heavy_surge", "seed": 777, "weeks": 6, "num_berths": 8, "num_cranes": 25},
            {"name": "crane_shortage", "seed": 42, "weeks": 4, "num_berths": 8, "num_cranes": 12},
            {"name": "capacity_crunch", "seed": 42, "weeks": 4, "num_berths": 5, "num_cranes": 15},
        ]

        for p in presets:
            if p["name"] not in scenario_manager._scenarios:
                scenario_manager.generate(**p)
    except Exception as e:
        print(f"Warning: Startup preset generation failed: {e}")


@app.get("/", tags=["meta"])
def root() -> dict:
    """Landing payload pointing to docs and the health probe."""
    return {
        "name": settings.app_name,
        "version": app.version,
        "docs": "/docs",
        "health": "/api/health",
    }
