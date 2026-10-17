from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.cases.models import CaseDetail, CaseSummary


@dataclass(frozen=True)
class SearchResponse:
    cases: tuple[CaseSummary, ...]
    raw_payload: dict[str, Any]
    source_url: str
    scraped_at: datetime


@dataclass(frozen=True)
class DetailResponse:
    detail: CaseDetail
    raw_payload: dict[str, Any]
    source_url: str
    scraped_at: datetime
