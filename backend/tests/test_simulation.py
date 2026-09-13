"""P3 tests: simulation engine produces valid baseline results.

Run with: ``pytest tests/test_simulation.py -v``
"""

from __future__ import annotations

import pytest

from app.data.generator import generate_scenario
from app.simulation.engine import EventType, SimulationEngine, SimulationResult
from app.simulation.kpi import (
    compute_kpis,
    format_kpi_report,
    kpis_to_dict,
    save_kpi_csv,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def scenario() -> dict:
    return generate_scenario(seed=42, weeks=4)


@pytest.fixture(scope="module")
def result(scenario: dict) -> SimulationResult:
    engine = SimulationEngine(scenario, seed=42, horizon_h=672.0)
    return engine.run()


@pytest.fixture(scope="module")
def kpis(result: SimulationResult, scenario: dict):
    return compute_kpis(result, scenario)


# ---------------------------------------------------------------------------
# Engine tests
# ---------------------------------------------------------------------------

class TestSimulationEngine:
    def test_run_completes(self, result: SimulationResult) -> None:
        assert len(result.events) > 0

    def test_all_vessels_processed(self, result: SimulationResult, scenario: dict) -> None:
        expected = scenario["meta"]["total_arrivals"]
        assert len(result.vessel_states) == expected

    def test_vessel_has_arrived(self, result: SimulationResult) -> None:
        for vs in result.vessel_states.values():
            assert vs.arrived_h >= 0

    def test_vessel_wait_non_negative(self, result: SimulationResult) -> None:
        for vs in result.vessel_states.values():
            assert vs.wait_h >= 0

    def test_event_types_present(self, result: SimulationResult) -> None:
        types = {e.event_type for e in result.events}
        assert EventType.ARRIVAL in types
        assert EventType.BERTH_ASSIGN in types
        assert EventType.DEPARTURE in types

    def test_events_chronological(self, result: SimulationResult) -> None:
        for i in range(1, len(result.events)):
            assert result.events[i].time_h >= result.events[i - 1].time_h

    def test_queue_samples_non_negative(self, result: SimulationResult) -> None:
        for _, qsize in result.queue_samples:
            assert qsize >= 0

    def test_reproducible_with_same_seed(self, scenario: dict) -> None:
        r1 = SimulationEngine(scenario, seed=42, horizon_h=672.0).run()
        r2 = SimulationEngine(scenario, seed=42, horizon_h=672.0).run()
        assert len(r1.events) == len(r2.events)
        for e1, e2 in zip(r1.events, r2.events):
            assert e1.time_h == e2.time_h
            assert e1.event_type == e2.event_type
            assert e1.vessel_id == e2.vessel_id


# ---------------------------------------------------------------------------
# KPI tests
# ---------------------------------------------------------------------------

class TestKPIs:
    def test_avg_wait_positive(self, kpis) -> None:
        assert kpis.avg_wait_h >= 0

    def test_p95_gte_avg(self, kpis) -> None:
        assert kpis.p95_wait_h >= kpis.avg_wait_h

    def test_berth_util_range(self, kpis) -> None:
        assert 0 <= kpis.berth_util_pct <= 100

    def test_crane_util_range(self, kpis) -> None:
        assert 0 <= kpis.crane_util_pct <= 100

    def test_yard_util_range(self, kpis) -> None:
        assert 0 <= kpis.yard_util_pct <= 100

    def test_demurrage_positive(self, kpis) -> None:
        assert kpis.demurrage_cost_usd > 0

    def test_kpis_to_dict(self, kpis) -> None:
        d = kpis_to_dict(kpis)
        assert "avg_wait_h" in d
        assert "demurrage_cost_usd" in d
        assert isinstance(d["max_queue"], int)

    def test_congested_port_behaviour(self, kpis) -> None:
        """Baseline should show congestion: avg wait > 0 and queue > 0."""
        assert kpis.avg_wait_h > 0
        assert kpis.max_queue > 0


# ---------------------------------------------------------------------------
# CSV output tests
# ---------------------------------------------------------------------------

class TestCSVOutput:
    def test_save_csv(self, result, kpis, tmp_path) -> None:
        kpi_path = save_kpi_csv(result, kpis, tmp_path)
        assert kpi_path.exists()
        assert (tmp_path / "vessel_results.csv").exists()

    def test_kpi_csv_content(self, result, kpis, tmp_path) -> None:
        kpi_path = save_kpi_csv(result, kpis, tmp_path)
        content = kpi_path.read_text()
        assert "avg_wait_h" in content
        assert "demurrage_cost_usd" in content

    def test_vessel_csv_row_count(self, result, kpis, scenario, tmp_path) -> None:
        save_kpi_csv(result, kpis, tmp_path)
        lines = (tmp_path / "vessel_results.csv").read_text().strip().split("\n")
        # Header + one row per vessel
        assert len(lines) == scenario["meta"]["total_arrivals"] + 1


# ---------------------------------------------------------------------------
# Report format test
# ---------------------------------------------------------------------------

class TestReport:
    def test_format_report(self, kpis, scenario) -> None:
        report = format_kpi_report(kpis, scenario)
        assert "BASELINE FCFS" in report
        assert "Avg anchorage wait" in report
        assert "Demurrage cost" in report
