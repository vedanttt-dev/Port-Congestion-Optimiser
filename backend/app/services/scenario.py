"""Orchestration service — loads scenario and runs sim on demand.

Provides a singleton-style ``ScenarioService`` used by all routers so the
scenario is loaded once and reused across requests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.data.generator import generate_scenario
from app.simulation.engine import SimulationEngine, SimulationResult
from app.simulation.kpi import compute_kpis

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw"


class ScenarioService:
    """Loads scenario data once, runs simulation lazily."""

    def __init__(self) -> None:
        self._scenario: dict[str, Any] | None = None
        self._result: SimulationResult | None = None

    @property
    def scenario(self) -> dict[str, Any]:
        if self._scenario is None:
            self._scenario = generate_scenario(seed=42, weeks=4)
        return self._scenario

    def get_result(self, seed: int = 42, horizon_h: float = 672.0) -> SimulationResult:
        if self._result is None:
            engine = SimulationEngine(self.scenario, seed=seed, horizon_h=horizon_h)
            self._result = engine.run()
        return self._result

    def get_kpis(self, seed: int = 42, horizon_h: float = 672.0):
        result = self.get_result(seed=seed, horizon_h=horizon_h)
        return compute_kpis(result, self.scenario)

    def reset(self) -> None:
        """Force re-generation on next access."""
        self._scenario = None
        self._result = None


# Module-level singleton
svc = ScenarioService()
