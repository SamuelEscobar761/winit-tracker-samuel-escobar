import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

from app.cases.matching.analyzer import analyze_person_cases, limit_cases
from app.cases.matching.case_filter import PersonCaseFilter
from app.cases.models import CaseSummary
from app.config.settings import Settings
from app.jobs.activity import Activity, current_activity
from app.jobs.events import EventType
from app.jobs.models import Job, PersonRun, PersonState, SourceSnapshot
from app.jobs.observations import ObservationRecorder
from app.jobs.progress import build_progress_data
from app.jobs.retry import RetryListener, RetryPolicy
from app.people.variants.config import NameVariantConfig, NameVariantStrategy
from app.people.variants.forms import NameForms, build_name_forms
from app.people.variants.queries import SearchAttempt, generate_search_attempts
from app.providers.base import CapProvider
from app.providers.errors import (
    CapDown,
    CaptchaRequired,
    DetailNotAvailable,
    NoResults,
    NoSearchableQuery,
    ProviderError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


_STATE_LABELS = {
    PersonState.QUEUED: "queued",
    PersonState.RUNNING: "running",
    PersonState.DONE: "done",
    PersonState.FAILED: "failed",
    PersonState.BLOCKED_CAPTCHA: "blocked by a CAPTCHA",
    PersonState.CANCELLED: "cancelled",
}


class JobCancelled(Exception):
    pass


class CaptchaBlocked(Exception):
    pass


@dataclass(frozen=True)
class _Winner:
    attempt: SearchAttempt
    caption: str


class PersonProcessor:
    def __init__(
        self,
        settings: Settings,
        variants: NameVariantConfig,
        retry_policy: RetryPolicy,
        recorder: ObservationRecorder | None,
    ) -> None:
        self._settings = settings
        self._variants = variants
        self._retry = retry_policy
        self._recorder = recorder

    async def run(self, job: Job, run: PersonRun, provider: CapProvider, lane: int) -> None:
        token = current_activity.set(Activity(job.event_log, run.index, lane))
        run.state = PersonState.RUNNING
        run.lane = lane
        try:
            await self._process(job, run, provider)
        except CapDown:
            run.state = PersonState.QUEUED
            raise
        except JobCancelled:
            self._finish(job, run, PersonState.CANCELLED, "The job was cancelled")
        except CaptchaBlocked:
            self._finish(
                job, run, PersonState.BLOCKED_CAPTCHA, "The CAPTCHA was not solved in time"
            )
        except ProviderError as error:
            self._finish(job, run, PersonState.FAILED, str(error) or type(error).__name__)
        except Exception:
            logger.exception("Unexpected error while processing person %s", run.index)
            self._finish(job, run, PersonState.FAILED, "Unexpected error")
        finally:
            current_activity.reset(token)

    async def _process(self, job: Job, run: PersonRun, provider: CapProvider) -> None:
        attempts = generate_search_attempts(run.person, self._variants)
        if not attempts:
            raise NoSearchableQuery("No search text of 4 to 20 characters can be built")
        forms = build_name_forms(run.person, self._variants)
        summaries, winner = await self._search_attempts(job, run, provider, attempts, forms)
        analysis = analyze_person_cases(run.person, summaries, forms)
        run.analysis, run.truncated = limit_cases(analysis, self._settings.max_cases_per_person)
        await self._remember_winner(run, winner, attempts[0])
        self._announce_found(job, run)
        await self._load_details(job, run, provider)
        self._finish(job, run, PersonState.DONE, None)

    async def _search_attempts(
        self,
        job: Job,
        run: PersonRun,
        provider: CapProvider,
        attempts: tuple[SearchAttempt, ...],
        forms: NameForms,
    ) -> tuple[list[CaseSummary], _Winner | None]:
        summaries: dict[tuple[str, str], CaseSummary] = {}
        winner: _Winner | None = None
        for position, attempt in enumerate(attempts, start=1):
            found = await self._run_attempt(job, run, provider, attempt, position, len(attempts))
            summaries.update({(case.case_key, case.caption): case for case in found})
            kept = PersonCaseFilter(run.person, forms).apply(found).kept
            winner = winner or (_Winner(attempt, kept[0].caption) if kept else None)
            if kept and self._variants.stop_after_first_with_results:
                break
        return list(summaries.values()), winner

    async def _run_attempt(
        self,
        job: Job,
        run: PersonRun,
        provider: CapProvider,
        attempt: SearchAttempt,
        position: int,
        total: int,
    ) -> tuple[CaseSummary, ...]:
        name = f"{run.person.first_name} {run.person.last_name}"
        job.event_log.append(
            EventType.SEARCHING,
            f"Searching {name}…",
            {
                "query": attempt.query,
                "strategy": attempt.strategy.value,
                "attempt": position,
                "of": total,
            },
            run.index,
            run.lane,
        )
        try:
            response = await self._guarded(
                job,
                run,
                lambda: provider.search(attempt.query),
                self._settings.search_timeout_seconds,
            )
        except NoResults:
            return ()
        run.search_source = (response.source_url, response.scraped_at)
        return response.cases

    async def _remember_winner(
        self, run: PersonRun, winner: _Winner | None, first_attempt: SearchAttempt
    ) -> None:
        chosen = winner.attempt if winner else first_attempt
        run.query, run.strategy = chosen.query, chosen.strategy
        if winner is None or winner.attempt.strategy is NameVariantStrategy.AS_WRITTEN:
            return
        if self._recorder is None:
            return
        csv_name = f"{run.person.first_name} {run.person.last_name}"
        await self._recorder.record(
            csv_name, winner.attempt.query, winner.caption, winner.attempt.strategy
        )

    async def _load_details(self, job: Job, run: PersonRun, provider: CapProvider) -> None:
        assert run.analysis is not None and run.query is not None
        eligible = [item.case for item in run.analysis.cases if item.case.is_detail_eligible]
        limit = self._settings.cap_max_details_per_person
        for case in eligible if limit is None else eligible[:limit]:
            if case.case_key in run.details:
                continue
            await self._load_one_detail(job, run, provider, run.query, case)

    async def _load_one_detail(
        self, job: Job, run: PersonRun, provider: CapProvider, query: str, case: CaseSummary
    ) -> None:
        try:
            response = await self._guarded(
                job,
                run,
                lambda: provider.fetch_detail(query, case.case_number),
                self._settings.detail_timeout_seconds,
            )
        except (CapDown, CaptchaBlocked, JobCancelled):
            raise
        except DetailNotAvailable as error:
            self._record_detail_failure(job, run, case, str(error))
        except ProviderError as error:
            self._record_detail_failure(job, run, case, str(error) or type(error).__name__)
        else:
            run.details[case.case_key] = response.detail
            run.detail_snapshots[case.case_key] = SourceSnapshot(
                response.source_url, response.scraped_at, response.raw_payload
            )
            job.event_log.append(
                EventType.DETAIL_LOADED,
                f"Loaded details of {case.case_number}",
                {"case_key": case.case_key},
                run.index,
                run.lane,
            )

    def _record_detail_failure(
        self, job: Job, run: PersonRun, case: CaseSummary, reason: str
    ) -> None:
        run.detail_errors[case.case_key] = reason
        job.event_log.append(
            EventType.DETAIL_FAILED,
            f"Could not load details of {case.case_number}",
            {"case_key": case.case_key, "reason": reason},
            run.index,
            run.lane,
        )

    async def _guarded(
        self,
        job: Job,
        run: PersonRun,
        operation: Callable[[], Awaitable[T]],
        timeout_seconds: float,
    ) -> T:
        while True:
            self._raise_if_cancelled(job)
            try:
                return await self._retry.run(
                    operation, timeout_seconds, self._retry_listener(job, run)
                )
            except CaptchaRequired:
                await self._wait_for_captcha(job, run)

    def _retry_listener(self, job: Job, run: PersonRun) -> RetryListener:
        async def notify(attempt: int, error: ProviderError, delay: float) -> None:
            job.event_log.append(
                EventType.RETRYING,
                f"Retrying after: {error}",
                {
                    "attempt": attempt,
                    "delay_seconds": round(delay, 2),
                    "error": type(error).__name__,
                },
                run.index,
                run.lane,
            )

        return notify

    async def _wait_for_captcha(self, job: Job, run: PersonRun) -> None:
        job.event_log.append(
            EventType.CAPTCHA_REQUIRED, "CAPTCHA required", {}, run.index, run.lane
        )
        run.captcha_pending = True
        try:
            await asyncio.wait_for(run.captcha_resolved.wait(), self._settings.captcha_wait_seconds)
        except TimeoutError:
            raise CaptchaBlocked from None
        finally:
            run.captcha_pending = False
        run.captcha_resolved.clear()
        self._raise_if_cancelled(job)
        job.event_log.append(EventType.CAPTCHA_RESOLVED, "CAPTCHA solved", {}, run.index, run.lane)

    def _raise_if_cancelled(self, job: Job) -> None:
        if job.cancel_requested:
            raise JobCancelled

    def _announce_found(self, job: Job, run: PersonRun) -> None:
        assert run.analysis is not None
        eligible = sum(1 for item in run.analysis.cases if item.case.is_detail_eligible)
        data = {
            "cases": len(run.analysis.cases),
            "eligible_for_details": eligible,
            "discarded": run.analysis.discarded_total,
            "identity_groups": len(run.analysis.identity_groups),
            "truncated": run.truncated,
        }
        count = len(run.analysis.cases)
        message = f"Found {count} case{'s' if count != 1 else ''}"
        job.event_log.append(EventType.FOUND, message, data, run.index, run.lane)

    def _finish(self, job: Job, run: PersonRun, state: PersonState, reason: str | None) -> None:
        run.state = state
        run.failure_reason = reason
        failed = state in (PersonState.FAILED, PersonState.BLOCKED_CAPTCHA)
        event_type = EventType.PERSON_FAILED if failed else EventType.PERSON_COMPLETED
        name = f"{run.person.first_name} {run.person.last_name}"
        message = f"{name}: {_STATE_LABELS[state]}" + (f" ({reason})" if reason else "")
        job.event_log.append(
            event_type, message, {"state": state.value, "reason": reason}, run.index, run.lane
        )
        job.event_log.append(EventType.PROGRESS, "Progress", build_progress_data(job))
