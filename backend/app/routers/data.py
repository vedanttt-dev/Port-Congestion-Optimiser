"""GET /api/data/summary — current scenario snapshot."""

from fastapi import APIRouter

from app.schemas import (
    AltPortSummary,
    BerthSummary,
    CraneSummary,
    DataSummaryResponse,
    YardSummary,
    VesselSummary,
)
from app.services.scenario import get_active_scenario

router = APIRouter(tags=["data"])


@router.get("/data/summary", response_model=DataSummaryResponse)
def data_summary() -> DataSummaryResponse:
    """Return the full scenario snapshot: vessels, berths, cranes, yard, ports."""
    sc = get_active_scenario()
    meta = sc["meta"]

    vessels = [
        VesselSummary(
            id=v.id, name=v.name, type=v.type.value,
            teu_capacity=v.teu_capacity, eta_h=v.eta_h,
            planned_etd_h=v.planned_etd_h, origin=v.origin,
            priority=v.priority_class,
        )
        for v in sc["vessels"]
    ]

    berths = [
        BerthSummary(
            id=b.id, length_m=b.length_m, max_draft_m=b.max_draft_m,
            crane_count=len(b.crane_ids), base_moves_per_hr=b.base_moves_per_hr,
            yard_zone_id=b.yard_zone_id,
        )
        for b in sc["berths"]
    ]

    cranes = [
        CraneSummary(
            id=c.id, max_moves_per_hr=c.max_moves_per_hr,
            compatible_berths=c.compatible_berths,
        )
        for c in sc["cranes"]
    ]

    yard_zones = [
        YardSummary(
            id=z.id, teu_capacity=z.teu_capacity, current_teu=z.current_teu,
            util_pct=round(z.current_teu / z.teu_capacity * 100, 1) if z.teu_capacity else 0.0,
        )
        for z in sc["yard_zones"]
    ]

    alt_ports = [
        AltPortSummary(
            id=p.id, name=p.name, transit_hours=p.transit_hours,
            berth_capacity=p.berth_capacity, congestion_index=p.congestion_index,
        )
        for p in sc["alt_ports"]
    ]

    return DataSummaryResponse(
        meta=meta, vessels=vessels, berths=berths,
        cranes=cranes, yard_zones=yard_zones, alt_ports=alt_ports,
    )
