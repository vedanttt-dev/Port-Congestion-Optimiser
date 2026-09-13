"""GET /api/kpis — aggregated metrics + deltas."""

from fastapi import APIRouter

from app.schemas import KpisResponse
from app.services.scenario import get_active_kpis

router = APIRouter(tags=["kpis"])


@router.get("/kpis", response_model=KpisResponse)
def kpis() -> KpisResponse:
    """Aggregated simulation KPIs."""
    kpi = get_active_kpis()
    return KpisResponse(
        avg_wait_h=kpi.avg_wait_h,
        p95_wait_h=kpi.p95_wait_h,
        max_queue=kpi.max_queue,
        berth_util_pct=kpi.berth_util_pct,
        crane_util_pct=kpi.crane_util_pct,
        yard_util_pct=kpi.yard_util_pct,
        demurrage_cost_usd=kpi.demurrage_cost_usd,
        hotspot_count=0,
        cost_saved_usd=0.0,
    )
