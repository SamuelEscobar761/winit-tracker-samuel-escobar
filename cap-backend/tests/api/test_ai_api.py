import shutil
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import create_app
from tests.api.test_jobs_api import upload, wait_until_finished
from tests.support.engine_harness import CSV_HEADER, PROJECT_ROOT

ClientFactory = Callable[..., TestClient]


@pytest.fixture
def make_client(tmp_path: Path) -> Iterator[ClientFactory]:
    opened: list[Any] = []

    def create(**overrides: object) -> TestClient:
        variants = tmp_path / "name_variants.json"
        shutil.copy(PROJECT_ROOT / "config" / "name_variants.json", variants)
        values: dict[str, object] = {
            "mock_fixtures_dir": PROJECT_ROOT / "fixtures",
            "name_variants_file": variants,
            "portal_rules_dir": tmp_path / "rules",
            "mock_speed_factor": 5000,
            "mock_failure_rate": 0,
            "max_workers": 2,
        }
        values.update(overrides)
        manager = TestClient(create_app(Settings.model_validate(values)))
        opened.append(manager)
        return manager.__enter__()

    yield create
    for manager in opened:
        manager.__exit__(None, None, None)


def finished_person(client: TestClient) -> tuple[str, dict[str, Any]]:
    job_id = upload(client, CSV_HEADER + "Pedro,Rodriguez,,r\n").json()["job_id"]
    wait_until_finished(client, job_id)
    return job_id, client.get(f"/jobs/{job_id}/people/0").json()


def case_with_detail(person: dict[str, Any]) -> dict[str, Any]:
    return next(case for case in person["cases"] if case["detail"] is not None)


def test_ai_is_off_by_default_and_says_why(make_client: ClientFactory) -> None:
    client = make_client()

    body = client.get("/ai/status").json()

    assert body["available"] is False
    assert body["mode"] == "off"
    assert body["reason"] == "AI_ENABLED is false"


def test_every_agent_endpoint_is_unavailable_when_ai_is_off(make_client: ClientFactory) -> None:
    client = make_client()
    job_id, person = finished_person(client)
    key = person["cases"][0]["case_key"]
    base = f"/ai/jobs/{job_id}/people/0"

    responses = [
        client.post(f"{base}/cases/{key}/explain"),
        client.post(f"{base}/insight"),
        client.post(f"{base}/cases/{key}/notices"),
    ]

    assert [response.status_code for response in responses] == [503, 503, 503]


def test_the_core_pipeline_is_identical_with_ai_off(make_client: ClientFactory) -> None:
    client = make_client()

    _, person = finished_person(client)

    assert person["cases_found"] == 188
    assert all("ai_generated" not in case for case in person["cases"])


def test_a_match_explanation_keeps_the_deterministic_label(make_client: ClientFactory) -> None:
    client = make_client(ai_enabled=True, ai_offline_mock=True)
    job_id, person = finished_person(client)
    case = person["cases"][0]

    response = client.post(f"/ai/jobs/{job_id}/people/0/cases/{case['case_key']}/explain")

    assert response.status_code == 200
    assert response.json()["label"] == case["match_label"]
    assert response.json()["ai_generated"] is True


def test_an_insight_cites_cases_of_that_person(make_client: ClientFactory) -> None:
    client = make_client(ai_enabled=True, ai_offline_mock=True)
    job_id, person = finished_person(client)
    keys = {case["case_key"] for case in person["cases"]}

    response = client.post(f"/ai/jobs/{job_id}/people/0/insight")

    assert response.status_code == 200
    findings = response.json()["findings"]
    assert findings
    assert all(set(finding["case_keys"]) <= keys for finding in findings)


def test_unknown_case_and_person_are_404(make_client: ClientFactory) -> None:
    client = make_client(ai_enabled=True, ai_offline_mock=True)
    job_id, _ = finished_person(client)

    assert client.post(f"/ai/jobs/{job_id}/people/0/cases/nope/explain").status_code == 404
    assert client.post(f"/ai/jobs/{job_id}/people/9/insight").status_code == 404


def test_the_rules_screen_data_lists_the_active_rules_and_history(
    make_client: ClientFactory,
) -> None:
    client = make_client()

    body = client.get("/rules").json()

    assert body["active"]["version"] == 1
    assert body["versions"] == [1]
    assert body["changelog"][0]["actor"] == "bootstrap"
    assert body["incidents"] == []


def test_rollback_to_an_unknown_version_is_404(make_client: ClientFactory) -> None:
    client = make_client()

    assert client.post("/rules/rollback", json={"version": 7}).status_code == 404


def test_repairs_need_ai(make_client: ClientFactory) -> None:
    client = make_client()

    assert client.post("/rules/incidents/x/repair").status_code == 503
    assert client.post("/rules/proposals/x/approve").status_code == 503


def test_unknown_incident_and_proposal_are_404_when_ai_is_on(make_client: ClientFactory) -> None:
    client = make_client(ai_enabled=True, ai_offline_mock=True)

    assert client.post("/rules/incidents/x/repair").status_code == 404
    assert client.post("/rules/proposals/x/approve").status_code == 404
    assert client.post("/rules/proposals/x/reject").status_code == 404


def test_rules_endpoints_require_a_session_in_live_mode(make_client: ClientFactory) -> None:
    client = make_client(cap_provider="live", admin_token="secret")

    assert client.get("/rules").status_code == 401
    assert client.get("/ai/status").status_code == 401
