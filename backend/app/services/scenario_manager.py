"""Scenario management — generate, save, compare what-if scenarios."""

from __future__ import annotations

import time
from typing import Any

from app.data.generator import generate_scenario
from app.simulation.engine import SimulationEngine
from app.simulation.kpi import compute_kpis


class ScenarioManager:
    """Manages multiple named scenarios with caching."""

    def __init__(self) -> None:
        self._scenarios: dict[str, dict[str, Any]] = {}
        self._results: dict[str, Any] = {}
        self._kpis: dict[str, Any] = {}
        self._active: str = "default"

    @property
    def active(self) -> str:
        return self._active

    def get_scenario(self, name: str | None = None) -> dict[str, Any]:
        key = name or self._active
        if key not in self._scenarios:
            raise KeyError(f"Scenario '{key}' not found")
        return self._scenarios[key]

    def get_result(self, name: str | None = None) -> Any:
        key = name or self._active
        if key not in self._results:
            sc = self.get_scenario(key)
            engine = SimulationEngine(sc, seed=sc["meta"]["seed"], horizon_h=672.0)
            self._results[key] = engine.run()
        return self._results[key]

    def get_kpis(self, name: str | None = None) -> Any:
        key = name or self._active
        if key not in self._kpis:
            result = self.get_result(key)
            sc = self.get_scenario(key)
            self._kpis[key] = compute_kpis(result, sc)
        return self._kpis[key]

    def generate(
        self,
        name: str,
        seed: int = 42,
        weeks: int = 4,
        arrivals_per_week: int | None = None,
        num_berths: int | None = None,
        num_cranes: int | None = None,
        vessel_type_override: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Generate a new scenario with optional parameter overrides."""
        start = time.time()
        sc = generate_scenario(seed=seed, weeks=weeks)
        gen_ms = round((time.time() - start) * 1000, 1)

        # Apply overrides
        if vessel_type_override:
            vessels = sc["vessels"]
            from app.domain.entities import VesselType
            type_counts = {vt: 0 for vt in VesselType}
            for v in vessels:
                type_counts[v.type] += 1
            # Store the override info in meta
            sc["meta"]["vessel_type_override"] = vessel_type_override

        if num_berths is not None:
            # Trim or pad berths
            current = len(sc["berths"])
            if num_berths < current:
                sc["berths"] = sc["berths"][:num_berths]
            sc["meta"]["num_berths"] = len(sc["berths"])

        if num_cranes is not None:
            # Adjust crane count
            current_cranes = len(sc["cranes"])
            if num_cranes < current_cranes:
                sc["cranes"] = sc["cranes"][:num_cranes]
            sc["meta"]["num_cranes"] = len(sc["cranes"])

        sc["meta"]["name"] = name
        sc["meta"]["generated_at"] = time.time()
        sc["meta"]["gen_ms"] = gen_ms

        self._scenarios[name] = sc
        # Invalidate cached results for this scenario
        self._results.pop(name, None)
        self._kpis.pop(name, None)

        return sc

    def save(self, name: str) -> dict[str, Any]:
        """Save/return scenario metadata."""
        sc = self.get_scenario(name)
        return {
            "name": name,
            "meta": sc["meta"],
            "num_vessels": len(sc["vessels"]),
            "num_berths": len(sc["berths"]),
            "num_cranes": len(sc["cranes"]),
        }

    def list_scenarios(self) -> list[dict[str, Any]]:
        """List all saved scenarios with summary."""
        result = []
        for name, sc in self._scenarios.items():
            meta = sc.get("meta", {})
            kpi = self._kpis.get(name)
            result.append({
                "name": name,
                "seed": meta.get("seed", 0),
                "weeks": meta.get("weeks", 0),
                "num_vessels": len(sc.get("vessels", [])),
                "num_berths": meta.get("num_berths", 0),
                "num_cranes": meta.get("num_cranes", 0),
                "avg_wait_h": round(kpi.avg_wait_h, 2) if kpi else None,
                "demurrage_usd": round(kpi.demurrage_cost_usd, 0) if kpi else None,
            })
        return result

    def compare(self, name_a: str, name_b: str) -> dict[str, Any]:
        """Compare two scenarios side by side."""
        kpi_a = self.get_kpis(name_a)
        kpi_b = self.get_kpis(name_b)
        sc_a = self.get_scenario(name_a)
        sc_b = self.get_scenario(name_b)

        def kpi_dict(k) -> dict:
            return {
                "avg_wait_h": round(k.avg_wait_h, 2),
                "p95_wait_h": round(k.p95_wait_h, 2),
                "max_queue": k.max_queue,
                "berth_util_pct": round(k.berth_util_pct, 1),
                "crane_util_pct": round(k.crane_util_pct, 1),
                "yard_util_pct": round(k.yard_util_pct, 1),
                "demurrage_cost_usd": round(k.demurrage_cost_usd, 2),
            }

        a_kpis = kpi_dict(kpi_a)
        b_kpis = kpi_dict(kpi_b)

        # Compute deltas
        deltas = {}
        for key in a_kpis:
            a_val = a_kpis[key]
            b_val = b_kpis[key]
            if isinstance(a_val, (int, float)) and a_val != 0:
                deltas[key] = round((b_val - a_val) / abs(a_val) * 100, 1)
            else:
                deltas[key] = 0.0

        return {
            "scenario_a": {
                "name": name_a,
                "meta": sc_a.get("meta", {}),
                "kpis": a_kpis,
            },
            "scenario_b": {
                "name": name_b,
                "meta": sc_b.get("meta", {}),
                "kpis": b_kpis,
            },
            "deltas_pct": deltas,
        }

    def set_active(self, name: str) -> None:
        """Set the active scenario used by other endpoints."""
        if name not in self._scenarios:
            raise KeyError(f"Scenario '{name}' not found")
        self._active = name

    def delete(self, name: str) -> bool:
        """Delete a scenario."""
        if name == "default":
            return False
        self._scenarios.pop(name, None)
        self._results.pop(name, None)
        self._kpis.pop(name, None)
        return True


# Module-level singleton
scenario_manager = ScenarioManager()
