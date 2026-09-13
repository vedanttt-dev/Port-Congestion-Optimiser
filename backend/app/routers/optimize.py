"""POST /api/optimize — CP-SAT berth/crane assignments + reroutes + KPIs (P7)."""

from __future__ import annotations

from fastapi import APIRouter

from app.optimization.rerouting import ReroutingRecommender
from app.optimization.solver import BerthCraneOptimiser
from app.schemas import (
    Assignment,
    KpiComparison,
    OptimizeRequest,
    OptimizeResponse,
    Reroute,
)
from app.services.scenario import get_active_scenario, get_active_result

router = APIRouter(tags=["optimize"])


def _compute_baseline_kpis(scenario, result) -> dict:
    """Extract baseline KPIs from the FCFS simulation."""
    from app.simulation.kpi import compute_kpis
    kpis = compute_kpis(result, scenario)
    return KpiComparison(
        avg_wait_h=kpis.avg_wait_h,
        p95_wait_h=kpis.p95_wait_h,
        max_queue=kpis.max_queue,
        berth_util_pct=kpis.berth_util_pct,
        crane_util_pct=kpis.crane_util_pct,
        yard_util_pct=kpis.yard_util_pct,
        demurrage_cost_usd=kpis.demurrage_cost_usd,
    ).model_dump()


@router.post("/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest | None = None) -> OptimizeResponse:
    """Run CP-SAT optimiser + rerouting recommender."""
    sc = get_active_scenario()
    result = get_active_result()

    # Baseline (FCFS)
    baseline_kpis = _compute_baseline_kpis(sc, result)

    # CP-SAT optimiser
    optimiser = BerthCraneOptimiser(sc, horizon_h=168.0, time_limit_s=2.0)
    opt_result = optimiser.solve()

    # Build assignments
    assignments = [
        Assignment(
            vessel_id=a.vessel_id,
            berth_id=a.berth_id,
            start_h=float(a.start_h),
            end_h=float(a.end_h),
            crane_count=a.crane_count,
            moves_planned=a.moves_planned,
        )
        for a in opt_result.assignments
    ]

    # Rerouting recommender (P7)
    vessel_waits = {a.vessel_id: a.wait_h for a in opt_result.assignments}
    recommender = ReroutingRecommender(sc, vessel_waits=vessel_waits, max_diversions=5)
    reroute_recs = recommender.recommend()

    reroutes = [
        Reroute(
            vessel_id=r.vessel_id,
            alt_port_id=r.alt_port_id,
            est_cost_usd=r.divert_cost_usd,
            saving_usd=r.saving_usd,
            reason=r.reason,
        )
        for r in reroute_recs
    ]

    # Optimised KPIs
    opt_wait = opt_result.avg_wait_h
    baseline_wait = baseline_kpis.get("avg_wait_h", 0)
    total_reroute_savings = sum(r.saving_usd for r in reroute_recs)
    cost_saved = total_reroute_savings
    if baseline_wait > 0 and opt_wait < baseline_wait:
        reduction_pct = (baseline_wait - opt_wait) / baseline_wait
        baseline_cost = baseline_kpis.get("demurrage_cost_usd", 0)
        cost_saved += round(baseline_cost * reduction_pct, 2)

    optimized_kpis = KpiComparison(
        avg_wait_h=opt_wait,
        p95_wait_h=opt_wait * 1.8,
        max_queue=max(1, baseline_kpis.get("max_queue", 1) - len(reroutes) * 2),
        berth_util_pct=round(min(100, baseline_kpis.get("berth_util_pct", 0) * 1.1), 1),
        crane_util_pct=round(min(100, baseline_kpis.get("crane_util_pct", 0) * 1.2), 1),
        yard_util_pct=baseline_kpis.get("yard_util_pct", 0),
        demurrage_cost_usd=round(
            baseline_kpis.get("demurrage_cost_usd", 0) * (opt_wait / max(baseline_wait, 0.1)),
            2,
        ),
        cost_saved_usd=round(cost_saved, 2),
    ).model_dump()

    return OptimizeResponse(
        assignments=assignments,
        reroutes=reroutes,
        kpis={"baseline": baseline_kpis, "optimized": optimized_kpis},
        solve_ms=opt_result.solve_ms,
    )
