"""Hotspot detection rules (plan.md §3.3 §9).

Rules:
  - berth_util > 90 % → high, > 80 % → med
  - queue > num_berths * 4 → high, > num_berths * 2 → med
  - predicted_wait > 24 h → high, > 12 h → med
  - yard > 90 % → high, > 85 % → med

Lead time = earliest hour at which the threshold is first breached in the
forward forecast.  Target: lead_time_h ≥ 12 h.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from app.domain.entities import HotspotKind, Severity

from .forecaster import ForwardResult


@dataclass
class Hotspot:
    id: str
    kind: str
    severity: str
    horizon_h: float
    lead_time_h: float
    affected_berths: list[str]
    affected_vessels: list[str]
    message: str


def _hash_id(kind: str, detail: str) -> str:
    raw = f"{kind}:{detail}"
    return hashlib.md5(raw.encode()).hexdigest()[:8].upper()


def detect_hotspots(
    result: ForwardResult,
    scenario: dict[str, Any],
    as_of_h: float = 0.0,
) -> list[Hotspot]:
    """Detect hotspots from the forward prediction results.

    Parameters
    ----------
    result:
        Output of :meth:`ForwardSimulator.run`.
    scenario:
        Original scenario dict.
    as_of_h:
        Current simulation hour.

    Returns
    -------
    List of :class:`Hotspot` objects with lead_time_h ≥ 12h where possible.
    """
    hotspots: list[Hotspot] = []
    meta = scenario["meta"]
    num_berths = meta["num_berths"]

    # --- Rule 1: berth utilisation ----------------------------------------
    for berth_util in result.berth_util:
        # Find first bucket where util > 90% or > 80%
        first_high: float | None = None
        first_med: float | None = None
        for bucket in berth_util.buckets:
            if bucket.util_pct > 90 and first_high is None:
                first_high = bucket.h
            if bucket.util_pct > 80 and first_med is None:
                first_med = bucket.h

        if first_high is not None:
            lead = max(0, first_high - as_of_h)
            hotspots.append(Hotspot(
                id=f"HS-{_hash_id('berth_util', berth_util.berth_id)}",
                kind="berth_util",
                severity="high",
                horizon_h=168,
                lead_time_h=round(lead, 1),
                affected_berths=[berth_util.berth_id],
                affected_vessels=[],
                message=(
                    f"Berth {berth_util.berth_id} predicted >90% utilisation "
                    f"at h{first_high:.0f} ({lead:.0f}h lead time)"
                ),
            ))
        elif first_med is not None:
            lead = max(0, first_med - as_of_h)
            hotspots.append(Hotspot(
                id=f"HS-{_hash_id('berth_util', berth_util.berth_id)}",
                kind="berth_util",
                severity="med",
                horizon_h=168,
                lead_time_h=round(lead, 1),
                affected_berths=[berth_util.berth_id],
                affected_vessels=[],
                message=(
                    f"Berth {berth_util.berth_id} predicted >80% utilisation "
                    f"at h{first_med:.0f} ({lead:.0f}h lead time)"
                ),
            ))

    # --- Rule 2: queue size -----------------------------------------------
    first_queue_high: float | None = None
    first_queue_med: float | None = None
    for qf in result.queue_forecast:
        if qf.queue_size > num_berths * 4 and first_queue_high is None:
            first_queue_high = qf.h
        if qf.queue_size > num_berths * 2 and first_queue_med is None:
            first_queue_med = qf.h

    if first_queue_high is not None:
        lead = max(0, first_queue_high - as_of_h)
        hotspots.append(Hotspot(
            id=f"HS-{_hash_id('queue', 'global')}",
            kind="queue",
            severity="high",
            horizon_h=168,
            lead_time_h=round(lead, 1),
            affected_berths=[b.id for b in scenario["berths"]],
            affected_vessels=[],
            message=(
                f"Queue predicted to exceed {num_berths * 4} vessels "
                f"at h{first_queue_high:.0f} ({lead:.0f}h lead time)"
            ),
        ))
    elif first_queue_med is not None:
        lead = max(0, first_queue_med - as_of_h)
        hotspots.append(Hotspot(
            id=f"HS-{_hash_id('queue', 'global')}",
            kind="queue",
            severity="med",
            horizon_h=168,
            lead_time_h=round(lead, 1),
            affected_berths=[b.id for b in scenario["berths"]],
            affected_vessels=[],
            message=(
                f"Queue predicted to exceed {num_berths * 2} vessels "
                f"at h{first_queue_med:.0f} ({lead:.0f}h lead time)"
            ),
        ))

    # --- Rule 3: predicted wait per vessel --------------------------------
    long_wait_vessels: list[str] = []
    for vp in result.vessel_predictions:
        if vp.predicted_wait_h > 24:
            long_wait_vessels.append(vp.vessel_id)
        elif vp.predicted_wait_h > 12:
            long_wait_vessels.append(vp.vessel_id)

    if long_wait_vessels:
        severity = "high" if any(
            vp.predicted_wait_h > 24
            for vp in result.vessel_predictions
            if vp.vessel_id in long_wait_vessels
        ) else "med"

        hotspots.append(Hotspot(
            id=f"HS-{_hash_id('wait', 'vessels')}",
            kind="wait",
            severity=severity,
            horizon_h=168,
            lead_time_h=round(max(0, result.vessel_predictions[0].eta_h - as_of_h), 1)
            if result.vessel_predictions else 0,
            affected_berths=[],
            affected_vessels=long_wait_vessels,
            message=(
                f"{len(long_wait_vessels)} vessel(s) predicted wait >12h; "
                f"avg predicted wait: {result.avg_wait_h:.1f}h"
            ),
        ))

    # --- Rule 4: yard utilisation -----------------------------------------
    first_yard_high: float | None = None
    first_yard_med: float | None = None
    for yf in result.yard_forecast:
        if yf.util_pct > 90 and first_yard_high is None:
            first_yard_high = yf.h
        if yf.util_pct > 85 and first_yard_med is None:
            first_yard_med = yf.h

    if first_yard_high is not None:
        lead = max(0, first_yard_high - as_of_h)
        hotspots.append(Hotspot(
            id=f"HS-{_hash_id('yard', 'global')}",
            kind="yard",
            severity="high",
            horizon_h=168,
            lead_time_h=round(lead, 1),
            affected_berths=[],
            affected_vessels=[],
            message=(
                f"Yard predicted >90% utilisation "
                f"at h{first_yard_high:.0f} ({lead:.0f}h lead time)"
            ),
        ))
    elif first_yard_med is not None:
        lead = max(0, first_yard_med - as_of_h)
        hotspots.append(Hotspot(
            id=f"HS-{_hash_id('yard', 'global')}",
            kind="yard",
            severity="med",
            horizon_h=168,
            lead_time_h=round(lead, 1),
            affected_berths=[],
            affected_vessels=[],
            message=(
                f"Yard predicted >85% utilisation "
                f"at h{first_yard_med:.0f} ({lead:.0f}h lead time)"
            ),
        ))

    return hotspots
