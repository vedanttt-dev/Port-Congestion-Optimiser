"""KPI computation from simulation results (plan.md §9).

Computes: avg wait, p95 wait, max queue, berth/crane/yard utilisation,
demurrage cost from a :class:`SimulationResult`.
"""

from __future__ import annotations

import csv
import io
import statistics
from pathlib import Path
from typing import Any

from app.domain.entities import KpiSnapshot

from .engine import SimulationResult


def compute_kpis(result: SimulationResult, scenario: dict[str, Any]) -> KpiSnapshot:
    """Derive KPI metrics from a simulation run.

    Parameters
    ----------
    result:
        Raw output of :meth:`SimulationEngine.run`.
    scenario:
        The original scenario dict (for entity metadata).

    Returns
    -------
    KpiSnapshot with all metrics populated.
    """
    vessel_states = result.vessel_states
    berths = scenario["berths"]
    cranes = scenario["cranes"]
    yard_zones = scenario["yard_zones"]
    horizon_h = result.horizon_h

    # --- Wait times -------------------------------------------------------
    waits = [vs.wait_h for vs in vessel_states.values() if vs.arrived_h >= 0]
    avg_wait = statistics.mean(waits) if waits else 0.0
    p95_wait = (
        sorted(waits)[int(len(waits) * 0.95)] if len(waits) >= 2 else avg_wait
    )

    # --- Max queue --------------------------------------------------------
    max_queue = max((qs[1] for qs in result.queue_samples), default=0)

    # --- Berth utilisation ------------------------------------------------
    total_berth_hours = len(berths) * horizon_h
    used_berth_hours = sum(
        end - start
        for intervals in result.berth_busy.values()
        for start, end in intervals
    )
    berth_util = (used_berth_hours / total_berth_hours * 100) if total_berth_hours else 0.0

    # --- Crane utilisation ------------------------------------------------
    total_crane_hours = len(cranes) * horizon_h
    used_crane_hours = sum(
        end - start
        for intervals in result.crane_busy.values()
        for start, end in intervals
    )
    crane_util = (used_crane_hours / total_crane_hours * 100) if total_crane_hours else 0.0

    # --- Yard utilisation (peak) -----------------------------------------
    yard_capacity = sum(z.teu_capacity for z in yard_zones)
    yard_current = sum(result.yard_teu.get(z.id, z.current_teu) for z in yard_zones)
    yard_util = (yard_current / yard_capacity * 100) if yard_capacity else 0.0

    # --- Demurrage cost ---------------------------------------------------
    demurrage_cost = 0.0
    for vs in vessel_states.values():
        if vs.wait_h > 0:
            daily_rate = vs.vessel.demurrage_usd_per_day
            demurrage_cost += (vs.wait_h / 24) * daily_rate

    return KpiSnapshot(
        avg_wait_h=round(avg_wait, 2),
        p95_wait_h=round(p95_wait, 2),
        max_queue=max_queue,
        berth_util_pct=round(berth_util, 1),
        crane_util_pct=round(crane_util, 1),
        yard_util_pct=round(yard_util, 1),
        demurrage_cost_usd=round(demurrage_cost, 2),
    )


def format_kpi_report(kpis: KpiSnapshot, scenario: dict[str, Any]) -> str:
    """Return a human-readable KPI report string."""
    meta = scenario["meta"]
    lines = [
        "=" * 60,
        "  BASELINE FCFS — SIMULATION KPI REPORT",
        "=" * 60,
        f"  Seed             : {meta['seed']}",
        f"  Simulation weeks : {meta['weeks']}",
        f"  Total vessels    : {meta['total_arrivals']}",
        f"  Berths           : {meta['num_berths']}",
        f"  Cranes           : {meta['num_cranes']}",
        f"  Yard capacity    : {meta['yard_teu_capacity']:,} TEU",
        "-" * 60,
        f"  Avg anchorage wait   : {kpis.avg_wait_h:>8.1f} h",
        f"  P95 anchorage wait   : {kpis.p95_wait_h:>8.1f} h",
        f"  Max queue size       : {kpis.max_queue:>8d}",
        f"  Berth utilisation    : {kpis.berth_util_pct:>7.1f} %",
        f"  Crane utilisation    : {kpis.crane_util_pct:>7.1f} %",
        f"  Yard utilisation     : {kpis.yard_util_pct:>7.1f} %",
        f"  Demurrage cost       : ${kpis.demurrage_cost_usd:>14,.2f}",
        "=" * 60,
    ]
    return "\n".join(lines)


def kpis_to_dict(kpis: KpiSnapshot) -> dict[str, Any]:
    """Convert KpiSnapshot to a plain dict."""
    return {
        "avg_wait_h": kpis.avg_wait_h,
        "p95_wait_h": kpis.p95_wait_h,
        "max_queue": kpis.max_queue,
        "berth_util_pct": kpis.berth_util_pct,
        "crane_util_pct": kpis.crane_util_pct,
        "yard_util_pct": kpis.yard_util_pct,
        "demurrage_cost_usd": kpis.demurrage_cost_usd,
    }


def save_kpi_csv(
    result: SimulationResult,
    kpis: KpiSnapshot,
    output_dir: str | Path,
) -> Path:
    """Save KPI summary + per-vessel data as CSV files.

    Returns the path to the KPI summary CSV.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1. KPI summary CSV
    kpi_path = out / "kpis.csv"
    with open(kpi_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["avg_wait_h", kpis.avg_wait_h])
        writer.writerow(["p95_wait_h", kpis.p95_wait_h])
        writer.writerow(["max_queue", kpis.max_queue])
        writer.writerow(["berth_util_pct", kpis.berth_util_pct])
        writer.writerow(["crane_util_pct", kpis.crane_util_pct])
        writer.writerow(["yard_util_pct", kpis.yard_util_pct])
        writer.writerow(["demurrage_cost_usd", kpis.demurrage_cost_usd])

    # 2. Per-vessel CSV
    vessel_path = out / "vessel_results.csv"
    with open(vessel_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "vessel_id", "name", "type", "teu", "priority",
            "eta_h", "arrived_h", "berth_assigned_h", "wait_h",
            "berth_id", "crane_ids", "total_moves",
            "service_start_h", "service_end_h", "departed_h",
        ])
        for vs in result.vessel_states.values():
            writer.writerow([
                vs.vessel.id, vs.vessel.name, vs.vessel.type.value,
                vs.vessel.teu_capacity, vs.vessel.priority_class,
                vs.vessel.eta_h, vs.arrived_h, vs.berth_assigned_h,
                round(vs.wait_h, 2), vs.assigned_berth,
                ";".join(vs.assigned_cranes), vs.total_moves,
                vs.service_start_h, vs.service_end_h, vs.departed_h,
            ])

    return kpi_path
