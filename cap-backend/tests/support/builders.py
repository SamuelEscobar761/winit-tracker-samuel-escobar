from datetime import date

from app.cases.keys import build_case_key
from app.cases.models import CaseSummary
from app.cases.status import CaseStatus
from app.people.models import Person


def make_case(
    caption: str = "SMITH, JOHN",
    date_of_birth: date | None = None,
    drivers_license: str | None = None,
    status: CaseStatus = CaseStatus.ACTIVE,
    case_number: str = "25IN-000001",
) -> CaseSummary:
    return CaseSummary(
        portal_case_id="1",
        case_number=case_number,
        case_key=build_case_key(case_number),
        citation_number=None,
        file_date=None,
        caption=caption,
        drivers_license=drivers_license,
        date_of_birth=date_of_birth,
        status=status,
        raw_status=status.value,
    )


def make_person(
    first_name: str = "John",
    last_name: str = "Smith",
    date_of_birth: date | None = None,
) -> Person:
    return Person(first_name=first_name, last_name=last_name, date_of_birth=date_of_birth)
