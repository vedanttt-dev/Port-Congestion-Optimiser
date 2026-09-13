"""P4 tests: API endpoints return correct shapes and status codes.

Run with: ``pytest tests/test_api.py -v``
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health & meta
# ---------------------------------------------------------------------------

class TestHealthMeta:
    def test_root(self) -> None:
        r = client.get("/")
        assert r.status_code == 200
        body = r.json()
        assert body["health"] == "/api/health"
        assert body["docs"] == "/docs"

    def test_health(self) -> None:
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_docs_available(self) -> None:
        r = client.get("/docs")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/data/summary
# ---------------------------------------------------------------------------

class TestDataSummary:
    def test_status_code(self) -> None:
        r = client.get("/api/data/summary")
        assert r.status_code == 200

    def test_has_meta(self) -> None:
        body = client.get("/api/data/summary").json()
        assert "meta" in body
        assert body["meta"]["num_berths"] == 8

    def test_has_vessels(self) -> None:
        body = client.get("/api/data/summary").json()
        assert len(body["vessels"]) > 0
        v = body["vessels"][0]
        assert "id" in v
        assert "name" in v
        assert "type" in v
        assert "teu_capacity" in v

    def test_has_berths(self) -> None:
        body = client.get("/api/data/summary").json()
        assert len(body["berths"]) == 8
        b = body["berths"][0]
        assert "length_m" in b
        assert "max_draft_m" in b

    def test_has_cranes(self) -> None:
        body = client.get("/api/data/summary").json()
        assert len(body["cranes"]) >= 22

    def test_has_yard_zones(self) -> None:
        body = client.get("/api/data/summary").json()
        assert len(body["yard_zones"]) == 2

    def test_has_alt_ports(self) -> None:
        body = client.get("/api/data/summary").json()
        assert len(body["alt_ports"]) == 2


# ---------------------------------------------------------------------------
# POST /api/predict
# ---------------------------------------------------------------------------

class TestPredict:
    def test_status_code(self) -> None:
        r = client.post("/api/predict")
        assert r.status_code == 200

    def test_has_vessel_forecasts(self) -> None:
        body = client.post("/api/predict").json()
        assert "vessel_forecasts" in body
        assert len(body["vessel_forecasts"]) > 0
        vf = body["vessel_forecasts"][0]
        assert "vessel_id" in vf
        assert "predicted_wait_h" in vf

    def test_has_hotspots(self) -> None:
        body = client.post("/api/predict").json()
        assert "hotspots" in body

    def test_has_queue_forecast(self) -> None:
        body = client.post("/api/predict").json()
        assert "queue_forecast" in body
        assert len(body["queue_forecast"]) > 0

    def test_has_berth_util_forecast(self) -> None:
        body = client.post("/api/predict").json()
        assert "berth_util_forecast" in body
        assert len(body["berth_util_forecast"]) == 8

    def test_with_overrides(self) -> None:
        r = client.post("/api/predict", json={"as_of_h": 0, "horizon_h": 168})
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/optimize
# ---------------------------------------------------------------------------

class TestOptimize:
    def test_status_code(self) -> None:
        r = client.post("/api/optimize")
        assert r.status_code == 200

    def test_has_assignments(self) -> None:
        body = client.post("/api/optimize").json()
        assert "assignments" in body
        assert len(body["assignments"]) > 0
        a = body["assignments"][0]
        assert "vessel_id" in a
        assert "berth_id" in a

    def test_has_kpis(self) -> None:
        body = client.post("/api/optimize").json()
        assert "kpis" in body
        assert "baseline" in body["kpis"]
        assert "optimized" in body["kpis"]

    def test_has_reroutes(self) -> None:
        body = client.post("/api/optimize").json()
        assert "reroutes" in body


# ---------------------------------------------------------------------------
# POST /api/plan
# ---------------------------------------------------------------------------

class TestPlan:
    def test_status_code(self) -> None:
        r = client.post("/api/plan")
        assert r.status_code == 200

    def test_has_shifts(self) -> None:
        body = client.post("/api/plan").json()
        assert "shifts" in body
        assert len(body["shifts"]) == 9  # 3 days × 3 shifts

    def test_shift_structure(self) -> None:
        body = client.post("/api/plan").json()
        s = body["shifts"][0]
        assert "id" in s
        assert "window" in s
        assert "work_orders" in s
        assert "alerts" in s

    def test_with_custom_horizon(self) -> None:
        r = client.post("/api/plan", json={"horizon_h": 48.0})
        body = r.json()
        assert len(body["shifts"]) == 6  # 48 / 8


# ---------------------------------------------------------------------------
# GET /api/kpis
# ---------------------------------------------------------------------------

class TestKpis:
    def test_status_code(self) -> None:
        r = client.get("/api/kpis")
        assert r.status_code == 200

    def test_has_all_fields(self) -> None:
        body = client.get("/api/kpis").json()
        expected = [
            "avg_wait_h", "p95_wait_h", "max_queue",
            "berth_util_pct", "crane_util_pct", "yard_util_pct",
            "demurrage_cost_usd",
        ]
        for field in expected:
            assert field in body, f"Missing field: {field}"

    def test_demurrage_positive(self) -> None:
        body = client.get("/api/kpis").json()
        assert body["demurrage_cost_usd"] > 0


# ---------------------------------------------------------------------------
# GET /api/live
# ---------------------------------------------------------------------------

class TestLive:
    def test_status_code(self) -> None:
        r = client.get("/api/live")
        assert r.status_code == 200

    def test_has_vessels(self) -> None:
        body = client.get("/api/live").json()
        assert "vessels" in body
        assert len(body["vessels"]) > 0
        v = body["vessels"][0]
        assert "lat" in v
        assert "lon" in v
        assert "state" in v

    def test_has_recent_events(self) -> None:
        body = client.get("/api/live").json()
        assert "recent_events" in body

    def test_has_kpis(self) -> None:
        body = client.get("/api/live").json()
        assert "kpis" in body


# ---------------------------------------------------------------------------
# CORS check
# ---------------------------------------------------------------------------

class TestCORS:
    def test_cors_preflight(self) -> None:
        r = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert r.status_code in (200, 405)
