from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import create_app


def build_client() -> TestClient:
    return TestClient(create_app(Settings()))


def test_health_reports_ok_and_active_provider() -> None:
    response = build_client().get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "provider": "mock"}


def test_cors_allows_configured_frontend_origin() -> None:
    response = build_client().get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
