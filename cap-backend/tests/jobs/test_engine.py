import asyncio
import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from app.cases.status import CaseStatus
from app.jobs.events import EventType
from app.jobs.models import Job, JobState, PersonState
from app.providers.errors import CapDown, CaptchaRequired, ProviderTimeout, SessionExpired
from app.providers.mock.failures import ScriptedFailures
from tests.support.engine_harness import (
    FIXTURES,
    event_types,
    running_engine,
)

PEDRO = "Pedro,Rodriguez,,ref-1\n"
JOHN = "John,Smith,,ref-2\n"
NOBODY = "Nemo,Nobody,,ref-3\n"


async def test_job_runs_from_csv_to_completion_with_ordered_events(tmp_path: Path) -> None:
    async with running_engine(tmp_path) as engine:
        job = await engine.submit(PEDRO + NOBODY)
        await engine.finish(job)

    types = event_types(job)
    assert job.state is JobState.COMPLETED
    assert types[0] is EventType.JOB_CREATED
    assert types[1] is EventType.JOB_STARTED
    assert types[-1] is EventType.JOB_COMPLETE
    assert [event.id for event in job.event_log.events_after(0)] == list(range(1, len(types) + 1))
    assert all(run.state is PersonState.DONE for run in job.people)


async def test_found_event_reports_how_many_cases_belong_to_the_person(tmp_path: Path) -> None:
    async with running_engine(tmp_path) as engine:
        job = await engine.submit(PEDRO)
        await engine.finish(job)

    found = next(event for event in job.event_log.events_after(0) if event.type is EventType.FOUND)
    assert found.message == "Found 188 cases"
    assert found.data["discarded"] == 5
    assert found.data["eligible_for_details"] == 59


async def test_details_are_loaded_for_every_eligible_case_and_never_for_warrants(
    tmp_path: Path,
) -> None:
    async with running_engine(tmp_path) as engine:
        job = await engine.submit(JOHN)
        await engine.finish(job)

    run = job.people[0]
    assert run.analysis is not None
    eligible = [item.case for item in run.analysis.cases if item.case.is_detail_eligible]
    assert len(eligible) == 65
    assert set(run.details) == {case.case_key for case in eligible}
    assert all(
        item.case.status is not CaseStatus.WARRANT
        for item in run.analysis.cases
        if item.case.case_key in run.details
    )


async def test_person_without_cases_finishes_with_zero_cases(tmp_path: Path) -> None:
    async with running_engine(tmp_path) as engine:
        job = await engine.submit(NOBODY)
        await engine.finish(job)

    run = job.people[0]
    assert run.state is PersonState.DONE
    assert run.analysis is not None and run.analysis.cases == ()


async def test_birth_date_in_the_csv_narrows_the_results(tmp_path: Path) -> None:
    async with running_engine(tmp_path) as engine:
        job = await engine.submit("John,Smith,1959-10-19,ref\n")
        await engine.finish(job)

    run = job.people[0]
    assert run.analysis is not None
    assert len(run.analysis.cases) == 19


async def test_case_cap_marks_the_result_as_truncated(tmp_path: Path) -> None:
    async with running_engine(tmp_path, max_cases_per_person=10) as engine:
        job = await engine.submit(PEDRO)
        await engine.finish(job)

    run = job.people[0]
    assert run.analysis is not None
    assert len(run.analysis.cases) == 10
    assert run.truncated


async def test_detail_limit_is_optional_and_respected_when_set(tmp_path: Path) -> None:
    async with running_engine(tmp_path, cap_max_details_per_person=2) as engine:
        job = await engine.submit(PEDRO)
        await engine.finish(job)

    assert len(job.people[0].details) == 2


async def test_throttle_pauses_are_reported_as_waiting_events(tmp_path: Path) -> None:
    async with running_engine(tmp_path) as engine:
        job = await engine.submit(NOBODY)
        await engine.finish(job)

    waits = [event for event in job.event_log.events_after(0) if event.type is EventType.WAITING]
    assert len(waits) == 2
    assert waits[0].person_index == 0 and waits[0].data["seconds"] == 5.0


