import base64
import shutil
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

from app.config.settings import Settings
from app.live.lanes import LaneRegistry
from app.live.mock_screen import CAPTCHA_BOX
from app.main import create_app
from app.providers.base import CapProvider
from app.providers.errors import CaptchaRequired
from app.providers.factory import create_provider
from app.providers.mock.failures import FailureSchedule, NoFailures, ScriptedFailures
from tests.support.engine_harness import CSV_HEADER, PROJECT_ROOT


def build_client(tmp_path: Path, failures: FailureSchedule) -> TestClient:
    variants = tmp_path / "name_variants.json"
    shutil.copy(PROJECT_ROOT / "config" / "name_variants.json", variants)
    settings = Settings.model_validate(
        {
            "mock_fixtures_dir": PROJECT_ROOT / "fixtures",
            "name_variants_file": variants,
            "mock_speed_factor": 5000,
            "mock_failure_rate": 0,
            "max_workers": 1,
            "captcha_wait_seconds": 30,
        }
    )
    registry = LaneRegistry()

    def factory(lane: int) -> CapProvider:
        if lane < 0:
            return create_provider(settings, failures=NoFailures())
        return create_provider(settings, channel=registry.channel_for(lane), failures=failures)

    return TestClient(create_app(settings, factory, registry))


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    with build_client(tmp_path, ScriptedFailures([CaptchaRequired("captcha")])) as test_client:
        yield test_client


def upload(client: TestClient, rows: str) -> str:
    files = {"file": ("people.csv", (CSV_HEADER + rows).encode("utf-8"))}
    job_id: str = client.post("/jobs", files=files).json()["job_id"]
    return job_id


def wait_until_finished(client: TestClient, job_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        snapshot: dict[str, Any] = client.get(f"/jobs/{job_id}").json()
        if snapshot["state"] in ("completed", "cancelled"):
            return snapshot
        time.sleep(0.05)
    raise AssertionError("The job did not finish in time")


def read_until(websocket: WebSocketTestSession, wanted: dict[str, Any]) -> dict[str, Any]:
    for _ in range(500):
        message: dict[str, Any] = websocket.receive_json()
        if all(message.get(key) == value for key, value in wanted.items()):
            return message
    raise AssertionError(f"Never received {wanted}")


def click_inside_captcha() -> dict[str, Any]:
    left, top, right, bottom = CAPTCHA_BOX
    return {"type": "click", "x": (left + right) / 2, "y": (top + bottom) / 2}


def test_the_lane_streams_frames_in_the_agreed_format(tmp_path: Path) -> None:
    with build_client(tmp_path, NoFailures()) as client:
        with client.websocket_connect("/ws/lanes/0") as websocket:
            upload(client, "Pedro,Rodriguez,,r\n")
            frame = read_until(websocket, {"type": "frame"})

    assert {"lane", "sequence", "width", "height", "mime_type", "data"} <= frame.keys()
    assert frame["mime_type"] == "image/jpeg"
    assert base64.b64decode(frame["data"]).startswith(b"\xff\xd8")


def test_status_identifies_the_job_and_person_served_by_the_lane(tmp_path: Path) -> None:
    with build_client(tmp_path, NoFailures()) as client:
        with client.websocket_connect("/ws/lanes/0") as websocket:
            job_id = upload(client, "Pedro,Rodriguez,,r\n")
            status = read_until(websocket, {"type": "status", "job_id": job_id})

    assert status["person_index"] == 0
    assert status["person_state"] == "running"


def test_lanes_endpoint_lists_the_workers(tmp_path: Path) -> None:
    with build_client(tmp_path, NoFailures()) as client:
        wait_until_finished(client, upload(client, "Nemo,Nobody,,x\n"))

        lanes = client.get("/lanes").json()

    assert [lane["lane"] for lane in lanes] == [0]
    assert lanes[0]["job_id"] is None


def test_input_is_ignored_when_no_captcha_is_waiting(tmp_path: Path) -> None:
    with build_client(tmp_path, NoFailures()) as client:
        with client.websocket_connect("/ws/lanes/0") as websocket:
            websocket.send_json({"type": "click", "x": 10, "y": 10})
            outcome = read_until(websocket, {"type": "input"})

    assert outcome["outcome"] == "ignored"


def test_malformed_input_is_reported_and_not_forwarded(tmp_path: Path) -> None:
    with build_client(tmp_path, NoFailures()) as client:
        with client.websocket_connect("/ws/lanes/0") as websocket:
            websocket.send_json({"type": "click"})
            outcome = read_until(websocket, {"type": "input"})

    assert outcome["outcome"] == "invalid"


def test_a_person_can_solve_the_simulated_captcha_in_the_live_view(client: TestClient) -> None:
    with client.websocket_connect("/ws/lanes/0") as websocket:
        job_id = upload(client, "Nemo,Nobody,,x\n")
        read_until(websocket, {"type": "status", "awaiting_captcha": True})

        websocket.send_json({"type": "click", "x": 5, "y": 5})
        assert read_until(websocket, {"type": "input"})["outcome"] == "forwarded"
        websocket.send_json(click_inside_captcha())
        outcome = read_until(websocket, {"type": "input"})
        snapshot = wait_until_finished(client, job_id)

    assert outcome["outcome"] == "captcha_resolved"
    assert snapshot["people"][0]["state"] == "done"


def test_the_captcha_events_are_visible_in_the_job_stream(client: TestClient) -> None:
    with client.websocket_connect("/ws/lanes/0") as websocket:
        job_id = upload(client, "Nemo,Nobody,,x\n")
        read_until(websocket, {"type": "status", "awaiting_captcha": True})
        websocket.send_json(click_inside_captcha())
        read_until(websocket, {"type": "input", "outcome": "captcha_resolved"})
    wait_until_finished(client, job_id)

    with client.stream("GET", f"/jobs/{job_id}/events") as response:
        text = "".join(response.iter_text())

    assert text.index("event: captcha_required") < text.index("event: captcha_resolved")
