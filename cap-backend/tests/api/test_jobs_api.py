import json
import shutil
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import create_app
from tests.support.engine_harness import CSV_HEADER, PROJECT_ROOT

BRIEF_SAMPLE = (
    CSV_HEADER
    + "Pedro,Rodriguez,,DRV-1002\n"
    + "# comment\n"
    + ",Smith,,DRV-1003\n"
    + "Pedro;Rodriguez,,DRV-1004\n"
    + "J0hn,Smith,31/02/1990,DRV-1005\n"
)


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    variants = tmp_path / "name_variants.json"
    shutil.copy(PROJECT_ROOT / "config" / "name_variants.json", variants)
    settings = Settings.model_validate(
        {
            "mock_fixtures_dir": PROJECT_ROOT / "fixtures",
            "name_variants_file": variants,
            "mock_speed_factor": 5000,
            "mock_failure_rate": 0,
            "max_workers": 2,
            "sse_heartbeat_seconds": 0.05,
        }
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def upload(client: TestClient, content: str, **form: str) -> Any:
    return client.post("/jobs", files={"file": ("people.csv", content.encode("utf-8"))}, data=form)


def wait_until_finished(client: TestClient, job_id: str, timeout: float = 20.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        snapshot: dict[str, Any] = client.get(f"/jobs/{job_id}").json()
        if snapshot["state"] in ("completed", "cancelled"):
            return snapshot
        time.sleep(0.05)
    raise AssertionError("The job did not finish in time")


def test_upload_returns_the_job_id_and_the_validation_report_immediately(
    client: TestClient,
) -> None:
    response = upload(client, BRIEF_SAMPLE)

    body = response.json()
    assert response.status_code == 201
    assert body["total_people"] == 1
    assert body["report"]["counts"] == {"accepted": 1, "normalized": 0, "rejected": 3}
    assert body["events_url"] == f"/jobs/{body['job_id']}/events"


def test_snapshot_reports_progress_and_people(client: TestClient) -> None:
    job_id = upload(client, CSV_HEADER + "Pedro,Rodriguez,,r\nNemo,Nobody,,x\n").json()["job_id"]

    snapshot = wait_until_finished(client, job_id)

    assert snapshot["state"] == "completed"
    assert snapshot["progress"]["percent"] == 100
    assert [person["state"] for person in snapshot["people"]] == ["done", "done"]
    assert snapshot["people"][0]["cases_found"] == 188


def test_person_view_hides_warrant_status_everywhere(client: TestClient) -> None:
    job_id = upload(client, CSV_HEADER + "Pedro,Rodriguez,,r\n").json()["job_id"]
    wait_until_finished(client, job_id)

    response = client.get(f"/jobs/{job_id}/people/0")

    person = response.json()
    restricted = [case for case in person["cases"] if case["is_restricted"]]
    assert restricted and all(case["status"] == "Restricted by portal" for case in restricted)
    assert all(case["detail"] is None for case in restricted)
    assert "Warrant" not in response.text


def test_person_view_includes_details_groups_and_discard_counts(client: TestClient) -> None:
    job_id = upload(client, CSV_HEADER + "Pedro,Rodriguez,,r\n").json()["job_id"]
    wait_until_finished(client, job_id)

    person = client.get(f"/jobs/{job_id}/people/0").json()

    detailed = [case for case in person["cases"] if case["detail"] is not None]
    assert len(detailed) == person["details_loaded"] == 59
    assert person["discarded"] == 5
    assert person["identity_groups"]
    assert all(case["group_id"] is not None for case in person["cases"])


def test_event_stream_replays_the_whole_finished_job(client: TestClient) -> None:
    job_id = upload(client, CSV_HEADER + "Nemo,Nobody,,x\n").json()["job_id"]
    wait_until_finished(client, job_id)

    with client.stream("GET", f"/jobs/{job_id}/events") as response:
        text = "".join(response.iter_text())

    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-accel-buffering"] == "no"
    assert response.headers["cache-control"] == "no-cache"
    assert text.startswith("id: 1\nevent: job_created")
    assert "event: job_complete" in text


def test_reconnecting_with_last_event_id_resumes_after_it(client: TestClient) -> None:
    job_id = upload(client, CSV_HEADER + "Nemo,Nobody,,x\n").json()["job_id"]
    wait_until_finished(client, job_id)

    with client.stream("GET", f"/jobs/{job_id}/events", headers={"Last-Event-ID": "2"}) as response:
        frames = "".join(response.iter_text())

    first_id = int(frames.split("\n", 1)[0].removeprefix("id: "))
    assert first_id == 3
    assert "id: 2\n" not in frames


def test_stream_data_is_a_typed_json_event(client: TestClient) -> None:
    job_id = upload(client, CSV_HEADER + "Nemo,Nobody,,x\n").json()["job_id"]
    wait_until_finished(client, job_id)

    with client.stream("GET", f"/jobs/{job_id}/events") as response:
        text = "".join(response.iter_text())

    data_line = next(line for line in text.split("\n") if line.startswith("data: "))
    event = json.loads(data_line.removeprefix("data: "))
    assert {"id", "type", "job_id", "timestamp", "message", "data"} <= event.keys()


def test_files_with_structural_problems_are_rejected_with_the_report(client: TestClient) -> None:
    response = upload(client, "name,age\nJohn,3\n")

    assert response.status_code == 422
    assert response.json()["report"]["file_issues"][0]["code"] == "missing_required_columns"


def test_a_file_without_searchable_rows_is_rejected(client: TestClient) -> None:
    response = upload(client, CSV_HEADER + ",Smith,,x\n")

    assert response.status_code == 422
    assert response.json()["detail"] == "The file has no row that can be searched"


def test_unknown_jobs_and_people_return_404(client: TestClient) -> None:
    assert client.get("/jobs/nope").status_code == 404
    assert client.get("/jobs/nope/events").status_code == 404
    job_id = upload(client, CSV_HEADER + "Nemo,Nobody,,x\n").json()["job_id"]
    assert client.get(f"/jobs/{job_id}/people/9").status_code == 404


def test_jobs_are_listed_newest_first(client: TestClient) -> None:
    first = upload(client, CSV_HEADER + "Nemo,Nobody,,x\n").json()["job_id"]
    second = upload(client, CSV_HEADER + "Zed,Nobody,,y\n").json()["job_id"]

    listed = [item["job_id"] for item in client.get("/jobs").json()]

    assert listed == [second, first]


def test_parallelism_form_field_is_clamped_by_the_server(client: TestClient) -> None:
    body = upload(client, CSV_HEADER + "Nemo,Nobody,,x\n", parallelism="50").json()

    assert body["parallelism"] == 2


def test_cancelling_a_finished_job_is_harmless(client: TestClient) -> None:
    job_id = upload(client, CSV_HEADER + "Nemo,Nobody,,x\n").json()["job_id"]
    wait_until_finished(client, job_id)

    response = client.post(f"/jobs/{job_id}/cancel")

    assert response.status_code == 200
    assert response.json()["state"] == "completed"


def test_retry_failed_on_a_job_without_failures_changes_nothing(client: TestClient) -> None:
    job_id = upload(client, CSV_HEADER + "Nemo,Nobody,,x\n").json()["job_id"]
    wait_until_finished(client, job_id)

    response = client.post(f"/jobs/{job_id}/retry-failed")

    assert response.status_code == 200
    assert response.json()["state"] == "completed"


def test_captcha_solved_endpoint_validates_job_and_person(client: TestClient) -> None:
    job_id = upload(client, CSV_HEADER + "Nemo,Nobody,,x\n").json()["job_id"]

    assert client.post(f"/jobs/{job_id}/people/0/captcha-solved").status_code == 204
    assert client.post(f"/jobs/{job_id}/people/9/captcha-solved").status_code == 404
    assert client.post("/jobs/nope/people/0/captcha-solved").status_code == 404


def test_validation_returns_the_report_without_creating_a_job(client: TestClient) -> None:
    files = {"file": ("people.csv", BRIEF_SAMPLE.encode("utf-8"))}

    response = client.post("/jobs/validate", files=files)

    body = response.json()
    assert response.status_code == 200
    assert body["ready_people"] == 1
    assert body["report"]["counts"] == {"accepted": 1, "normalized": 0, "rejected": 3}
    assert body["max_parallelism"] == 2
    assert client.get("/jobs").json() == []


def test_validation_reports_file_level_problems_instead_of_failing(client: TestClient) -> None:
    files = {"file": ("people.csv", b"name,age\nJohn,3\n")}

    body = client.post("/jobs/validate", files=files).json()

    assert body["ready_people"] == 0
    assert body["report"]["file_issues"][0]["code"] == "missing_required_columns"


def test_public_configuration_tells_the_frontend_its_limits(client: TestClient) -> None:
    config = client.get("/config").json()

    assert config["provider"] == "mock"
    assert config["max_workers"] == 2
    assert config["csv_max_rows"] > 0


def test_raw_source_of_a_case_shows_the_search_item_and_the_detail(client: TestClient) -> None:
    job_id = upload(client, CSV_HEADER + "Pedro,Rodriguez,,r\n").json()["job_id"]
    wait_until_finished(client, job_id)
    person = client.get(f"/jobs/{job_id}/people/0").json()
    detailed = next(case for case in person["cases"] if case["detail"] is not None)

    raw = client.get(f"/jobs/{job_id}/people/0/cases/{detailed['case_key']}/raw").json()

    assert raw["search_item"]["caseNumber"] == detailed["case_number"]
    assert raw["detail_response"]["data"]["bfAmount"]
    assert raw["search_source_url"].startswith("mock://")
    assert raw["is_restricted"] is False


def test_raw_source_of_a_restricted_case_hides_the_warrant_status(client: TestClient) -> None:
    job_id = upload(client, CSV_HEADER + "Pedro,Rodriguez,,r\n").json()["job_id"]
    wait_until_finished(client, job_id)
    person = client.get(f"/jobs/{job_id}/people/0").json()
    restricted = next(case for case in person["cases"] if case["is_restricted"])

    response = client.get(f"/jobs/{job_id}/people/0/cases/{restricted['case_key']}/raw")

    raw = response.json()
    assert raw["is_restricted"] is True
    assert raw["search_item"]["caseStatus"] == "Restricted by portal"
    assert raw["detail_response"] is None
    assert "Warrant" not in response.text


def test_raw_source_of_an_unknown_case_is_not_found(client: TestClient) -> None:
    job_id = upload(client, CSV_HEADER + "Nemo,Nobody,,x\n").json()["job_id"]
    wait_until_finished(client, job_id)

    assert client.get(f"/jobs/{job_id}/people/0/cases/NOPE/raw").status_code == 404