async def test_session_expiry_is_retried_and_reported(tmp_path: Path) -> None:
    failures = ScriptedFailures([SessionExpired("expired"), None])
    async with running_engine(tmp_path, failures) as engine:
        job = await engine.submit(NOBODY)
        await engine.finish(job)

    assert EventType.RETRYING in event_types(job)
    assert job.people[0].state is PersonState.DONE


async def test_exhausted_retries_fail_only_that_person(tmp_path: Path) -> None:
    failures = ScriptedFailures([ProviderTimeout("slow")] * 3)
    async with running_engine(tmp_path, failures) as engine:
        job = await engine.submit(NOBODY + PEDRO)
        await engine.finish(job)

    failed, succeeded = job.people
    assert failed.state is PersonState.FAILED
    assert failed.failure_reason == "slow"
    assert succeeded.state is PersonState.DONE
    assert job.state is JobState.COMPLETED
    assert EventType.PERSON_FAILED in event_types(job)


async def test_portal_down_pauses_everything_instead_of_failing_people(tmp_path: Path) -> None:
    failures = ScriptedFailures([CapDown("maintenance")])
    async with running_engine(tmp_path, failures) as engine:
        job = await engine.submit(NOBODY)
        await engine.finish(job)

    types = event_types(job)
    assert types.index(EventType.CAP_DOWN) < types.index(EventType.CAP_RECOVERED)
    assert EventType.PERSON_FAILED not in types
    assert job.people[0].state is PersonState.DONE


async def test_captcha_waits_for_the_human_and_then_continues(tmp_path: Path) -> None:
    failures = ScriptedFailures([CaptchaRequired("captcha")])
    async with running_engine(tmp_path, failures, captcha_wait_seconds=5.0) as engine:
        job = await engine.submit(NOBODY)
        await engine.wait_for_event(job, EventType.CAPTCHA_REQUIRED)
        engine.system.service.resolve_captcha(job.id, 0)
        await engine.finish(job)

    types = event_types(job)
    assert EventType.CAPTCHA_RESOLVED in types
    assert job.people[0].state is PersonState.DONE


async def test_unsolved_captcha_blocks_the_person_and_retry_resumes_it(tmp_path: Path) -> None:
    failures = ScriptedFailures([CaptchaRequired("captcha")])
    async with running_engine(tmp_path, failures, captcha_wait_seconds=0.05) as engine:
        job = await engine.submit(NOBODY + PEDRO)
        await engine.finish(job)
        assert person_state(job, 0) is PersonState.BLOCKED_CAPTCHA
        assert person_state(job, 1) is PersonState.DONE

        await engine.system.service.retry_failed(job.id)
        await engine.finish(job)

    assert person_state(job, 0) is PersonState.DONE
    assert EventType.JOB_RETRY in event_types(job)
    assert job.state is JobState.COMPLETED


async def test_retry_only_reruns_failed_people(tmp_path: Path) -> None:
    failures = ScriptedFailures([ProviderTimeout("slow")] * 3)
    async with running_engine(tmp_path, failures) as engine:
        job = await engine.submit(NOBODY + NOBODY.replace("Nemo", "Zed"))
        await engine.finish(job)
        searches_before = event_types(job).count(EventType.SEARCHING)

        await engine.system.service.retry_failed(job.id)
        await engine.finish(job)

    searches_after = event_types(job).count(EventType.SEARCHING)
    assert searches_after - searches_before == 1
    assert all(run.state is PersonState.DONE for run in job.people)


