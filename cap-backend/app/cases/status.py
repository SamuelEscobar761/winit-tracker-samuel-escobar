from enum import StrEnum


class CaseStatus(StrEnum):
    ACTIVE = "Active"
    CLOSED = "Closed"
    INACTIVE = "Inactive"
    AR_FINE = "AR Fine"
    WARRANT = "Warrant"
    PROBATION = "Probation"
    PENDING_ADJUDICATION = "Pending Adjudication"
    TRAFFIC_SCHOOL_PENDING = "Traffic School Pending"
    UNKNOWN = "Unknown"


STATUSES_WITHOUT_DETAIL = frozenset({CaseStatus.CLOSED, CaseStatus.WARRANT})

_STATUS_BY_PORTAL_TEXT = {status.value.lower(): status for status in CaseStatus}


def parse_case_status(raw_status: str | None) -> CaseStatus:
    portal_text = (raw_status or "").strip().lower()
    return _STATUS_BY_PORTAL_TEXT.get(portal_text, CaseStatus.UNKNOWN)
