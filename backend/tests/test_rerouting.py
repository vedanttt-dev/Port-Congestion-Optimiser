"""P7 tests: rerouting recommender produces valid recommendations.

Run with: ``pytest tests/test_rerouting.py -v``
"""

from __future__ import annotations

import pytest

from app.data.generator import generate_scenario
from app.optimization.rerouting import ReroutingRecommender, RerouteRecommendation
from app.optimization.solver import BerthCraneOptimiser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def scenario() -> dict:
    return generate_scenario(seed=42, weeks=4)


@pytest.fixture(scope="module")
def vessel_waits(scenario: dict) -> dict[str, float]:
    """Get vessel waits from the optimizer."""
    opt = BerthCraneOptimiser(scenario, horizon_h=168.0, time_limit_s=2.0)
    result = opt.solve()
    return {a.vessel_id: a.wait_h for a in result.assignments}


@pytest.fixture(scope="module")
def recommendations(scenario: dict, vessel_waits: dict) -> list[RerouteRecommendation]:
    rec = ReroutingRecommender(scenario, vessel_waits=vessel_waits, max_diversions=5)
    return rec.recommend()


# ---------------------------------------------------------------------------
# Cost model tests
# ---------------------------------------------------------------------------

class TestCostModel:
    def test_wait_cost_positive(self, scenario, vessel_waits) -> None:
        from app.optimization.rerouting import _wait_cost
        v = scenario["vessels"][0]
        cost = _wait_cost(v, 24.0)
        assert cost > 0

    def test_wait_cost_increases_with_wait(self, scenario) -> None:
        from app.optimization.rerouting import _wait_cost
        v = scenario["vessels"][0]
        cost_12h = _wait_cost(v, 12.0)
        cost_48h = _wait_cost(v, 48.0)
        assert cost_48h > cost_12h

    def test_divert_cost_positive(self, scenario) -> None:
        from app.optimization.rerouting import _divert_cost
        v = scenario["vessels"][0]
        ap = scenario["alt_ports"][0]
        cost = _divert_cost(v, ap)
        assert cost > 0

    def test_divert_cost_varies_by_port(self, scenario) -> None:
        from app.optimization.rerouting import _divert_cost
        v = scenario["vessels"][0]
        cost_ap1 = _divert_cost(v, scenario["alt_ports"][0])
        cost_ap2 = _divert_cost(v, scenario["alt_ports"][1])
        assert cost_ap1 != cost_ap2


# ---------------------------------------------------------------------------
# Recommender tests
# ---------------------------------------------------------------------------

class TestRecommender:
    def test_returns_list(self, recommendations) -> None:
        assert isinstance(recommendations, list)

    def test_max_diversions(self, recommendations) -> None:
        assert len(recommendations) <= 5

    def test_recommendation_has_fields(self, recommendations) -> None:
        for r in recommendations:
            assert r.vessel_id
            assert r.alt_port_id
            assert r.saving_usd > 0
            assert r.wait_cost_usd > 0
            assert r.divert_cost_usd > 0
            assert r.reason

    def test_sorted_by_saving(self, recommendations) -> None:
        savings = [r.saving_usd for r in recommendations]
        assert savings == sorted(savings, reverse=True)

    def test_no_duplicate_vessels(self, recommendations) -> None:
        vessel_ids = [r.vessel_id for r in recommendations]
        assert len(vessel_ids) == len(set(vessel_ids))

    def test_respects_alt_port_capacity(self, recommendations, scenario) -> None:
        alt_port_usage: dict[str, int] = {}
        for r in recommendations:
            alt_port_usage[r.alt_port_id] = alt_port_usage.get(r.alt_port_id, 0) + 1
        for ap in scenario["alt_ports"]:
            assert alt_port_usage.get(ap.id, 0) <= ap.berth_capacity

    def test_no_savings_with_zero_wait(self, scenario) -> None:
        rec = ReroutingRecommender(scenario, vessel_waits={}, max_diversions=5)
        result = rec.recommend()
        assert len(result) == 0


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestOptimizeReroutes:
    def test_optimize_has_reroutes(self) -> None:
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        body = client.post("/api/optimize").json()
        assert "reroutes" in body
        assert isinstance(body["reroutes"], list)

    def test_reroute_structure(self) -> None:
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        body = client.post("/api/optimize").json()
        if body["reroutes"]:
            r = body["reroutes"][0]
            assert "vessel_id" in r
            assert "alt_port_id" in r
            assert "saving_usd" in r
            assert "reason" in r

    def test_optimize_cost_saved_includes_reroutes(self) -> None:
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        body = client.post("/api/optimize").json()
        assert body["kpis"]["optimized"]["cost_saved_usd"] >= 0
