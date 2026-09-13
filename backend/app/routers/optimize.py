"""POST /api/optimize — berth/crane assignments + reroutes + KPIs."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas import (
    Assignment,
    KpiComparison,
    OptimizeRequest,
    OptimizeResponse,
    Reroute,
)
from app.services.scenario import svc

router = APIRouter(tags=["optimize"])


@router.post("/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest | None = None) -> OptimizeResponse:
    """Run the baseline simulation and return assignments + KPI comparison.

    Phase 6 will replace this with the actual CP-SAT solver. For now it
    returns the FCFS baseline assignments derived from the simulation.
    """
    sc = svc.scenario
    result = svc.get_result()
    kpis = svc.get_kpis()

    # Build assignments from simulation results
    assignments = []
    for vs in result.vessel_states.values():
        if vs.assigned_berth:
            assignments.append(Assignment(
                vessel_id=vs.vessel.id,
                berth_id=vs.assigned_berth,
                start_h=round(vs.berth_assigned_h, 2),
                end_h=round(vs.service_end_h, 2),
                crane_count=len(vs.assigned_cranes),
                moves_planned=vs.total_moves,
            ))

    # Stub reroutes — will be real in P7
    reroutes: list[Reroute] = []

    return OptimizeResponse(
        assignments=assignments,
        reroutes=reroutes,
        kpis={
            "baseline": KpiComparison(
                avg_wait_h=kpis.avg_wait_h,
                p95_wait_h=kpis.p95_wait_h,
                max_queue=kpis.max_queue,
                berth_util_pct=kpis.berth_util_pct,
                crane_util_pct=kpis.crane_util_pct,
                yard_util_pct=kpis.yard_util_pct,
                demurrage_cost_usd=kpis.demurrage_cost_usd,
            ).model_dump(),
            "optimized": KpiComparison(
                avg_wait_h=kpis.avg_wait_h,
                p95_wait_h=kpis.p95_wait_h,
                max_queue=kpis.max_queue,
                berth_util_pct=kpis.berth_util_pct,
                crane_util_pct=kpis.crane_util_pct,
                yard_util_pct=kpis.yard_util_pct,
                demurrage_cost_usd=kpis.demurrage_cost_usd,
            ).model_dump(),
        },
        solve_ms=0.0,
    )
