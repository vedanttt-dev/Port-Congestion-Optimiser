"""GET /api/live — live simulation snapshot for map animation."""

from __future__ import annotations

import math

from fastapi import APIRouter

from app.schemas import LiveEvent, LiveResponse, VesselPosition
from app.services.scenario import svc

router = APIRouter(tags=["live"])

# Simple lat/lon grid for the port area (LA/Long Beach approximate)
_BASE_LAT = 33.75
_BASE_LON = -118.25
_BERTH_SPACING = 0.005


def _vessel_position(vs, berths_map: dict) -> VesselPosition:
    """Derive a lat/lon position from the vessel's current sim state."""
    status = vs.vessel.status.value

    if status == "berthed" and vs.assigned_berth:
        # Position at berth
        berth_idx = 0
        for i, b in enumerate(berths_map.values()):
            if b.id == vs.assigned_berth:
                berth_idx = i
                break
        lat = _BASE_LAT + berth_idx * _BERTH_SPACING
        lon = _BASE_LON + berth_idx * _BERTH_SPACING * 0.5
        heading = 0.0
    elif status == "anchorage":
        # Anchorage area — offset from port
        lat = _BASE_LAT - 0.02
        lon = _BASE_LON + 0.01 + (hash(vs.vessel.id) % 100) * 0.0002
        heading = 0.0
    elif status == "outbound":
        # Heading away from port
        lat = _BASE_LAT + 0.05
        lon = _BASE_LON - 0.05
        heading = 225.0
    elif status == "diverted":
        lat = _BASE_LAT - 0.1
        lon = _BASE_LON + 0.1
        heading = 315.0
    else:
        # Inbound — approaching from sea
        lat = _BASE_LAT - 0.04
        lon = _BASE_LON + 0.03
        heading = 45.0

    return VesselPosition(
        id=vs.vessel.id,
        name=vs.vessel.name,
        lat=round(lat, 6),
        lon=round(lon, 6),
        state=status,
        speed_kn=0.0 if status in ("berthed", "anchorage") else 12.0,
        heading=heading,
        berth_id=vs.assigned_berth or None,
        vessel_type=vs.vessel.type.value,
        teu_capacity=vs.vessel.teu_capacity,
    )


@router.get("/live", response_model=LiveResponse)
def live() -> LiveResponse:
    """Live simulation snapshot: vessel positions, queue, recent events."""
    sc = svc.scenario
    result = svc.get_result()
    kpis = svc.get_kpis()

    berths_map = {b.id: b for b in sc["berths"]}

    vessel_positions = [
        _vessel_position(vs, berths_map) for vs in result.vessel_states.values()
    ]

    # Recent events (last 20)
    recent = [
        LiveEvent(
            time_h=round(e.time_h, 2),
            vessel_id=e.vessel_id,
            event_type=e.event_type.value,
            detail=e.detail,
        )
        for e in result.events[-20:]
    ]

    yard_cap = sum(z.teu_capacity for z in sc["yard_zones"])
    yard_teu = sum(result.yard_teu.get(z.id, z.current_teu) for z in sc["yard_zones"])

    return LiveResponse(
        sim_h=round(result.events[-1].time_h, 2) if result.events else 0.0,
        vessels=vessel_positions,
        queue_size=max((qs[1] for qs in result.queue_samples), default=0),
        yard_util_pct=round(yard_teu / yard_cap * 100, 1) if yard_cap else 0.0,
        recent_events=recent,
        kpis={
            "avg_wait_h": kpis.avg_wait_h,
            "demurrage_cost_usd": kpis.demurrage_cost_usd,
        },
    )
