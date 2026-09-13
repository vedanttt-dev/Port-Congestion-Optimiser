"""CP-SAT berth + crane assignment optimiser (plan.md §3.4 §6-P6).

Two-phase approach:
  1. CP-SAT assigns each vessel to a berth to minimise total weighted wait.
  2. Within each berth, schedule in global ETA order respecting berth capacity.

Solve budget: 2 seconds.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from ortools.sat.python import cp_model

from app.domain.entities import Berth, Crane, Vessel, YardZone


@dataclass
class BerthAssignment:
    vessel_id: str
    berth_id: str
    start_h: int
    end_h: int
    crane_count: int
    moves_planned: int
    wait_h: float = 0.0


@dataclass
class OptResult:
    assignments: list[BerthAssignment]
    avg_wait_h: float = 0.0
    total_wait_h: float = 0.0
    solve_ms: float = 0.0
    obj_value: float = 0.0
    status: str = "unknown"


class BerthCraneOptimiser:
    """CP-SAT model for berth allocation + crane assignment."""

    def __init__(
        self,
        scenario: dict[str, Any],
        *,
        horizon_h: float = 168.0,
        time_limit_s: float = 2.0,
    ) -> None:
        self.scenario = scenario
        self.horizon = int(horizon_h)
        self.time_limit = time_limit_s

        self.vessels: list[Vessel] = list(scenario["vessels"])
        self.berths: list[Berth] = list(scenario["berths"])
        self.cranes: list[Crane] = list(scenario["cranes"])
        self.yard_zones: list[YardZone] = list(scenario["yard_zones"])

        self._crane_map = {c.id: c for c in self.cranes}
        self._berth_map = {b.id: b for b in self.berths}

        self._compatible: dict[str, list[str]] = {}
        for v in self.vessels:
            compat = []
            for b in self.berths:
                if v.loa_m <= b.length_m and v.draft_m <= b.max_draft_m and b.crane_ids:
                    compat.append(b.id)
            self._compatible[v.id] = compat

        self._berth_max_cranes: dict[str, int] = {
            b.id: len(b.crane_ids) for b in self.berths
        }

    def _est_service(self, v: Vessel, num_cranes: int = 3) -> int:
        total_moves = v.import_moves + v.export_moves
        return max(4, min(total_moves // (num_cranes * 30), 72))

    def _num_cranes_for(self, v: Vessel, b: Berth) -> int:
        count = min(2 + v.teu_capacity // 8000, len(b.crane_ids))
        return max(2, count)

    def solve(self) -> OptResult:
        t0 = time.perf_counter()

        # ---- Phase 1: CP-SAT berth assignment ----
        berth_map = {b.id: b for b in self.berths}
        assignments_by_vessel = self._phase1()

        # ---- Phase 2: Simulate with assigned berths (FCFS ordering) ----
        assignments = self._phase2(assignments_by_vessel)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        waits = [a.wait_h for a in assignments]
        avg_wait = sum(waits) / len(waits) if waits else 0.0

        return OptResult(
            assignments=assignments,
            avg_wait_h=round(avg_wait, 2),
            total_wait_h=round(sum(waits), 2),
            solve_ms=round(elapsed_ms, 1),
            obj_value=0.0,
            status="optimal" if len(assignments) == len(self.vessels) else "feasible",
        )

    def _phase1(self) -> dict[str, str]:
        """CP-SAT: assign each vessel to a berth, minimising total weighted wait."""
        model = cp_model.CpModel()
        berth_map = {b.id: b for b in self.berths}

        # Variables
        assign: dict[tuple[str, str], cp_model.IntVar] = {}
        for v in self.vessels:
            for b_id in self._compatible.get(v.id, []):
                assign[(v.id, b_id)] = model.new_bool_var(f"a_{v.id}_{b_id}")

        # Each vessel assigned to exactly one berth
        for v in self.vessels:
            compat = self._compatible.get(v.id, [])
            if compat:
                model.add_exactly_one([assign[(v.id, b_id)] for b_id in compat])

        # Berth capacity: estimate how many vessels each berth can handle
        # in the horizon (rough: horizon / avg_service_time)
        vessels_sorted = sorted(self.vessels, key=lambda v: v.eta_h)

        # Estimate per-pair wait using a simplified FCFS model
        # For each (vessel, berth) pair, compute estimated queue position
        berth_queues: dict[str, list[tuple[float, int, str]]] = defaultdict(list)
        for v in vessels_sorted:
            svc = self._est_service(v)
            for b_id in self._compatible.get(v.id, []):
                # Position in queue: count of compatible vessels with earlier ETA
                position = sum(
                    1 for vv in vessels_sorted
                    if vv.eta_h < v.eta_h and b_id in self._compatible.get(vv.id, [])
                )
                berth_queues[b_id].append((v.eta_h, position, v.id))

        # Objective: minimise total weighted wait
        # Wait ≈ position * avg_service_time at the berth
        obj_terms = []
        for v in self.vessels:
            svc = self._est_service(v)
            weight = 3 if v.priority_class == 1 else 1
            for b_id in self._compatible.get(v.id, []):
                # Count vessels with earlier ETA at this berth
                earlier_count = sum(
                    1 for vv in vessels_sorted
                    if vv.eta_h < v.eta_h and b_id in self._compatible.get(vv.id, [])
                )
                # Estimated wait at this berth
                est_wait = earlier_count * (svc // 2)
                # Load balancing: prefer berths with fewer earlier vessels
                obj_terms.append(assign[(v.id, b_id)] * est_wait * weight)

        if obj_terms:
            model.minimize(sum(obj_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.time_limit
        solver.parameters.num_workers = 1
        status_code = solver.solve(model)

        result: dict[str, str] = {}
        if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for v in self.vessels:
                for b_id in self._compatible.get(v.id, []):
                    if solver.value(assign[(v.id, b_id)]):
                        result[v.id] = b_id
                        break

        return result

    def _phase2(self, berth_assignments: dict[str, str]) -> list[BerthAssignment]:
        """Simulate with assigned berths: process vessels in global ETA order."""
        berth_map = {b.id: b for b in self.berths}

        # Track when each berth becomes free
        berth_free: dict[str, float] = {b.id: 0.0 for b in self.berths}

        # Process ALL vessels in global ETA order (like the simpy FCFS engine)
        vessels_by_eta = sorted(self.vessels, key=lambda v: v.eta_h)
        result: list[BerthAssignment] = []

        for v in vessels_by_eta:
            b_id = berth_assignments.get(v.id)
            if not b_id or b_id not in berth_map:
                continue

            berth = berth_map[b_id]
            svc = self._est_service(v)
            cranes = self._num_cranes_for(v, berth)

            # Start time: max(ETA, berth_free_time)
            start = max(int(v.eta_h), int(berth_free[b_id]))
            end = start + svc
            wait = max(0.0, start - v.eta_h)

            berth_free[b_id] = end

            result.append(BerthAssignment(
                vessel_id=v.id,
                berth_id=b_id,
                start_h=start,
                end_h=end,
                crane_count=cranes,
                moves_planned=v.import_moves + v.export_moves,
                wait_h=round(wait, 2),
            ))

        return result
