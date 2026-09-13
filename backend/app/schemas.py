"""Pydantic API schemas — contract freeze (plan.md §7).

Every request/response shape used by the REST endpoints lives here.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    """POST /api/predict"""
    as_of_h: float = 0.0
    horizon_h: float = 168.0
    overrides: dict | None = None


class OptimizeRequest(BaseModel):
    """POST /api/optimize"""
    scenario: str = "default"
    overrides: dict | None = None


class PlanRequest(BaseModel):
    """POST /api/plan"""
    assignments: list[dict] | None = None
    horizon_h: float = 72.0
    shift_h: float = 8.0


# ---------------------------------------------------------------------------
# Response sub-schemas
# ---------------------------------------------------------------------------

class VesselForecast(BaseModel):
    vessel_id: str
    name: str = ""
    type: str = ""
    predicted_wait_h: float = 0.0
    predicted_berth_h: float = 0.0
    status: str = ""
    eta_h: float = 0.0
    teu_capacity: int = 0
    priority: int = 2


class BucketForecast(BaseModel):
    h: float
    util_pct: float


class BerthUtilForecast(BaseModel):
    berth_id: str
    buckets: list[BucketForecast] = []


class QueueForecast(BaseModel):
    h: float
    queue_size: int


class YardForecast(BaseModel):
    h: float
    util_pct: float


class Hotspot(BaseModel):
    id: str = ""
    kind: str
    severity: str = "low"
    horizon_h: float = 0.0
    lead_time_h: float = 0.0
    affected_berths: list[str] = []
    affected_vessels: list[str] = []
    message: str = ""


class PredictResponse(BaseModel):
    vessel_forecasts: list[VesselForecast] = []
    berth_util_forecast: list[BerthUtilForecast] = []
    queue_forecast: list[QueueForecast] = []
    yard_forecast: list[YardForecast] = []
    hotspots: list[Hotspot] = []


# --- Optimize response ---

class Assignment(BaseModel):
    vessel_id: str
    berth_id: str
    start_h: float
    end_h: float
    crane_count: int
    moves_planned: int = 0


class Reroute(BaseModel):
    vessel_id: str
    alt_port_id: str
    est_cost_usd: float
    saving_usd: float
    reason: str


class KpiComparison(BaseModel):
    avg_wait_h: float = 0.0
    p95_wait_h: float = 0.0
    max_queue: int = 0
    berth_util_pct: float = 0.0
    crane_util_pct: float = 0.0
    yard_util_pct: float = 0.0
    demurrage_cost_usd: float = 0.0
    cost_saved_usd: float = 0.0


class OptimizeResponse(BaseModel):
    assignments: list[Assignment] = []
    reroutes: list[Reroute] = []
    kpis: dict = Field(default_factory=lambda: {"baseline": {}, "optimized": {}})
    solve_ms: float = 0.0


# --- Plan response ---

class WorkOrder(BaseModel):
    vessel_id: str
    berth_id: str
    crane_ids: list[str] = []
    target_moves: int = 0
    priority: int = 2
    alert: str = ""
    contingency_note: str = ""


class ShiftBlock(BaseModel):
    id: str
    window: str
    alerts: list[str] = []
    work_orders: list[WorkOrder] = []
    contingency_notes: list[str] = []


class PlanResponse(BaseModel):
    shifts: list[ShiftBlock] = []


# --- KPIs response ---

class KpisResponse(BaseModel):
    avg_wait_h: float = 0.0
    p95_wait_h: float = 0.0
    max_queue: int = 0
    berth_util_pct: float = 0.0
    crane_util_pct: float = 0.0
    yard_util_pct: float = 0.0
    demurrage_cost_usd: float = 0.0
    hotspot_count: int = 0
    cost_saved_usd: float = 0.0


# --- Data summary ---

class BerthSummary(BaseModel):
    id: str
    length_m: float
    max_draft_m: float
    crane_count: int = 0
    base_moves_per_hr: int = 0
    yard_zone_id: str = ""


class CraneSummary(BaseModel):
    id: str
    max_moves_per_hr: int = 0
    compatible_berths: list[str] = []


class YardSummary(BaseModel):
    id: str
    teu_capacity: int = 0
    current_teu: int = 0
    util_pct: float = 0.0


class AltPortSummary(BaseModel):
    id: str
    name: str = ""
    transit_hours: float = 0.0
    berth_capacity: int = 0
    congestion_index: float = 0.0


class VesselSummary(BaseModel):
    id: str
    name: str = ""
    type: str = ""
    teu_capacity: int = 0
    eta_h: float = 0.0
    planned_etd_h: float = 0.0
    origin: str = ""
    priority: int = 2


class DataSummaryResponse(BaseModel):
    meta: dict = Field(default_factory=dict)
    vessels: list[VesselSummary] = []
    berths: list[BerthSummary] = []
    cranes: list[CraneSummary] = []
    yard_zones: list[YardSummary] = []
    alt_ports: list[AltPortSummary] = []


# --- Live / map response ---

class VesselPosition(BaseModel):
    id: str
    name: str = ""
    lat: float = 0.0
    lon: float = 0.0
    state: str = "inbound"
    speed_kn: float = 0.0
    heading: float = 0.0
    berth_id: str | None = None
    vessel_type: str = ""
    teu_capacity: int = 0


class LiveEvent(BaseModel):
    time_h: float
    vessel_id: str
    event_type: str
    detail: str = ""


class LiveResponse(BaseModel):
    sim_h: float = 0.0
    vessels: list[VesselPosition] = []
    queue_size: int = 0
    yard_util_pct: float = 0.0
    recent_events: list[LiveEvent] = []
    kpis: dict = Field(default_factory=dict)
