"""Domain entities — plain dataclasses (plan.md §4).

All times are **simulation hours**; clocks start at ``as_of_h = 0`` (now).
Prediction horizon = 168 h (7 days); planning window = 72 h; shift length = 8 h.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class VesselType(str, enum.Enum):
    FEEDER = "feeder"
    MEDIUM = "medium"
    MEGA = "mega"


class VesselStatus(str, enum.Enum):
    INBOUND = "inbound"
    ANCHORAGE = "anchorage"
    BERTHED = "berthed"
    OUTBOUND = "outbound"
    DIVERTED = "diverted"


class BerthStatus(str, enum.Enum):
    IDLE = "idle"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"


class HotspotKind(str, enum.Enum):
    BERTH_UTIL = "berth_util"
    QUEUE = "queue"
    WAIT = "wait"
    YARD = "yard"


class Severity(str, enum.Enum):
    LOW = "low"
    MED = "med"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------

@dataclass
class Vessel:
    id: str
    name: str
    type: VesselType
    teu_capacity: int
    import_moves: int
    export_moves: int
    loa_m: float
    draft_m: float
    eta_h: float
    planned_etd_h: float
    origin: str
    destination: str
    priority_class: int = 1
    demurrage_usd_per_day: float = 0.0
    status: VesselStatus = VesselStatus.INBOUND


@dataclass
class Berth:
    id: str
    length_m: float
    max_draft_m: float
    crane_ids: list[str] = field(default_factory=list)
    base_moves_per_hr: int = 0
    yard_zone_id: str = ""
    status: BerthStatus = BerthStatus.IDLE


@dataclass
class Crane:
    id: str
    max_moves_per_hr: int = 0
    compatible_berths: list[str] = field(default_factory=list)
    maintenance_window: tuple[float, float] | None = None


@dataclass
class YardZone:
    id: str
    teu_capacity: int = 0
    current_teu: int = 0
    avg_dwell_days: float = 0.0


@dataclass
class AltPort:
    id: str
    name: str
    transit_hours: float
    berth_capacity: int
    handling_premium_usd: float
    congestion_index: float


# ---------------------------------------------------------------------------
# Schedule & planning entities
# ---------------------------------------------------------------------------

@dataclass
class ScheduleEntry:
    vessel_id: str
    berth_id: str
    start_h: float
    end_h: float
    crane_count: int
    moves_planned: int


@dataclass
class ShiftBlock:
    day: int
    shift_no: int
    start_h: float
    end_h: float


@dataclass
class WorkOrder:
    shift_id: str
    vessel_id: str
    berth_id: str
    crane_ids: list[str] = field(default_factory=list)
    target_moves: int = 0
    priority: int = 1
    alert: str = ""
    contingency_note: str = ""


# ---------------------------------------------------------------------------
# Alert & KPI entities
# ---------------------------------------------------------------------------

@dataclass
class HotspotAlert:
    id: str
    kind: HotspotKind
    horizon_h: float
    severity: Severity
    affected_berths: list[str] = field(default_factory=list)
    affected_vessels: list[str] = field(default_factory=list)
    lead_time_h: float = 0.0
    message: str = ""


@dataclass
class KpiSnapshot:
    avg_wait_h: float = 0.0
    p95_wait_h: float = 0.0
    max_queue: int = 0
    berth_util_pct: float = 0.0
    crane_util_pct: float = 0.0
    yard_util_pct: float = 0.0
    demurrage_cost_usd: float = 0.0
    hotspot_count: int = 0
    cost_saved_usd: float = 0.0
