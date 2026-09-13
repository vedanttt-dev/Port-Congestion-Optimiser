"""72-hour shift plan builder (plan.md §3.6 §6-P8).

Converts the optimised berth/crane schedule into **9 shift blocks**
(3 days x 3 shifts of 8 hours each), with per-shift:
  - Work orders (vessel, berth, cranes, target moves, priority)
  - Hotspot alerts
  - Contingency notes
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from app.optimization.solver import BerthAssignment, OptResult


# ---------------------------------------------------------------------------
# Contingency note templates
# ---------------------------------------------------------------------------

CONTINGENCY_TEMPLATES = [
    "Crane breakdown: reallocate cranes from berth {berth} to cover",
    "Weather delay: shift vessel {vessel} to next shift block",
    "Yard overflow: divert incoming containers to zone YZ2",
    "Priority vessel {vessel} arrival: pre-clear berth {berth}",
    "Schedule slippage: vessel {vessel} may need extended crane window",
]


# ---------------------------------------------------------------------------
# Shift plan builder
# ---------------------------------------------------------------------------

class ShiftPlanBuilder:
    """Builds a 72-hour shift plan from optimised assignments.

    Parameters
    ----------
    assignments:
        Optimised berth assignments from :class:`BerthCraneOptimiser`.
    scenario:
        Scenario dict with vessels, berths, yard_zones.
    horizon_h:
        Planning horizon (default 72 = 3 days).
    shift_h:
        Shift duration (default 8 hours).
    """

    def __init__(
        self,
        assignments: list[BerthAssignment],
        scenario: dict[str, Any],
        *,
        horizon_h: float = 72.0,
        shift_h: float = 8.0,
    ) -> None:
        self.assignments = assignments
        self.scenario = scenario
        self.horizon_h = horizon_h
        self.shift_h = shift_h

        self._vessel_map = {v.id: v for v in scenario["vessels"]}
        self._berth_map = {b.id: b for b in scenario["berths"]}
        self._yard_teu = {
            z.id: z.current_teu for z in scenario["yard_zones"]
        }
        self._yard_cap = {
            z.id: z.teu_capacity for z in scenario["yard_zones"]
        }

    def build(self) -> list[dict[str, Any]]:
        """Build the 9-shift plan and return as list of dicts."""
        num_shifts = int(self.horizon_h / self.shift_h)
        shifts: list[dict[str, Any]] = []

        for i in range(num_shifts):
            day = i // 3 + 1
            shift_no = i % 3 + 1
            start_h = i * self.shift_h
            end_h = (i + 1) * self.shift_h
            shift_id = f"D{day}S{shift_no}"

            # Collect active assignments in this shift window
            work_orders = []
            alerts = []
            active_vessels: list[str] = []

            for a in self.assignments:
                # Check if this assignment overlaps the shift
                if a.start_h < end_h and a.end_h > start_h:
                    vessel = self._vessel_map.get(a.vessel_id)
                    if not vessel:
                        continue

                    # Calculate moves for this shift
                    total_svc = max(1, a.end_h - a.start_h)
                    overlap_start = max(start_h, a.start_h)
                    overlap_end = min(end_h, a.end_h)
                    shift_fraction = (overlap_end - overlap_start) / total_svc
                    target_moves = int(a.moves_planned * shift_fraction)

                    work_orders.append({
                        "vessel_id": a.vessel_id,
                        "vessel_name": vessel.name,
                        "berth_id": a.berth_id,
                        "crane_ids": [f"QC{i}" for i in range(1, a.crane_count + 1)],
                        "target_moves": target_moves,
                        "priority": vessel.priority_class,
                        "alert": "High priority" if vessel.priority_class == 1 else "",
                    })
                    active_vessels.append(a.vessel_id)

                    # Check for delays
                    if a.wait_h > 24:
                        alerts.append(
                            f"Vessel {a.vessel_id} ({vessel.name}) waited {a.wait_h:.1f}h"
                        )

            # Generate hotspot alerts
            hotspot_alerts = self._detect_shift_hotspots(start_h, end_h, active_vessels)
            alerts.extend(hotspot_alerts)

            # Generate contingency notes
            contingency = self._generate_contingencies(
                start_h, end_h, work_orders, shift_id
            )

            shifts.append({
                "id": shift_id,
                "day": day,
                "shift_no": shift_no,
                "window": f"h{start_h:.0f}-h{end_h:.0f}",
                "start_h": start_h,
                "end_h": end_h,
                "alerts": alerts,
                "work_orders": work_orders,
                "contingency_notes": contingency,
                "vessel_count": len(work_orders),
            })

        return shifts

    def _detect_shift_hotspots(
        self, start_h: float, end_h: float, active_vessels: list[str]
    ) -> list[str]:
        """Detect hotspot conditions within a shift window."""
        alerts = []

        # Yard utilisation check
        total_teu = sum(self._yard_teu.values())
        total_cap = sum(self._yard_cap.values())
        if total_cap > 0:
            yard_pct = total_teu / total_cap * 100
            if yard_pct > 90:
                alerts.append(f"HIGH YARD ALERT: {yard_pct:.0f}% utilisation — risk of overflow")
            elif yard_pct > 85:
                alerts.append(f"YARD WARNING: {yard_pct:.0f}% utilisation approaching capacity")

        # Berth congestion check
        active_berths = len(set(
            a.berth_id for a in self.assignments
            if a.start_h < end_h and a.end_h > start_h
        ))
        total_berths = len(self.scenario["berths"])
        if total_berths > 0:
            berth_pct = active_berths / total_berths * 100
            if berth_pct > 85:
                alerts.append(
                    f"BERTH CONGESTION: {active_berths}/{total_berths} berths occupied"
                )

        # High vessel count
        if len(active_vessels) > total_berths * 1.5:
            alerts.append(
                f"QUEUE WARNING: {len(active_vessels)} vessels active, "
                f"exceeds berth capacity"
            )

        return alerts

    def _generate_contingencies(
        self,
        start_h: float,
        end_h: float,
        work_orders: list[dict],
        shift_id: str,
    ) -> list[str]:
        """Generate contingency notes based on current shift conditions."""
        notes = []

        # Check for crane-heavy workload
        total_cranes = sum(len(wo.get("crane_ids", [])) for wo in work_orders)
        if total_cranes > 20:
            notes.append(
                "Contingency: High crane utilisation — standby extra crane operators"
            )

        # Check for high-priority vessels
        priority_count = sum(1 for wo in work_orders if wo.get("priority") == 1)
        if priority_count > 0:
            notes.append(
                f"Contingency: {priority_count} high-priority vessel(s) in shift — "
                f"ensure no crane downtime"
            )

        # Yard pressure
        total_teu = sum(self._yard_teu.values())
        total_cap = sum(self._yard_cap.values())
        if total_cap > 0 and total_teu / total_cap > 0.80:
            notes.append(
                "Contingency: Yard approaching capacity — pre-arrange off-dock staging"
            )

        # Heavy shift
        if len(work_orders) > 8:
            notes.append(
                "Contingency: Heavy shift — consider splitting crane gangs"
            )

        if not notes:
            notes.append("No special contingencies required for this shift")

        return notes


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def shift_plan_to_csv(shifts: list[dict[str, Any]]) -> str:
    """Convert shift plan to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "shift_id", "day", "shift_no", "window", "vessel_count",
        "vessel_id", "vessel_name", "berth_id", "cranes", "target_moves",
        "priority", "alert", "contingency",
    ])

    for shift in shifts:
        if not shift["work_orders"]:
            writer.writerow([
                shift["id"], shift["day"], shift["shift_no"], shift["window"],
                0, "", "", "", "", "", "", "",
                "; ".join(shift["contingency_notes"]),
            ])
        else:
            for wo in shift["work_orders"]:
                writer.writerow([
                    shift["id"], shift["day"], shift["shift_no"], shift["window"],
                    shift["vessel_count"],
                    wo["vessel_id"], wo["vessel_name"], wo["berth_id"],
                    ";".join(wo.get("crane_ids", [])),
                    wo["target_moves"], wo["priority"],
                    wo.get("alert", ""),
                    "; ".join(shift["contingency_notes"]),
                ])

    return output.getvalue()


def save_shift_plan_csv(
    shifts: list[dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """Save shift plan to a CSV file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(shift_plan_to_csv(shifts))
    return path