async def test_cancel_stops_queued_work_and_closes_the_log(tmp_path: Path) -> None:
    failures = ScriptedFailures([CaptchaRequired("captcha")])
    async with running_engine(tmp_path, failures, captcha_wait_seconds=5.0) as engine:
        job = await engine.submit(NOBODY + PEDRO + JOHN)
        await engine.wait_for_event(job, EventType.CAPTCHA_REQUIRED)

        await engine.system.service.cancel_job(job.id)
        await engine.finish(job)

    assert job.state is JobState.CANCELLED
    assert [run.state for run in job.people] == [PersonState.CANCELLED] * 3
    assert event_types(job)[-1] is EventType.JOB_CANCELLED
    assert job.event_log.is_closed


async def test_requested_parallelism_is_capped_by_the_server_limit(tmp_path: Path) -> None:
    async with running_engine(tmp_path, max_workers=2) as engine:
        job = await engine.submit(NOBODY, parallelism=99)
        await engine.finish(job)

    assert job.parallelism == 2


async def test_two_workers_share_one_job(tmp_path: Path) -> None:
    people = "".join(f"Nemo{letter},Nobody,,r{letter}\n" for letter in "abcd")
    async with running_engine(tmp_path, max_workers=2) as engine:
        job = await engine.submit(people, parallelism=2)
        await engine.finish(job)

    assert {run.lane for run in job.people} == {0, 1}


async def test_empty_import_cannot_become_a_job(tmp_path: Path) -> None:
    from app.jobs.service import EmptyJob

    async with running_engine(tmp_path) as engine:
        with pytest.raises(EmptyJob):
            await engine.submit(",Smith,,x\n")


def person_state(job: Job, index: int) -> PersonState:
    return job.people[index].state


def write_catalog_with_compound_surname(directory: Path) -> None:
    for name in ("select_26IN-055186.json", "select_25IN-169374.json"):
        shutil.copy(FIXTURES / name, directory / name)
    search = {
        "data": [
            {
                "caseId": "1",
                "caseNumber": "25IN-000001",
                "citationNumber": "1",
                "fileDate": "1/1/2020",
                "caseCaption": "GARCIA, MARIA",
                "driversLicense": "",
                "dateOfBirth": "",
                "caseStatus": "Closed",
            }
        ],
        "result": 0,
        "message": "Found 1 Case(s)",
    }
    (directory / "search_garcia.json").write_text(json.dumps(search), encoding="utf-8")
    catalog = {
        "searches": [{"canonical_query": "garcia, maria", "file": "search_garcia.json"}],
        "details": {},
        "templates": {
            "proof_of_correction": "select_26IN-055186.json",
            "payment_plan": "select_25IN-169374.json",
        },
    }
    (directory / "mock_catalog.json").write_text(json.dumps(catalog), encoding="utf-8")


async def test_name_variants_are_tried_in_order_and_the_winner_is_recorded(tmp_path: Path) -> None:
    catalog_dir = tmp_path / "fixtures"
    catalog_dir.mkdir()
    write_catalog_with_compound_surname(catalog_dir)
    async with running_engine(tmp_path, fixtures_dir=catalog_dir) as engine:
        job = await engine.submit("Maria,Garcia Lopez,,ref\n")
        await engine.finish(job)

    searches = [e for e in job.event_log.events_after(0) if e.type is EventType.SEARCHING]
    assert [event.data["query"] for event in searches] == ["garcia lopez, maria", "garcia, maria"]
    run = job.people[0]
    assert run.strategy is not None and run.strategy.value == "first_surname_only"
    assert run.analysis is not None and len(run.analysis.cases) == 1
    observations = json.loads(engine.variants_path.read_text(encoding="utf-8"))["observations"]
    assert observations == [
        {
            "csv_name": "Maria Garcia Lopez",
            "query_that_worked": "garcia, maria",
            "caption_seen": "GARCIA, MARIA",
            "strategy": "first_surname_only",
            "observed_on": date(2026, 10, 16).isoformat(),
        }
    ]


async def test_workers_stop_cleanly_when_the_pool_is_stopped(tmp_path: Path) -> None:
    async with running_engine(tmp_path) as engine:
        pool = engine.system.pool

    await asyncio.sleep(0)
    assert pool._tasks and all(task.done() for task in pool._tasks)
