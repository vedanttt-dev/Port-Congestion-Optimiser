"""Scenario management endpoints — generate, list, compare, save."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.schemas import KpisResponse
from app.services.scenario import svc
from app.services.scenario_manager import scenario_manager

router = APIRouter(tags=["scenario"])


def _ensure_default() -> None:
    """Ensure default scenario exists in the manager."""
    if "default" not in scenario_manager._scenarios:
        scenario_manager._scenarios["default"] = svc.scenario


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ScenarioGenerateRequest(BaseModel):
    """POST /api/scenario/generate"""
    name: str = "scenario_1"
    seed: int = Field(default=42, ge=0, le=999999)
    weeks: int = Field(default=4, ge=1, le=12)
    num_berths: int | None = Field(default=None, ge=3, le=16)
    num_cranes: int | None = Field(default=None, ge=4, le=40)


class ScenarioCompareRequest(BaseModel):
    """POST /api/scenario/compare"""
    scenario_a: str
    scenario_b: str


class ScenarioSetActiveRequest(BaseModel):
    """POST /api/scenario/set-active"""
    name: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/scenario/list")
def list_scenarios() -> list[dict]:
    """List all saved scenarios with summary stats."""
    _ensure_default()
    return scenario_manager.list_scenarios()


@router.post("/scenario/generate")
def generate_scenario(req: ScenarioGenerateRequest) -> dict:
    """Generate a new scenario with custom parameters."""
    _ensure_default()
    try:
        sc = scenario_manager.generate(
            name=req.name,
            seed=req.seed,
            weeks=req.weeks,
            num_berths=req.num_berths,
            num_cranes=req.num_cranes,
        )
        return {
            "name": req.name,
            "meta": sc["meta"],
            "num_vessels": len(sc["vessels"]),
            "num_berths": len(sc["berths"]),
            "num_cranes": len(sc["cranes"]),
            "status": "generated",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scenario/{name}/kpis")
def get_scenario_kpis(name: str) -> dict:
    """Get KPIs for a specific scenario."""
    try:
        kpi = scenario_manager.get_kpis(name)
        return {
            "name": name,
            "kpis": {
                "avg_wait_h": round(kpi.avg_wait_h, 2),
                "p95_wait_h": round(kpi.p95_wait_h, 2),
                "max_queue": kpi.max_queue,
                "berth_util_pct": round(kpi.berth_util_pct, 1),
                "crane_util_pct": round(kpi.crane_util_pct, 1),
                "yard_util_pct": round(kpi.yard_util_pct, 1),
                "demurrage_cost_usd": round(kpi.demurrage_cost_usd, 2),
            },
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")


@router.post("/scenario/compare")
def compare_scenarios(req: ScenarioCompareRequest) -> dict:
    """Compare two scenarios side by side."""
    try:
        return scenario_manager.compare(req.scenario_a, req.scenario_b)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/scenario/set-active")
def set_active_scenario(req: ScenarioSetActiveRequest) -> dict:
    """Set the active scenario used by all other endpoints."""
    try:
        scenario_manager.set_active(req.name)
        return {"active": req.name, "status": "set"}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Scenario '{req.name}' not found")


@router.delete("/scenario/{name}")
def delete_scenario(name: str) -> dict:
    """Delete a scenario (cannot delete 'default')."""
    if name == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default scenario")
    success = scenario_manager.delete(name)
    return {"deleted": success, "name": name}
