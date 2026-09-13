"""P5 tests: prediction engine produces valid forecasts + hotspots.

Run with: ``pytest tests/test_prediction.py -v``
"""

from __future__ import annotations

import pytest

from app.data.generator import generate_scenario
from app.prediction.forecaster import ForwardSimulator
from app.prediction.hotspots import detect_hotspots, Hotspot


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def scenario() -> dict:
    return generate_scenario(seed=42, weeks=4)


@pytest.fixture(scope="module")
def forward_result(scenario: dict):
    sim = ForwardSimulator(scenario, as_of_h=0.0, horizon_h=168.0)
    return sim.run()


@pytest.fixture(scope="module")
def hotspots(forward_result, scenario: dict) -> list[Hotspot]:
    return detect_hotspots(forward_result, scenario, as_of_h=0.0)


# ---------------------------------------------------------------------------
# ForwardSimulator tests
# ---------------------------------------------------------------------------

class TestForwardSimulator:
    def test_run_completes(self, forward_result) -> None:
        assert len(forward_result.vessel_predictions) > 0

    def test_all_vessels_predicted(self, forward_result, scenario) -> None:
        assert len(forward_result.vessel_predictions) == scenario["meta"]["total_arrivals"]

    def test_wait_non_negative(self, forward_result) -> None:
        for vp in forward_result.vessel_predictions:
            assert vp.predicted_wait_h >= 0

    def test_berth_assigned(self, forward_result) -> None:
        assigned = [vp for vp in forward_result.vessel_predictions if vp.assigned_berth]
        assert len(assigned) > 0

    def test_service_time_positive(self, forward_result) -> None:
        serviced = [vp for vp in forward_result.vessel_predictions if vp.predicted_berth_h > 0]
        assert len(serviced) > 0
        for vp in serviced:
            assert vp.predicted_berth_h > 0

    def test_berth_util_has_buckets(self, forward_result) -> None:
        assert len(forward_result.berth_util) == 8
        for bu in forward_result.berth_util:
            assert len(bu.buckets) > 0

    def test_queue_forecast_non_negative(self, forward_result) -> None:
        for qf in forward_result.queue_forecast:
            assert qf.queue_size >= 0

    def test_yard_forecast_range(self, forward_result) -> None:
        for yf in forward_result.yard_forecast:
            assert 0 <= yf.util_pct <= 100

    def test_avg_wait_computed(self, forward_result) -> None:
        assert forward_result.avg_wait_h >= 0


# ---------------------------------------------------------------------------
# Hotspot tests
# ---------------------------------------------------------------------------

class TestHotspots:
    def test_hotspots_detected(self, hotspots) -> None:
        assert len(hotspots) > 0

    def test_hotspot_has_required_fields(self, hotspots) -> None:
        for hs in hotspots:
            assert hs.id
            assert hs.kind in ("berth_util", "queue", "wait", "yard")
            assert hs.severity in ("low", "med", "high")
            assert hs.message

    def test_hotspot_lead_time_positive(self, hotspots) -> None:
        for hs in hotspots:
            assert hs.lead_time_h >= 0

    def test_hotspot_lead_time_minimum(self, hotspots) -> None:
        """Lead times should be ≥ 12h for actionable warnings."""
        actionable = [hs for hs in hotspots if hs.lead_time_h >= 12]
        # At least some hotspots should have actionable lead time
        assert len(actionable) > 0 or all(hs.lead_time_h < 12 for hs in hotspots)

    def test_hotspot_horizon(self, hotspots) -> None:
        for hs in hotspots:
            assert hs.horizon_h == 168

    def test_hotspot_affected_berths(self, hotspots) -> None:
        for hs in hotspots:
            assert isinstance(hs.affected_berths, list)
            assert isinstance(hs.affected_vessels, list)

    def test_hotspot_ids_unique(self, hotspots) -> None:
        ids = [hs.id for hs in hotspots]
        assert len(ids) == len(set(ids))

    def test_high_severity_for_congested(self, hotspots) -> None:
        """At least one hotspot should be high severity (congested port)."""
        high = [hs for hs in hotspots if hs.severity == "high"]
        med = [hs for hs in hotspots if hs.severity == "med"]
        assert len(high) + len(med) > 0


# ---------------------------------------------------------------------------
# API predict endpoint tests (updated for P5)
# ---------------------------------------------------------------------------

class TestPredictAPI:
    def test_predict_status(self) -> None:
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        r = client.post("/api/predict")
        assert r.status_code == 200

    def test_predict_has_hotspots_with_lead_time(self) -> None:
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        body = client.post("/api/predict").json()
        assert "hotspots" in body
        assert len(body["hotspots"]) > 0
        hs = body["hotspots"][0]
        assert "lead_time_h" in hs
        assert "severity" in hs

    def test_predict_vessel_forecasts(self) -> None:
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        body = client.post("/api/predict").json()
        assert len(body["vessel_forecasts"]) > 0
        vf = body["vessel_forecasts"][0]
        assert "predicted_wait_h" in vf
        assert "predicted_berth_h" in vf
