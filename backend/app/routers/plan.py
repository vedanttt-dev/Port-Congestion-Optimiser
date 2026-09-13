"""POST /api/plan — 72 h shift plan (9 blocks + work orders + CSV export).

P8: maps optimised schedule → shift blocks with hotspot alerts + contingency notes.
"""

from __future__ import annotations

import io
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.optimization.solver import BerthCraneOptimiser
from app.planning.shift_plan import ShiftPlanBuilder, shift_plan_to_csv
from app.schemas import PlanRequest, PlanResponse, ShiftBlock, WorkOrder
from app.services.scenario import get_active_scenario

router = APIRouter(tags=["plan"])


def _build_shift_plan(
    horizon_h: float = 72.0,
    shift_h: float = 8.0,
    assignments: list | None = None,
) -> tuple[list[dict], list]:
    """Build shift plan, return (shifts_dicts, berth_assignments)."""
    sc = get_active_scenario()

    # Get assignments from optimizer if not supplied
    if assignments is None:
        opt = BerthCraneOptimiser(sc, horizon_h=horizon_h, time_limit_s=2.0)
        opt_result = opt.solve()
        ba_list = list(opt_result.assignments)
    else:
        from app.optimization.solver import BerthAssignment
        ba_list = [
            BerthAssignment(
                vessel_id=a["vessel_id"],
                berth_id=a["berth_id"],
                start_h=a.get("start_h", 0),
                end_h=a.get("end_h", 0),
                crane_count=a.get("crane_count", 2),
                moves_planned=a.get("moves_planned", 0),
                wait_h=a.get("wait_h", 0),
            )
            for a in assignments
        ]

    builder = ShiftPlanBuilder(
        ba_list, sc, horizon_h=horizon_h, shift_h=shift_h
    )
    shifts = builder.build()
    return shifts, ba_list


def _dicts_to_shift_blocks(shifts: list[dict]) -> list[ShiftBlock]:
    """Convert dicts from builder to Pydantic ShiftBlock."""
    blocks = []
    for s in shifts:
        wo_list = [
            WorkOrder(
                vessel_id=wo["vessel_id"],
                berth_id=wo["berth_id"],
                crane_ids=wo.get("crane_ids", []),
                target_moves=wo.get("target_moves", 0),
                priority=wo.get("priority", 2),
                alert=wo.get("alert", ""),
            )
            for wo in s["work_orders"]
        ]
        blocks.append(ShiftBlock(
            id=s["id"],
            window=s["window"],
            alerts=s.get("alerts", []),
            work_orders=wo_list,
            contingency_notes=s.get("contingency_notes", []),
        ))
    return blocks


@router.post("/plan", response_model=PlanResponse)
def plan(req: PlanRequest | None = None) -> PlanResponse:
    """72 h shift plan (9 blocks + work orders + hotspot alerts + contingency notes)."""
    horizon = req.horizon_h if req else 72.0
    shift_h = req.shift_h if req else 8.0
    assignments = req.assignments if req and req.assignments else None
    shifts, _ = _build_shift_plan(horizon, shift_h, assignments)
    return PlanResponse(shifts=_dicts_to_shift_blocks(shifts))


@router.get("/plan/export")
def plan_export_csv(
    horizon_h: float = 72.0,
    shift_h: float = 8.0,
) -> StreamingResponse:
    """GET /api/plan/export — download shift plan as CSV."""
    shifts, _ = _build_shift_plan(horizon_h, shift_h)
    csv_str = shift_plan_to_csv(shifts)
    buf = io.BytesIO(csv_str.encode("utf-8"))
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=shift_plan.csv"},
    )
