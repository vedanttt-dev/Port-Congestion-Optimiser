"""P1 exit-criterion tests: FastAPI app boots and serves the health probe."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_points_to_docs_and_health() -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["health"] == "/api/health"
    assert body["docs"] == "/docs"


def test_health_ok() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
