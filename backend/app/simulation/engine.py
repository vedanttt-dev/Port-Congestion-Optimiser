"""Discrete-event simulation engine using simpy (plan.md §3.2).

Models the FCFS (first-come-first-served) baseline policy for a container
terminal:  arrival → anchorage queue → berth assignment → crane work →
yard check → departure.

Usage::

    from app.data.generator import generate_scenario
    from app.simulation.engine import SimulationEngine

    scenario = generate_scenario(seed=42, weeks=4)
    engine = SimulationEngine(scenario)
    result = engine.run()
"""

from __future__ import annotations

import dataclasses
import enum
import heapq
import random
from typing import Any

import simpy

from app.domain.entities import Berth, Crane, Vessel, VesselStatus, YardZone


# ---------------------------------------------------------------------------
# Event log entry
# ---------------------------------------------------------------------------

class EventType(str, enum.Enum):
    ARRIVAL = "arrival"
    ANCHORAGE_JOIN = "anchorage_join"
    ANCHORAGE_DEPART = "anchorage_depart"
    BERTH_ASSIGN = "berth_assign"
    CRANE_START = "crane_start"
    CRANE_DONE = "crane_done"
    YARD_CHECK = "yard_check"
    DEPARTURE = "departure"
    BERTH_RELEASE = "berth_release"


@dataclasses.dataclass
class SimEvent:
    time_h: float
    event_type: EventType
    vessel_id: str
    berth_id: str = ""
    crane_ids: list[str] = dataclasses.field(default_factory=list)
    detail: str = ""


# ---------------------------------------------------------------------------
# Vessel runtime state (not persisted — tracks sim-time status)
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class VesselState:
    vessel: Vessel
    arrived_h: float = -1.0
    berth_assigned_h: float = -1.0
    service_start_h: float = -1.0
    service_end_h: float = -1.0
    departed_h: float = -1.0
    wait_h: float = 0.0
    assigned_berth: str = ""
    assigned_cranes: list[str] = dataclasses.field(default_factory=list)
    total_moves: int = 0


# ---------------------------------------------------------------------------
# Simulation engine
# ---------------------------------------------------------------------------

