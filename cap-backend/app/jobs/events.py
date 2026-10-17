from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class EventType(StrEnum):
    JOB_CREATED = "job_created"
    JOB_STARTED = "job_started"
    SEARCHING = "searching"
    WAITING = "waiting"
    RETRYING = "retrying"
    FOUND = "found"
    DETAIL_LOADED = "detail_loaded"
    DETAIL_FAILED = "detail_failed"
    CAPTCHA_REQUIRED = "captcha_required"
    CAPTCHA_RESOLVED = "captcha_resolved"
    CAP_DOWN = "cap_down"
    CAP_RECOVERED = "cap_recovered"
    PERSON_COMPLETED = "person_completed"
    PERSON_FAILED = "person_failed"
    PROGRESS = "progress"
    JOB_RETRY = "job_retry"
    JOB_COMPLETE = "job_complete"
    JOB_CANCELLED = "job_cancelled"


class JobEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    type: EventType
    job_id: str
    timestamp: datetime
    message: str
    person_index: int | None = None
    lane: int | None = None
    data: dict[str, Any] = {}
