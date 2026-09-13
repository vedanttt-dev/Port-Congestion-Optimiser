"""Forward simulation predictor (plan.md §3.3).

Runs a lightweight forward simulation from ``as_of_h`` using the planned
arrivals + current queue to predict per-vessel waits, berth/yard utilisation
in 4-hour buckets, and overall congestion trajectory.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from app.domain.entities import Berth, Crane, Vessel, VesselStatus, YardZone


# ---------------------------------------------------------------------------
# Prediction result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class VesselPrediction:
    vessel_id: str
    name: str
    vessel_type: str
    eta_h: float
    teu_capacity: int
    priority: int
    predicted_wait_h: float = 0.0
    predicted_berth_h: float = 0.0
    predicted_start_h: float = 0.0
    predicted_end_h: float = 0.0
    assigned_berth: str = ""
    status: str = "pending"


@dataclass
class BucketUtil:
    h: float
    util_pct: float


@dataclass
class BerthUtilPrediction:
    berth_id: str
    buckets: list[BucketUtil] = field(default_factory=list)


@dataclass
class QueuePrediction:
    h: float
    queue_size: int = 0


@dataclass
class YardUtilPrediction:
    h: float
    util_pct: float = 0.0


@dataclass
class ForwardResult:
    vessel_predictions: list[VesselPrediction]
    berth_util: list[BerthUtilPrediction]
    queue_forecast: list[QueuePrediction]
    yard_forecast: list[YardUtilPrediction]
    max_queue: int = 0
    avg_wait_h: float = 0.0


# ---------------------------------------------------------------------------
# Forward simulator
# ---------------------------------------------------------------------------

class ForwardSimulator:
    """Lightweight forward simulation from ``as_of_h``.

    Uses a simple queueing model: vessels arrive at ETA, wait in queue,
    get assigned to the first available compatible berth (FCFS), and depart
    after service time.

    Parameters
    ----------
    scenario:
        The scenario dict (vessels, berths, cranes, yard_zones).
    as_of_h:
        Current simulation hour (prediction start time).
    horizon_h:
        How far ahead to predict (default 168h = 7 days).
    bucket_h:
        Bucket size for utilisation forecasts (default 4h).
    """

    def __init__(
        self,
        scenario: dict[str, Any],
        as_of_h: float = 0.0,
        horizon_h: float = 168.0,
        bucket_h: float = 4.0,
    ) -> None:
        self.scenario = scenario
        self.as_of_h = as_of_h
        self.horizon_h = horizon_h
        self.bucket_h = bucket_h
        self.rng = random.Random(42)

        self.berths: list[Berth] = list(scenario["berths"])
        self.cranes: list[Crane] = list(scenario["cranes"])
        self.yard_zones: list[YardZone] = list(scenario["yard_zones"])

        self._berth_map = {b.id: b for b in self.berths}
        self._crane_map = {c.id: c for c in self.cranes}

        # Berth free-from time: when each berth becomes available
        self._berth_free: dict[str, float] = {b.id: as_of_h for b in self.berths}
        # Crane count available per berth (from berth.crane_ids)
        self._berth_cranes: dict[str, list[str]] = {
            b.id: list(b.crane_ids) for b in self.berths
        }
        # Yard current TEU
        self._yard_teu: dict[str, int] = {
            z.id: z.current_teu for z in self.yard_zones
        }

    def _find_berth(self, vessel: Vessel) -> str | None:
        """Find first available compatible berth (FCFS)."""
        for berth in self.berths:
            if vessel.loa_m > berth.length_m:
                continue
            if vessel.draft_m > berth.max_draft_m:
                continue
            if not berth.crane_ids:
                continue
            return berth.id
        return None

    def _assign_cranes(self, berth_id: str, vessel: Vessel) -> list[str]:
        """Assign cranes to vessel (min 2, scaled by TEU)."""
        available = self._berth_cranes.get(berth_id, [])
        count = min(2 + vessel.teu_capacity // 8000, len(available))
        count = max(2, min(count, len(available)))
        return available[:count]

    def _service_time(self, vessel: Vessel, crane_ids: list[str]) -> float:
        """Estimate service time based on moves and crane throughput."""
        total_moves = vessel.import_moves + vessel.export_moves
        crane_rate = sum(
            self._crane_map[cid].max_moves_per_hr
            for cid in crane_ids if cid in self._crane_map
        )
        crane_rate = max(crane_rate, 1)
        return (total_moves / crane_rate) * self.rng.uniform(0.85, 1.15)

    def run(self) -> ForwardResult:
        """Run the forward simulation and return predictions."""
        # Get vessels that haven't departed yet at as_of_h
        future_vessels = [
            v for v in self.scenario["vessels"]
            if v.eta_h >= self.as_of_h - 24  # include recently arrived (within 24h)
        ]
        future_vessels.sort(key=lambda v: v.eta_h)

        predictions: list[VesselPrediction] = []
        berth_events: dict[str, list[tuple[float, float]]] = {
            b.id: [] for b in self.berths
        }
        queue_snapshots: list[tuple[float, int]] = []

        queue: list[VesselPrediction] = []

        for vessel in future_vessels:
            vp = VesselPrediction(
                vessel_id=vessel.id,
                name=vessel.name,
                vessel_type=vessel.type.value,
                eta_h=vessel.eta_h,
                teu_capacity=vessel.teu_capacity,
                priority=vessel.priority_class,
            )

            # Wait until ETA
            current_time = max(vessel.eta_h, self.as_of_h)

            # Find berth
            berth_id = self._find_berth(vessel)
            if berth_id is None:
                # No compatible berth — add to queue
                queue.append(vp)
                queue_snapshots.append((current_time, len(queue)))
                continue

            # Wait for berth to be free
            berth_free_at = self._berth_free[berth_id]
            wait = max(0, berth_free_at - current_time)
            vp.predicted_wait_h = round(wait, 2)
            vp.assigned_berth = berth_id

            start_h = max(current_time, berth_free_at)
            vp.predicted_start_h = round(start_h, 2)

            # Assign cranes and compute service time
            crane_ids = self._assign_cranes(berth_id, vessel)
            service_t = self._service_time(vessel, crane_ids)
            vp.predicted_berth_h = round(service_t, 2)
            vp.predicted_end_h = round(start_h + service_t, 2)
            vp.status = "berthed"

            # Update berth free time
            self._berth_free[berth_id] = start_h + service_t
            berth_events[berth_id].append((start_h, start_h + service_t))

            # Yard update
            teu_needed = vessel.teu_capacity // 2
            zone_id = self._berth_map[berth_id].yard_zone_id
            self._yard_teu[zone_id] = min(
                self._yard_teu[zone_id] + teu_needed,
                self._yard_map_capacity(zone_id),
            )
            # Release after dwell (3 days average)
            dwell_h = 72.0
            self._yard_teu[zone_id] = max(
                self._yard_teu[zone_id] - teu_needed, 0
            )

            predictions.append(vp)

            # Snapshot queue
            queue_snapshots.append((current_time, len(queue)))

        # Process remaining queue (vessels that arrived but no berth)
        for vp in queue:
            # Try to assign from freed berths
            for berth in self.berths:
                vessel = next(
                    (v for v in self.scenario["vessels"] if v.id == vp.vessel_id),
                    None,
                )
                if vessel is None:
                    continue
                if vessel.loa_m > berth.length_m or vessel.draft_m > berth.max_draft_m:
                    continue
                if not berth.crane_ids:
                    continue

                berth_id = berth.id
                berth_free_at = self._berth_free[berth_id]
                wait = max(0, berth_free_at - vp.eta_h)
                vp.predicted_wait_h = round(wait, 2)
                vp.assigned_berth = berth_id
                vp.predicted_start_h = round(max(vp.eta_h, berth_free_at), 2)

                crane_ids = self._assign_cranes(berth_id, vessel)
                service_t = self._service_time(vessel, crane_ids)
                vp.predicted_berth_h = round(service_t, 2)
                vp.predicted_end_h = round(vp.predicted_start_h + service_t, 2)
                vp.status = "berthed"

                self._berth_free[berth_id] = vp.predicted_start_h + service_t
                berth_events[berth_id].append((vp.predicted_start_h, vp.predicted_end_h))
                break
            else:
                # Still no berth available
                vp.predicted_wait_h = 999.0  # marker for unresolved
                vp.status = "queued"

            predictions.append(vp)

        # Build utilisation forecasts in 4h buckets
        berth_util = self._build_berth_util(berth_events)
        queue_forecast = self._build_queue_forecast(queue_snapshots)
        yard_forecast = self._build_yard_forecast()

        # Compute summary stats
        waits = [p.predicted_wait_h for p in predictions if p.predicted_wait_h < 999]
        avg_wait = sum(waits) / len(waits) if waits else 0.0
        max_q = max((qs[1] for qs in queue_snapshots), default=0)

        return ForwardResult(
            vessel_predictions=predictions,
            berth_util=berth_util,
            queue_forecast=queue_forecast,
            yard_forecast=yard_forecast,
            max_queue=max_q,
            avg_wait_h=round(avg_wait, 2),
        )

    def _yard_map_capacity(self, zone_id: str) -> int:
        for z in self.yard_zones:
            if z.id == zone_id:
                return z.teu_capacity
        return 999_999

    def _build_berth_util(
        self, berth_events: dict[str, list[tuple[float, float]]]
    ) -> list[BerthUtilPrediction]:
        """Build berth utilisation in 4h buckets."""
        result = []
        num_berths = len(self.berths)
        for berth in self.berths:
            buckets = []
            t = self.as_of_h
            while t < self.as_of_h + self.horizon_h:
                t_end = min(t + self.bucket_h, self.as_of_h + self.horizon_h)
                busy = sum(
                    min(end, t_end) - max(start, t)
                    for start, end in berth_events.get(berth.id, [])
                    if end > t and start < t_end
                )
                util = round(busy / self.bucket_h * 100, 1) if self.bucket_h > 0 else 0.0
                buckets.append(BucketUtil(h=round(t, 1), util_pct=min(util, 100.0)))
                t += self.bucket_h
            result.append(BerthUtilPrediction(berth_id=berth.id, buckets=buckets))
        return result

    def _build_queue_forecast(
        self, queue_snapshots: list[tuple[float, int]]
    ) -> list[QueuePrediction]:
        """Build queue forecast in 4h buckets."""
        result = []
        t = self.as_of_h
        while t < self.as_of_h + self.horizon_h:
            t_end = min(t + self.bucket_h, self.as_of_h + self.horizon_h)
            relevant = [
                qs for qs in queue_snapshots
                if t <= qs[0] < t_end
            ]
            max_q = max((qs[1] for qs in relevant), default=0)
            result.append(QueuePrediction(h=round(t, 1), queue_size=max_q))
            t += self.bucket_h
        return result

    def _build_yard_forecast(self) -> list[YardUtilPrediction]:
        """Build yard utilisation forecast in 4h buckets."""
        result = []
        yard_cap = sum(z.teu_capacity for z in self.yard_zones)
        t = self.as_of_h
        while t < self.as_of_h + self.horizon_h:
            yard_teu = sum(
                self._yard_teu.get(z.id, z.current_teu)
                for z in self.yard_zones
            )
            util = round(yard_teu / yard_cap * 100, 1) if yard_cap else 0.0
            result.append(YardUtilPrediction(h=round(t, 1), util_pct=min(util, 100.0)))
            t += self.bucket_h
        return result