class SimulationEngine:
    """Simpy-based discrete-event simulation of a container terminal.

    Parameters
    ----------
    scenario:
        Output of :func:`app.data.generator.generate_scenario`.
    seed:
        Random seed for simpy and internal RNG.
    horizon_h:
        Maximum simulation time in hours.
    """

    def __init__(
        self,
        scenario: dict[str, Any],
        *,
        seed: int = 42,
        horizon_h: float = 672.0,
    ) -> None:
        self.env = simpy.Environment()
        self.rng = random.Random(seed)
        self.seed = seed
        self.horizon_h = horizon_h

        # Copy entities from scenario
        self.vessels: list[Vessel] = list(scenario["vessels"])
        self.berths: list[Berth] = list(scenario["berths"])
        self.cranes: list[Crane] = list(scenario["cranes"])
        self.yard_zones: list[YardZone] = list(scenario["yard_zones"])

        # Lookup maps
        self._berth_map: dict[str, Berth] = {b.id: b for b in self.berths}
        self._crane_map: dict[str, Crane] = {c.id: c for c in self.cranes}
        self._yard_map: dict[str, YardZone] = {z.id: z for z in self.yard_zones}

        # Simpy resources
        self.berth_resources = {
            b.id: simpy.Resource(self.env, capacity=1) for b in self.berths
        }
        self.crane_resources: dict[str, simpy.Resource] = {}
        for crane in self.cranes:
            # Each crane is a single unit; modelled as a Resource per berth
            # that crane serves.  Instead, we track crane availability via
            # a shared pool per compatible-berth set (simplified: per-berth
            # crane count limit).
            pass  # handled via berth-level crane capacity tracking

        # Runtime state
        self.vessel_states: dict[str, VesselState] = {
            v.id: VesselState(vessel=v) for v in self.vessels
        }
        self.events: list[SimEvent] = []
        self._queue_samples: list[tuple[float, int]] = []  # (time_h, queue_size)
        self._berth_busy: dict[str, list[tuple[float, float]]] = {
            b.id: [] for b in self.berths
        }  # berth_id -> [(start_h, end_h)]
        self._crane_busy: dict[str, list[tuple[float, float]]] = {
            c.id: [] for c in self.cranes
        }
        self._crane_berth_usage: dict[str, int] = {b.id: 0 for b in self.berths}
        self._yard_teu: dict[str, int] = {
            z.id: z.current_teu for z in self.yard_zones
        }
        self._queue_length = 0

        # Sort vessels by ETA for processing
        self.vessels.sort(key=lambda v: v.eta_h)

    # ------------------------------------------------------------------
    # FCFS berth assignment
    # ------------------------------------------------------------------

    def _find_berth_fcfs(self, vessel: Vessel) -> Berth | None:
        """Find the first available berth that fits the vessel (FCFS).

        Checks length, draft, and crane availability.
        """
        for berth in self.berths:
            if berth.status.value == "maintenance":
                continue
            if vessel.loa_m > berth.length_m:
                continue
            if vessel.draft_m > berth.max_draft_m:
                continue
            # Check if berth is idle (no vessels currently berthed)
            if self._crane_berth_usage[berth.id] > 0:
                continue
            # Check crane availability for this berth
            available_cranes = [
                cid for cid in berth.crane_ids
                if self._crane_berth_usage[berth.id] == 0
            ]
            if not available_cranes:
                continue
            return berth
        return None

    def _assign_cranes(self, berth: Berth, vessel: Vessel) -> list[str]:
        """Assign cranes to a vessel at a berth (FCFS, min 2)."""
        crane_count = min(2 + vessel.teu_capacity // 8000, len(berth.crane_ids))
        crane_count = max(2, min(crane_count, len(berth.crane_ids)))
        return berth.crane_ids[:crane_count]

    # ------------------------------------------------------------------
    # Yard capacity check
    # ------------------------------------------------------------------

    def _yard_available(self, yard_zone_id: str, teu_needed: int) -> bool:
        """Check if yard zone has capacity for the vessel's containers."""
        zone = self._yard_map.get(yard_zone_id)
        if not zone:
            return False
        return self._yard_teu[yard_zone_id] + teu_needed <= zone.teu_capacity

    def _yard_add(self, yard_zone_id: str, teu: int) -> None:
        self._yard_teu[yard_zone_id] = min(
            self._yard_teu[yard_zone_id] + teu,
            self._yard_map[yard_zone_id].teu_capacity,
        )

    def _yard_remove(self, yard_zone_id: str, teu: int) -> None:
        self._yard_teu[yard_zone_id] = max(
            self._yard_teu[yard_zone_id] - teu, 0
        )

    # ------------------------------------------------------------------
    # Simpy processes
    # ------------------------------------------------------------------

    def _vessel_process(self, vessel: Vessel) -> None:  # type: ignore[no-untyped-def]
        """Full lifecycle of a single vessel."""
        vs = self.vessel_states[vessel.id]

        # 1. Arrival
        yield self.env.timeout(max(0, vessel.eta_h - self.env.now))
        vs.arrived_h = self.env.now
        vessel.status = VesselStatus.INBOUND
        self._log(EventType.ARRIVAL, vessel, detail=f"ETA={vessel.eta_h:.1f}h")

        # 2. Join anchorage queue
        vessel.status = VesselStatus.ANCHORAGE
        self._queue_length += 1
        self._queue_samples.append((self.env.now, self._queue_length))
        self._log(EventType.ANCHORAGE_JOIN, vessel, detail=f"queue={self._queue_length}")

        # 3. Wait for berth (FCFS)
        while True:
            berth = self._find_berth_fcfs(vessel)
            if berth is not None:
                # Request the berth resource (capacity=1)
                with self.berth_resources[berth.id].request() as req:
                    yield req  # wait until berth is free
                    # Double-check berth is still suitable
                    if self._crane_berth_usage[berth.id] == 0:
                        break
            # No berth available — wait and retry
            yield self.env.timeout(0.5)

        # 4. Berth assigned
        vessel.status = VesselStatus.BERTHED
        vs.berth_assigned_h = self.env.now
        vs.wait_h = self.env.now - vessel.eta_h
        vs.assigned_berth = berth.id

        cranes_assigned = self._assign_cranes(berth, vessel)
        vs.assigned_cranes = cranes_assigned
        vs.total_moves = vessel.import_moves + vessel.export_moves

        self._queue_length -= 1
        self._queue_samples.append((self.env.now, self._queue_length))
        self._crane_berth_usage[berth.id] = len(cranes_assigned)

        self._log(
            EventType.BERTH_ASSIGN, vessel,
            berth_id=berth.id,
            crane_ids=cranes_assigned,
            detail=f"wait={vs.wait_h:.1f}h, moves={vs.total_moves}",
        )

        # 5. Yard check
        teu_needed = vessel.teu_capacity // 2  # import half
        if not self._yard_available(berth.yard_zone_id, teu_needed):
            # Wait until yard has space
            while not self._yard_available(berth.yard_zone_id, teu_needed):
                yield self.env.timeout(1.0)
        self._yard_add(berth.yard_zone_id, teu_needed)
        self._log(
            EventType.YARD_CHECK, vessel,
            berth_id=berth.id,
            detail=f"yard_zone={berth.yard_zone_id}, +{teu_needed}TEU",
        )

        # 6. Crane work
        vs.service_start_h = self.env.now
        self._log(
            EventType.CRANE_START, vessel,
            berth_id=berth.id,
            crane_ids=cranes_assigned,
        )

        # Calculate service time based on moves and crane throughput
        total_crane_rate = sum(
            self._crane_map[cid].max_moves_per_hr for cid in cranes_assigned
        )
        total_crane_rate = max(total_crane_rate, 1)
        service_time = vs.total_moves / total_crane_rate

        # Add some random variability (±15%)
        service_time *= self.rng.uniform(0.85, 1.15)

        # Record crane busy intervals
        for cid in cranes_assigned:
            self._crane_busy[cid].append((self.env.now, self.env.now + service_time))

        yield self.env.timeout(service_time)

        vs.service_end_h = self.env.now
        self._log(
            EventType.CRANE_DONE, vessel,
            berth_id=berth.id,
            crane_ids=cranes_assigned,
            detail=f"service={service_time:.1f}h",
        )

        # 7. Yard release (dwell time)
        dwell_h = self._yard_map[berth.yard_zone_id].avg_dwell_days * 24
        yield self.env.timeout(dwell_h)
        self._yard_remove(berth.yard_zone_id, teu_needed)

        # 8. Departure
        vessel.status = VesselStatus.OUTBOUND
        vs.departed_h = self.env.now
        self._log(EventType.DEPARTURE, vessel, berth_id=berth.id)

        # 9. Release berth
        self._crane_berth_usage[berth.id] = 0
        self._berth_busy[berth.id].append((vs.berth_assigned_h, self.env.now))
        self._log(EventType.BERTH_RELEASE, vessel, berth_id=berth.id)

    def _log(
        self,
        event_type: EventType,
        vessel: Vessel,
        berth_id: str = "",
        crane_ids: list[str] | None = None,
        detail: str = "",
    ) -> None:
        self.events.append(SimEvent(
            time_h=self.env.now,
            event_type=event_type,
            vessel_id=vessel.id,
            berth_id=berth_id,
            crane_ids=crane_ids or [],
            detail=detail,
        ))

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self) -> SimulationResult:
        """Run the simulation and return results."""
        # Schedule all vessel processes
        for vessel in self.vessels:
            self.env.process(self._vessel_process(vessel))

        # Run until horizon
        self.env.run(until=self.horizon_h)

        return SimulationResult(
            events=self.events,
            vessel_states=self.vessel_states,
            queue_samples=self._queue_samples,
            berth_busy=self._berth_busy,
            crane_busy=self._crane_busy,
            yard_teu=self._yard_teu,
            seed=self.seed,
            horizon_h=self.horizon_h,
        )


# ---------------------------------------------------------------------------
# Simulation result container
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class SimulationResult:
    """Raw output of a simulation run."""
    events: list[SimEvent]
    vessel_states: dict[str, VesselState]
    queue_samples: list[tuple[float, int]]
    berth_busy: dict[str, list[tuple[float, float]]]
    crane_busy: dict[str, list[tuple[float, float]]]
    yard_teu: dict[str, int]
    seed: int
    horizon_h: float
