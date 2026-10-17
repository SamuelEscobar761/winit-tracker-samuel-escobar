import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from app.cases.matching.analyzer import PersonCaseAnalysis
from app.cases.models import CaseDetail
from app.csv_import.models import ImportReport
from app.jobs.event_log import EventLog
from app.people.models import Person
from app.people.variants.config import NameVariantStrategy


class PersonState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    BLOCKED_CAPTCHA = "blocked_captcha"
    CANCELLED = "cancelled"


TERMINAL_PERSON_STATES = frozenset(
    {
        PersonState.DONE,
        PersonState.FAILED,
        PersonState.BLOCKED_CAPTCHA,
        PersonState.CANCELLED,
    }
)
RETRYABLE_PERSON_STATES = frozenset({PersonState.FAILED, PersonState.BLOCKED_CAPTCHA})


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class SourceSnapshot:
    url: str
    scraped_at: datetime
    payload: dict[str, Any]


@dataclass
class PersonRun:
    index: int
    line_number: int
    person: Person
    state: PersonState = PersonState.QUEUED
    lane: int | None = None
    query: str | None = None
    strategy: NameVariantStrategy | None = None
    analysis: PersonCaseAnalysis | None = None
    truncated: bool = False
    details: dict[str, CaseDetail] = field(default_factory=dict)
    detail_errors: dict[str, str] = field(default_factory=dict)
    search_source: tuple[str, datetime] | None = None
    detail_snapshots: dict[str, SourceSnapshot] = field(default_factory=dict)
    failure_reason: str | None = None
    captcha_pending: bool = False
    captcha_resolved: asyncio.Event = field(default_factory=asyncio.Event)

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_PERSON_STATES

    def reset_for_retry(self) -> None:
        self.state = PersonState.QUEUED
        self.lane = None
        self.failure_reason = None
        self.captcha_pending = False
        self.captcha_resolved.clear()


@dataclass
class Job:
    id: str
    created_at: datetime
    parallelism: int
    report: ImportReport
    people: list[PersonRun]
    event_log: EventLog
    state: JobState = JobState.QUEUED
    cancel_requested: bool = False
    running_count: int = 0

    def count_people(self, state: PersonState) -> int:
        return sum(1 for run in self.people if run.state is state)

    @property
    def all_people_terminal(self) -> bool:
        return all(run.is_terminal for run in self.people)
