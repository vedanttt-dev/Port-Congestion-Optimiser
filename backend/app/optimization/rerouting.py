"""Rerouting recommender (plan.md §3.5 §6-P7).

Compares *waiting at the primary port* vs *diverting to an alternate port*
for each vessel and recommends a diversion set that maximises total savings
while respecting alt-port berth capacity limits.

Cost model
----------
- wait_cost(v) = demurrage_per_day × (wait_h / 24) + schedule_slippage
- divert_cost(v) = fuel_surcharge + transit_cost + alt_port_handling_premium
                   + alt_port_congestion_penalty
- saving(v) = wait_cost(v) − divert_cost(v)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.entities import AltPort, Vessel


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Fuel surcharge per nautical mile (rough estimate)
FUEL_USD_PER_NM = 25.0

# Average speed for fuel calc
SPEED_KN = 14.0

# Schedule slippage cost per hour of delay
SCHEDULE_SLIPPAGE_USD_PER_H = 500.0

# Average nautical miles per transit hour (at 14 kn)
NM_PER_HOUR = 14.0


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class RerouteRecommendation:
    vessel_id: str
    vessel_name: str
    alt_port_id: str
    alt_port_name: str
    wait_cost_usd: float
    divert_cost_usd: float
    saving_usd: float
    reason: str
    est_transit_h: float = 0.0
    wait_h: float = 0.0


# ---------------------------------------------------------------------------
# Cost computations
# ---------------------------------------------------------------------------

def _wait_cost(vessel: Vessel, wait_h: float) -> float:
    """Demurrage + schedule slippage for waiting at primary port."""
    demurrage = vessel.demurrage_usd_per_day * (wait_h / 24)
    slippage = wait_h * SCHEDULE_SLIPPAGE_USD_PER_H
    return demurrage + slippage


def _divert_cost(vessel: Vessel, alt_port: AltPort) -> float:
    """Total cost of diverting to an alternate port."""
    nm = alt_port.transit_hours * NM_PER_HOUR
    fuel = nm * FUEL_USD_PER_NM
    handling = alt_port.handling_premium_usd
    congestion = alt_port.congestion_index * 100_000  # penalty for congested alt port
    return fuel + handling + congestion


# ---------------------------------------------------------------------------
# Recommender
# ---------------------------------------------------------------------------

class ReroutingRecommender:
    """Evaluates diversion candidates and recommends a set.

    Parameters
    ----------
    scenario:
        Scenario dict with vessels, alt_ports.
    vessel_waits:
        Mapping of vessel_id → predicted wait in hours (from optimizer/prediction).
    max_diversions:
        Maximum number of vessels to divert (default: 5).
    """

    def __init__(
        self,
        scenario: dict[str, Any],
        vessel_waits: dict[str, float] | None = None,
        max_diversions: int = 5,
    ) -> None:
        self.vessels: list[Vessel] = list(scenario["vessels"])
        self.alt_ports: list[AltPort] = list(scenario["alt_ports"])
        self.vessel_waits = vessel_waits or {}
        self.max_diversions = max_diversions

        self._vessel_map = {v.id: v for v in self.vessels}

    def recommend(self) -> list[RerouteRecommendation]:
        """Return sorted list of vessel-port reroute recommendations.

        Vessels with the highest saving are recommended first, subject to
        alt-port berth capacity limits.
        """
        # Compute saving for every (vessel, alt_port) pair
        candidates: list[RerouteRecommendation] = []
        for v in self.vessels:
            wait_h = self.vessel_waits.get(v.id, 0)
            if wait_h <= 0:
                continue

            wc = _wait_cost(v, wait_h)
            for ap in self.alt_ports:
                dc = _divert_cost(v, ap)
                saving = wc - dc
                if saving > 0:
                    candidates.append(RerouteRecommendation(
                        vessel_id=v.id,
                        vessel_name=v.name,
                        alt_port_id=ap.id,
                        alt_port_name=ap.name,
                        wait_cost_usd=round(wc, 2),
                        divert_cost_usd=round(dc, 2),
                        saving_usd=round(saving, 2),
                        reason=(
                            f"Save ${saving:,.0f}: wait cost ${wc:,.0f} vs "
                            f"divert cost ${dc:,.0f} ({ap.name})"
                        ),
                        est_transit_h=ap.transit_hours,
                        wait_h=wait_h,
                    ))

        # Sort by saving descending
        candidates.sort(key=lambda r: r.saving_usd, reverse=True)

        # Select top recommendations respecting alt-port capacity
        alt_port_usage: dict[str, int] = {ap.id: 0 for ap in self.alt_ports}
        selected: list[RerouteRecommendation] = []
        for rec in candidates:
            if len(selected) >= self.max_diversions:
                break
            ap = next((a for a in self.alt_ports if a.id == rec.alt_port_id), None)
            if ap is None:
                continue
            if alt_port_usage[rec.alt_port_id] >= ap.berth_capacity:
                continue
            # Don't divert the same vessel twice
            if any(r.vessel_id == rec.vessel_id for r in selected):
                continue
            alt_port_usage[rec.alt_port_id] += 1
            selected.append(rec)

        return selected
