import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.config.settings import Settings
from app.live.lanes import LaneRegistry
from app.main import create_app
from app.providers.base import CapProvider
from app.providers.factory import create_provider
from tests.support.engine_harness import CSV_HEADER, PROJECT_ROOT

TOKEN = "correct-horse-battery"
ORIGIN = {"origin": "http://testserver"}


def settings_for(tmp_path: Path, **overrides: object) -> Settings:
    variants = tmp_path / "name_variants.json"
    shutil.copy(PROJECT_ROOT / "config" / "name_variants.json", variants)
    values: dict[str, object] = {
        "mock_fixtures_dir": PROJECT_ROOT / "fixtures",
        "name_variants_file": variants,
        "mock_speed_factor": 5000,
        "mock_failure_rate": 0,
        "max_workers": 1,
        "cookie_secure": False,
    }
    values.update(overrides)
    return Settings.model_validate(values)


def build_live_mode_client(tmp_path: Path, **overrides: object) -> TestClient:
    settings = settings_for(tmp_path, cap_provider="live", admin_token=TOKEN, **overrides)
    mock_settings = settings_for(tmp_path)
    registry = LaneRegistry()

    def factory(lane: int) -> CapProvider:
        channel = registry.channel_for(lane) if lane >= 0 else None
        return create_provider(mock_settings, channel=channel)

    return TestClient(create_app(settings, factory, registry))


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    with build_live_mode_client(tmp_path) as test_client:
        yield test_client


def login(client: TestClient, token: str = TOKEN) -> None:
    response = client.post("/auth/login", json={"token": token}, headers=ORIGIN)
    assert response.status_code == 204


def test_everything_but_health_requires_a_session_in_live_mode(client: TestClient) -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/jobs").status_code == 401
    assert client.get("/jobs/abc").status_code == 401
    assert client.get("/jobs/abc/events").status_code == 401
    assert client.post("/jobs/abc/cancel").status_code == 401
    assert client.get("/lanes").status_code == 401


def test_wrong_token_is_refused(client: TestClient) -> None:
    response = client.post("/auth/login", json={"token": "nope"}, headers=ORIGIN)

    assert response.status_code == 401
    assert client.get("/jobs").status_code == 401


def test_login_sets_a_hardened_cookie_and_opens_the_api(client: TestClient) -> None:
    response = client.post("/auth/login", json={"token": TOKEN}, headers=ORIGIN)

    cookie = response.headers["set-cookie"].lower()
    assert response.status_code == 204
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert TOKEN not in response.headers["set-cookie"]
    assert client.get("/jobs").status_code == 200


def test_cookie_is_marked_secure_unless_relaxed_for_local_development(tmp_path: Path) -> None:
    with build_live_mode_client(tmp_path, cookie_secure=True) as secure_client:
        response = secure_client.post("/auth/login", json={"token": TOKEN}, headers=ORIGIN)

    assert "secure" in response.headers["set-cookie"].lower()


def test_the_token_cannot_travel_in_a_url(client: TestClient) -> None:
    assert client.get(f"/auth/login?token={TOKEN}").status_code == 405
    assert client.get(f"/jobs?token={TOKEN}").status_code == 401


def test_logout_ends_the_session(client: TestClient) -> None:
    login(client)

    assert client.post("/auth/logout", headers=ORIGIN).status_code == 204

    assert client.get("/jobs").status_code == 401


def test_session_endpoint_tells_the_frontend_what_to_do(client: TestClient) -> None:
    assert client.get("/auth/session").json() == {
        "authentication_required": True,
        "authenticated": False,
    }
    login(client)
    assert client.get("/auth/session").json()["authenticated"] is True


def test_login_attempts_are_rate_limited(tmp_path: Path) -> None:
    with build_live_mode_client(tmp_path, login_max_failures_per_minute=3) as limited:
        codes = [
            limited.post("/auth/login", json={"token": "bad"}, headers=ORIGIN).status_code
            for _ in range(4)
        ]
        correct = limited.post("/auth/login", json={"token": TOKEN}, headers=ORIGIN)

    assert codes == [401, 401, 401, 429]
    assert correct.status_code == 429


def test_requests_from_a_foreign_origin_are_refused(client: TestClient) -> None:
    login(client)

    response = client.post("/jobs/abc/cancel", headers={"origin": "http://evil.example"})
    login_response = client.post(
        "/auth/login", json={"token": TOKEN}, headers={"origin": "http://evil.example"}
    )

    assert response.status_code == 403
    assert login_response.status_code == 403


def test_the_configured_frontend_origin_is_accepted(client: TestClient) -> None:
    login(client)

    response = client.post("/jobs/abc/cancel", headers={"origin": "http://localhost:5173"})

    assert response.status_code == 404


def test_the_live_view_channel_needs_a_session_and_a_valid_origin(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/lanes/0", headers=ORIGIN):
            pass

    login(client)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/lanes/0", headers={"origin": "http://evil.example"}):
            pass
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws/lanes/0"):
        pass


def test_an_authenticated_viewer_receives_the_lane_status(client: TestClient) -> None:
    login(client)

    with client.websocket_connect("/ws/lanes/0", headers=ORIGIN) as websocket:
        message = websocket.receive_json()

    assert message["type"] == "status"
    assert message["lane"] == 0 and message["awaiting_captcha"] is False


def test_mock_mode_needs_no_authentication(tmp_path: Path) -> None:
    with TestClient(create_app(settings_for(tmp_path))) as open_client:
        assert open_client.get("/jobs").status_code == 200
        assert open_client.get("/auth/session").json()["authentication_required"] is False
        assert open_client.post("/auth/login", json={"token": "x"}).status_code == 401


def test_jobs_can_be_created_after_login(client: TestClient) -> None:
    login(client)
    files = {"file": ("people.csv", (CSV_HEADER + "Nemo,Nobody,,x\n").encode("utf-8"))}

    response = client.post("/jobs", files=files, headers=ORIGIN)

    assert response.status_code == 201
