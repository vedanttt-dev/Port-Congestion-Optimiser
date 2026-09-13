"""POST /api/plan — 72 h shift plan (9 blocks + work orders)."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas import PlanRequest, PlanResponse, ShiftBlock, WorkOrder
from app.services.scenario import svc

router = APIRouter(tags=["plan"])


def _build_shift_plan(horizon_h: float = 72.0, shift_h: float = 8.0) -> list[ShiftBlock]:
    """Map the optimised schedule to 9 shift blocks (3 days × 3 shifts)."""
    result = svc.get_result()
    shifts: list[ShiftBlock] = []

    num_shifts = int(horizon_h / shift_h)
    for i in range(num_shifts):
        day = i // 3 + 1
        shift_no = i % 3 + 1
        start_h = i * shift_h
        end_h = (i + 1) * shift_h
        shift_id = f"D{day}S{shift_no}"

        # Collect work orders for this shift window
        work_orders = []
        alerts = []
        for vs in result.vessel_states.values():
            if vs.assigned_berth and vs.berth_assigned_h <= end_h and vs.service_end_h >= start_h:
                work_orders.append(WorkOrder(
                    vessel_id=vs.vessel.id,
                    berth_id=vs.assigned_berth,
                    crane_ids=vs.assigned_cranes,
                    target_moves=min(
                        vs.total_moves,
                        int(vs.total_moves * (end_h - max(start_h, vs.berth_assigned_h))
                            / max(1, vs.service_end_h - vs.berth_assigned_h)),
                    ),
                    priority=vs.vessel.priority_class,
                    alert="High priority" if vs.vessel.priority_class == 1 else "",
                ))
                if vs.wait_h > 24:
                    alerts.append(f"Vessel {vs.vessel.id} waited {vs.wait_h:.1f}h")

        shifts.append(ShiftBlock(
            id=shift_id,
            window=f"h{start_h:.0f}-h{end_h:.0f}",
            alerts=alerts,
            work_orders=work_orders,
            contingency_notes=[],
        ))

    return shifts


@router.post("/plan", response_model=PlanResponse)
def plan(req: PlanRequest | None = None) -> PlanResponse:
    """72 h shift plan (9 blocks + work orders)."""
    horizon = req.horizon_h if req else 72.0
    shift_h = req.shift_h if req else 8.0
    shifts = _build_shift_plan(horizon, shift_h)
    return PlanResponse(shifts=shifts)
