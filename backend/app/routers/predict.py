"""POST /api/predict — congestion forecast + hotspot alerts (P5)."""

from __future__ import annotations

from fastapi import APIRouter

from app.prediction.forecaster import ForwardSimulator
from app.prediction.hotspots import detect_hotspots
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
from app.services.scenario import get_active_scenario

router = APIRouter(tags=["predict"])


def _build_forecasts(
    scenario: dict, as_of_h: float, horizon_h: float
) -> PredictResponse:
    """Run forward simulation and build the full predict response."""
    sim = ForwardSimulator(scenario, as_of_h=as_of_h, horizon_h=horizon_h)
    fwd = sim.run()

    # Vessel forecasts
    vessel_forecasts = [
        VesselForecast(
            vessel_id=vp.vessel_id,
            name=vp.name,
            type=vp.vessel_type,
            predicted_wait_h=vp.predicted_wait_h,
            predicted_berth_h=vp.predicted_berth_h,
            status=vp.status,
            eta_h=vp.eta_h,
            teu_capacity=vp.teu_capacity,
            priority=vp.priority,
        )
        for vp in fwd.vessel_predictions
    ]

    # Berth utilisation forecast
    berth_util_forecast = [
        BerthUtilForecast(
            berth_id=bu.berth_id,
            buckets=[
                BucketForecast(h=b.h, util_pct=b.util_pct) for b in bu.buckets
            ],
        )
        for bu in fwd.berth_util
    ]

    # Queue forecast
    queue_forecast = [
        QueueForecast(h=qf.h, queue_size=qf.queue_size)
        for qf in fwd.queue_forecast
    ]

    # Yard forecast
    yard_forecast = [
        YardForecast(h=yf.h, util_pct=yf.util_pct)
        for yf in fwd.yard_forecast
    ]

    # Hotspot detection with lead times
    hs_list = detect_hotspots(fwd, scenario, as_of_h=as_of_h)
    hotspots = [
        Hotspot(
            id=hs.id,
            kind=hs.kind,
            severity=hs.severity,
            horizon_h=hs.horizon_h,
            lead_time_h=hs.lead_time_h,
            affected_berths=hs.affected_berths,
            affected_vessels=hs.affected_vessels,
            message=hs.message,
        )
        for hs in hs_list
    ]

    return PredictResponse(
        vessel_forecasts=vessel_forecasts,
        berth_util_forecast=berth_util_forecast,
        queue_forecast=queue_forecast,
        yard_forecast=yard_forecast,
        hotspots=hotspots,
    )


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest | None = None) -> PredictResponse:
    """Congestion forecast + hotspot alerts with lead times ≥ 12h."""
    sc = get_active_scenario()
    as_of_h = req.as_of_h if req else 0.0
    horizon_h = req.horizon_h if req else 168.0
    return _build_forecasts(sc, as_of_h, horizon_h)
