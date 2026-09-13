"""POST /api/predict — congestion forecast + hotspot alerts."""

from __future__ import annotations

import hashlib
from typing import Any

from fastapi import APIRouter

from app.schemas import (
    BerthUtilForecast,
    BucketForecast,
    Hotspot,
    PredictRequest,
    PredictResponse,
    QueueForecast,
    VesselForecast,
    YardForecast,
)
from app.services.scenario import svc

router = APIRouter(tags=["predict"])

_hotspot_counter = 0


def _detect_hotspots(scenario: dict[str, Any], result) -> list[Hotspot]:
    """Simple hotspot rules based on the simulation results (plan.md §3.3)."""
    global _hotspot_counter
    hotspots: list[Hotspot] = []
    meta = scenario["meta"]
    kpis = svc.get_kpis()

    # Rule 1: high avg wait
    if kpis.avg_wait_h > 12:
        _hotspot_counter += 1
        hotspots.append(Hotspot(
            id=f"HS{_hotspot_counter:03d}",
            kind="wait",
            severity="high" if kpis.avg_wait_h > 24 else "med",
            horizon_h=168,
            lead_time_h=max(0, 48),
            message=f"Average anchorage wait is {kpis.avg_wait_h:.1f}h (target < 12h)",
        ))

    # Rule 2: high queue
    if kpis.max_queue > meta["num_berths"] * 2:
        _hotspot_counter += 1
        hotspots.append(Hotspot(
            id=f"HS{_hotspot_counter:03d}",
            kind="queue",
            severity="high" if kpis.max_queue > meta["num_berths"] * 4 else "med",
            horizon_h=168,
            lead_time_h=max(0, 36),
            affected_berths=[b.id for b in scenario["berths"]],
            message=f"Max queue reached {kpis.max_queue} vessels (capacity warning)",
        ))

    # Rule 3: berth utilisation
    if kpis.berth_util_pct > 80:
        _hotspot_counter += 1
        hotspots.append(Hotspot(
            id=f"HS{_hotspot_counter:03d}",
            kind="berth_util",
            severity="high" if kpis.berth_util_pct > 90 else "med",
            horizon_h=168,
            lead_time_h=max(0, 24),
            message=f"Berth utilisation at {kpis.berth_util_pct:.1f}%",
        ))

    # Rule 4: yard utilisation
    if kpis.yard_util_pct > 85:
        _hotspot_counter += 1
        hotspots.append(Hotspot(
            id=f"HS{_hotspot_counter:03d}",
            kind="yard",
            severity="high" if kpis.yard_util_pct > 90 else "med",
            horizon_h=168,
            lead_time_h=max(0, 24),
            message=f"Yard utilisation at {kpis.yard_util_pct:.1f}% (target ≤ 85%)",
        ))

    return hotspots


def _build_forecasts(scenario: dict[str, Any], result) -> PredictResponse:
    """Build vessel forecasts + utilisation forecasts from sim results."""
    vessel_forecasts = []
    for vs in result.vessel_states.values():
        vessel_forecasts.append(VesselForecast(
            vessel_id=vs.vessel.id,
            name=vs.vessel.name,
            type=vs.vessel.type.value,
            predicted_wait_h=round(vs.wait_h, 2),
            predicted_berth_h=round(
                (vs.service_end_h - vs.service_start_h) if vs.service_start_h > 0 else 0, 2
            ),
            status=vs.vessel.status.value,
            eta_h=vs.vessel.eta_h,
            teu_capacity=vs.vessel.teu_capacity,
            priority=vs.vessel.priority_class,
        ))

    # Berth utilisation in 24h buckets
    horizon = 168.0
    bucket_size = 24.0
    berth_util_forecast = []
    for berth in scenario["berths"]:
        buckets = []
        for h_start in range(0, int(horizon), int(bucket_size)):
            h_end = h_start + bucket_size
            busy = sum(
                min(end, h_end) - max(start, h_start)
                for start, end in result.berth_busy.get(berth.id, [])
                if end > h_start and start < h_end
            )
            util = round(busy / bucket_size * 100, 1)
            buckets.append(BucketForecast(h=float(h_start), util_pct=util))
        berth_util_forecast.append(BerthUtilForecast(berth_id=berth.id, buckets=buckets))

    # Queue forecast
    queue_forecast = []
    for h_start in range(0, int(horizon), int(bucket_size)):
        relevant = [qs for qs in result.queue_samples if h_start <= qs[0] < h_start + bucket_size]
        max_q = max((qs[1] for qs in relevant), default=0)
        queue_forecast.append(QueueForecast(h=float(h_start), queue_size=max_q))

    # Yard forecast
    yard_forecast = []
    yard_cap = sum(z.teu_capacity for z in scenario["yard_zones"])
    for h_start in range(0, int(horizon), int(bucket_size)):
        yard_teu = sum(result.yard_teu.get(z.id, z.current_teu) for z in scenario["yard_zones"])
        util = round(yard_teu / yard_cap * 100, 1) if yard_cap else 0.0
        yard_forecast.append(YardForecast(h=float(h_start), util_pct=util))

    return PredictResponse(
        vessel_forecasts=vessel_forecasts,
        berth_util_forecast=berth_util_forecast,
        queue_forecast=queue_forecast,
        yard_forecast=yard_forecast,
        hotspots=_detect_hotspots(scenario, result),
    )


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest | None = None) -> PredictResponse:
    """Congestion forecast + hotspot alerts."""
    sc = svc.scenario
    result = svc.get_result(horizon_h=req.horizon_h if req else 168.0)
    return _build_forecasts(sc, result)
