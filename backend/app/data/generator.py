"""Synthetic data generator for a congested container terminal (plan.md §4).

Produces a deterministic dataset: vessels, berths, cranes, yard zones,
alternate ports — all conforming to the entity models in ``domain.entities``.

Usage::

    from app.data.generator import generate_scenario
    scenario = generate_scenario(seed=42, weeks=4)

The default parameters reproduce a **congested** LA/Long-Beach-style port:
~30 arrivals/week, 8 berths, 24 cranes, 2 yard zones, 2 alternate ports.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.domain.entities import (
    AltPort,
    Berth,
    BerthStatus,
    Crane,
    Vessel,
    VesselType,
    YardZone,
)

# ---------------------------------------------------------------------------
# Constants — benchmark-validated ranges (plan.md §4 "Synthetic data design")
# ---------------------------------------------------------------------------

VESSEL_ARRIVALS_PER_WEEK_RANGE = (25, 40)

VESSEL_PROFILES: dict[VesselType, dict[str, Any]] = {
    VesselType.FEEDER: {
        "teu_range": (800, 2_000),
        "moves_range": (200, 600),
        "loa_m_range": (140, 200),
        "draft_m_range": (8.0, 12.0),
        "weight": 0.40,
    },
    VesselType.MEDIUM: {
        "teu_range": (4_000, 12_000),
        "moves_range": (800, 2_400),
        "loa_m_range": (250, 320),
        "draft_m_range": (12.0, 15.0),
        "weight": 0.40,
    },
    VesselType.MEGA: {
        "teu_range": (18_000, 24_000),
        "moves_range": (3_600, 6_000),
        "loa_m_range": (360, 400),
        "draft_m_range": (14.5, 16.5),
        "weight": 0.20,
    },
}

PORTS_OF_ORIGIN = [
    "Shanghai", "Busan", "Singapore", "Shenzhen", "Ningbo",
    "Kaohsiung", "Yokohama", "Hamburg", "Antwerp", "Rotterdam",
    "Felixstowe", "Le Havre", "Santos", "Colombo", "Tanjung Pelepas",
]

DEMURRAGE_RATES: dict[VesselType, float] = {
    VesselType.FEEDER: 8_000,
    VesselType.MEDIUM: 25_000,
    VesselType.MEGA: 60_000,
}

VESSEL_NAME_PREFIXES = [
    "MV", "MS", "MT", "MSC", "COSCO", "Maersk", "Evergreen",
    "ONE", "Hapag", "Yang Ming", "ZIM", "CMA CGM",
]

VESSEL_NAME_SUFFIXES = [
    "Spirit", "Glory", "Fortune", "Progress", "Unity",
    "Horizon", "Victory", "Star", "Ocean", "Pioneer",
    "Express", "Vanguard", "Endeavour", "Resolve", "Integrity",
    "Perseverance", "Enterprise", "Champion", "Summit", "Pinnacle",
]

NUM_BERTHS = 8
BERTH_LENGTH_RANGE = (250, 400)
BERTH_DRAFT_RANGE = (13.0, 17.0)

NUM_CRANES_RANGE = (22, 28)
CRANE_MOVES_PER_HR_RANGE = (30, 35)

NUM_YARD_ZONES = 2
YARD_TEU_CAPACITY_RANGE = (8_000, 15_000)
YARD_INITIAL_UTILIZATION = (0.55, 0.75)
YARD_DWELL_DAYS_RANGE = (3.0, 7.0)

ALT_PORTS = [
    {
        "name": "Port of Long Beach (Alternate)",
        "transit_hours": 12.0,
        "berth_capacity": 6,
        "handling_premium_usd": 150_000,
        "congestion_index": 0.35,
    },
    {
        "name": "Port of Oakland (Alternate)",
        "transit_hours": 24.0,
        "berth_capacity": 4,
        "handling_premium_usd": 250_000,
        "congestion_index": 0.20,
    },
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _rand_range(lo: float, hi: float, rng: random.Random) -> float:
    return rng.uniform(lo, hi)


def _rand_int(lo: int, hi: int, rng: random.Random) -> int:
    return rng.randint(lo, hi)


def _generate_vessel_names(count: int, rng: random.Random) -> list[str]:
    """Generate unique vessel names."""
    names: set[str] = set()
    while len(names) < count:
        prefix = rng.choice(VESSEL_NAME_PREFIXES)
        suffix = rng.choice(VESSEL_NAME_SUFFIXES)
        name = f"{prefix} {suffix}"
        names.add(name)
    return list(names)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_scenario(
    *,
    seed: int = 42,
    weeks: int = 4,
    as_of_h: float = 0.0,
) -> dict[str, Any]:
    """Generate a complete synthetic scenario.

    Parameters
    ----------
    seed:
        Random seed for reproducibility.
    weeks:
        Number of weeks of vessel arrivals to generate.
    as_of_h:
        Simulation-hour clock offset (0 = now).

    Returns
    -------
    dict with keys: vessels, berths, cranes, yard_zones, alt_ports, meta.
    """
    rng = random.Random(seed)

    # --- Vessels -----------------------------------------------------------
    arrivals_per_week = _rand_int(*VESSEL_ARRIVALS_PER_WEEK_RANGE, rng)
    total_arrivals = arrivals_per_week * weeks

    vessel_names = _generate_vessel_names(total_arrivals, rng)

    vessel_types = list(VESSEL_PROFILES.keys())
    type_weights = [VESSEL_PROFILES[v]["weight"] for v in vessel_types]

    # Pre-allocate vessel type counts to guarantee target distribution
    type_counts = {vt: 0 for vt in vessel_types}
    for i in range(total_arrivals):
        vtype = rng.choices(vessel_types, weights=type_weights, k=1)[0]
        type_counts[vtype] += 1
    # Overwrite with exact weighted allocation
    remaining = total_arrivals
    for vt in vessel_types:
        exact = round(total_arrivals * VESSEL_PROFILES[vt]["weight"])
        type_counts[vt] = min(exact, remaining)
        remaining -= type_counts[vt]
    # Distribute remainder
    for vt in vessel_types:
        if remaining <= 0:
            break
        type_counts[vt] += 1
        remaining -= 1

    # Build the ordered list of types
    type_pool: list[VesselType] = []
    for vt in vessel_types:
        type_pool.extend([vt] * type_counts[vt])
    rng.shuffle(type_pool)

    vessels: list[Vessel] = []
    for i in range(total_arrivals):
        vtype = type_pool[i]
        profile = VESSEL_PROFILES[vtype]

        teu = _rand_int(*profile["teu_range"], rng)
        moves = _rand_int(*profile["moves_range"], rng)
        import_moves = moves // 2 + rng.randint(-50, 50)
        import_moves = max(0, min(import_moves, moves))
        export_moves = moves - import_moves

        loa = round(_rand_range(*profile["loa_m_range"], rng), 1)
        draft = round(_rand_range(*profile["draft_m_range"], rng), 1)

        # Spread arrivals over the week window
        week_idx = i // arrivals_per_week
        day_in_week = rng.uniform(0, 168)
        eta_h = round(week_idx * 168 + day_in_week + as_of_h, 2)
        service_duration = rng.uniform(12, 48)
        planned_etd_h = round(eta_h + service_duration, 2)

        origin = rng.choice(PORTS_OF_ORIGIN)
        # Destination is always the primary terminal
        destination = "Port of Los Angeles (Primary)"

        priority = 1 if rng.random() < 0.15 else 2  # 15 % high-priority
        demurrage = DEMURRAGE_RATES[vtype]

        vessel = Vessel(
            id=f"V{i + 1:04d}",
            name=vessel_names[i],
            type=vtype,
            teu_capacity=teu,
            import_moves=import_moves,
            export_moves=export_moves,
            loa_m=loa,
            draft_m=draft,
            eta_h=eta_h,
            planned_etd_h=planned_etd_h,
            origin=origin,
            destination=destination,
            priority_class=priority,
            demurrage_usd_per_day=demurrage,
        )
        vessels.append(vessel)

    # --- Berths ------------------------------------------------------------
    berths: list[Berth] = []
    for i in range(NUM_BERTHS):
        length = round(_rand_range(*BERTH_LENGTH_RANGE, rng), 1)
        draft = round(_rand_range(*BERTH_DRAFT_RANGE, rng), 1)
        yard_zone_id = f"YZ{(i % NUM_YARD_ZONES) + 1}"
        base_moves = _rand_int(20, 28, rng)

        berth = Berth(
            id=f"B{i + 1:02d}",
            length_m=length,
            max_draft_m=draft,
            crane_ids=[],  # populated after cranes are created
            base_moves_per_hr=base_moves,
            yard_zone_id=yard_zone_id,
            status=BerthStatus.IDLE,
        )
        berths.append(berth)

    # --- Cranes ------------------------------------------------------------
    total_cranes = _rand_int(*NUM_CRANES_RANGE, rng)
    cranes: list[Crane] = []
    crane_idx = 0
    for i in range(total_cranes):
        moves_hr = _rand_int(*CRANE_MOVES_PER_HR_RANGE, rng)
        # Each crane is compatible with 2-4 adjacent berths
        min_berth = max(0, crane_idx % NUM_BERTHS - 1)
        max_berth = min(NUM_BERTHS - 1, min_berth + rng.randint(2, 4))
        compatible = [berths[b].id for b in range(min_berth, max_berth + 1)]

        crane = Crane(
            id=f"QC{i + 1:02d}",
            max_moves_per_hr=moves_hr,
            compatible_berths=compatible,
        )
        cranes.append(crane)
        crane_idx += 1

    # Assign cranes to berths based on compatibility
    for crane in cranes:
        for berth_id in crane.compatible_berths:
            for berth in berths:
                if berth.id == berth_id and crane.id not in berth.crane_ids:
                    berth.crane_ids.append(crane.id)

    # --- Yard zones --------------------------------------------------------
    yard_zones: list[YardZone] = []
    for i in range(NUM_YARD_ZONES):
        capacity = _rand_int(*YARD_TEU_CAPACITY_RANGE, rng)
        util = round(_rand_range(*YARD_INITIAL_UTILIZATION, rng), 3)
        current = int(capacity * util)
        dwell = round(_rand_range(*YARD_DWELL_DAYS_RANGE, rng), 1)

        zone = YardZone(
            id=f"YZ{i + 1}",
            teu_capacity=capacity,
            current_teu=current,
            avg_dwell_days=dwell,
        )
        yard_zones.append(zone)

    # --- Alternate ports ---------------------------------------------------
    alt_ports: list[AltPort] = []
    for i, spec in enumerate(ALT_PORTS):
        port = AltPort(
            id=f"AP{i + 1}",
            name=spec["name"],
            transit_hours=spec["transit_hours"],
            berth_capacity=spec["berth_capacity"],
            handling_premium_usd=spec["handling_premium_usd"],
            congestion_index=spec["congestion_index"],
        )
        alt_ports.append(port)

    # --- Metadata ----------------------------------------------------------
    total_teu_capacity = sum(z.teu_capacity for z in yard_zones)
    total_current_teu = sum(z.current_teu for z in yard_zones)

    meta = {
        "seed": seed,
        "weeks": weeks,
        "as_of_h": as_of_h,
        "arrivals_per_week": arrivals_per_week,
        "total_arrivals": total_arrivals,
        "num_berths": NUM_BERTHS,
        "num_cranes": total_cranes,
        "num_yard_zones": NUM_YARD_ZONES,
        "yard_teu_capacity": total_teu_capacity,
        "yard_current_teu": total_current_teu,
        "yard_util_pct": round(total_current_teu / total_teu_capacity * 100, 1)
        if total_teu_capacity
        else 0.0,
        "num_alt_ports": len(alt_ports),
    }

    return {
        "vessels": vessels,
        "berths": berths,
        "cranes": cranes,
        "yard_zones": yard_zones,
        "alt_ports": alt_ports,
        "meta": meta,
    }


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _entity_to_dict(obj: object) -> dict[str, Any]:
    """Convert a dataclass to a plain dict, handling enums."""
    d = asdict(obj)
    for k, v in d.items():
        if hasattr(v, "value"):
            d[k] = v.value
    return d


def save_scenario(
    scenario: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    """Persist the scenario as JSON files under *output_dir*.

    Returns a mapping of entity name → file path.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    saved: dict[str, Path] = {}
    entity_keys = ["vessels", "berths", "cranes", "yard_zones", "alt_ports"]

    for key in entity_keys:
        items = scenario[key]
        data = [_entity_to_dict(item) for item in items]
        fpath = out / f"{key}.json"
        fpath.write_text(json.dumps(data, indent=2))
        saved[key] = fpath

    # Save meta separately
    meta_path = out / "meta.json"
    meta_path.write_text(json.dumps(scenario["meta"], indent=2))
    saved["meta"] = meta_path

    return saved
