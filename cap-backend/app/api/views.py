from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from app.cases.matching.assessment import AssessedCase
from app.cases.models import RESTRICTED_STATUS_LABEL, CaseDetail, Charge
from app.csv_import.models import FileIssue, ImportReport, ImportRow, RowStatus
from app.jobs.models import Job, PersonRun, PersonState
from app.jobs.progress import build_progress_data


class ChargeView(BaseModel):
    statute: str
    description: str


class PaymentPlanView(BaseModel):
    past_amount_due: str | None
    monthly_amount: str | None
    remaining_balance: str | None


class DetailView(BaseModel):
    charges: list[ChargeView]
    amount_due: str | None
    proof_of_correction_required: bool
    has_payment_plan: bool
    payment_plan: PaymentPlanView | None
    is_extension_eligible: bool
    original_date: date | None
    extended_date: date | None
    notices: list[str]


class CaseView(BaseModel):
    case_number: str
    case_key: str
    citation_number: str | None
    file_date: date | None
    caption: str
    status: str
    is_restricted: bool
    date_of_birth: date | None
    drivers_license: str | None
    match_label: str
    match_reasons: list[str]
    group_id: int | None
    detail: DetailView | None
    detail_error: str | None


class IdentityGroupView(BaseModel):
    group_id: int
    date_of_birth: date | None
    drivers_license: str | None
    case_count: int
    case_keys: list[str]


class PersonSummaryView(BaseModel):
    index: int
    line_number: int
    first_name: str
    last_name: str
    date_of_birth: date | None
    external_ref: str | None
    state: str
    lane: int | None
    query: str | None
    strategy: str | None
    failure_reason: str | None
    cases_found: int
    eligible_for_details: int
    details_loaded: int
    discarded: int
    truncated: bool


class PersonView(PersonSummaryView):
    cases: list[CaseView]
    identity_groups: list[IdentityGroupView]
    discarded_by_reason: dict[str, int]


class RowView(BaseModel):
    line_number: int
    status: str
    original: dict[str, str]
    changes: list[dict[str, str]]
    issues: list[dict[str, str | None]]
    duplicate_of_line: int | None


class ReportView(BaseModel):
    encoding: str | None
    delimiter: str | None
    counts: dict[str, int]
    rows: list[RowView]
    file_issues: list[dict[str, str]]


class RawCaseView(BaseModel):
    case_key: str
    is_restricted: bool
    search_item: dict[str, Any]
    search_source_url: str | None
    search_scraped_at: datetime | None
    detail_response: dict[str, Any] | None
    detail_source_url: str | None
    detail_scraped_at: datetime | None


class ValidationView(BaseModel):
    report: ReportView
    ready_people: int
    max_parallelism: int
    default_parallelism: int


class ConfigView(BaseModel):
    provider: str
    max_workers: int
    default_parallelism: int
    csv_max_bytes: int
    csv_max_rows: int


class JobSnapshot(BaseModel):
    job_id: str
    state: str
    created_at: datetime
    parallelism: int
    progress: dict[str, int]
    people: list[PersonSummaryView]
    report: ReportView


class JobListItem(BaseModel):
    job_id: str
    state: str
    created_at: datetime
    total_people: int
    progress: dict[str, int]


def to_report_view(report: ImportReport) -> ReportView:
    return ReportView(
        encoding=report.encoding,
        delimiter=report.delimiter,
        counts={status.value: count for status, count in report.counts.items()},
        rows=[_to_row_view(row) for row in report.rows],
        file_issues=[_to_file_issue(issue) for issue in report.file_issues],
    )


def to_raw_case_view(run: PersonRun, item: AssessedCase) -> RawCaseView:
    case = item.case
    detail = run.detail_snapshots.get(case.case_key)
    source = run.search_source
    return RawCaseView(
        case_key=case.case_key,
        is_restricted=case.is_restricted,
        search_item=_redact_restricted(case.raw_item, case.is_restricted),
        search_source_url=source[0] if source else None,
        search_scraped_at=source[1] if source else None,
        detail_response=detail.payload if detail else None,
        detail_source_url=detail.url if detail else None,
        detail_scraped_at=detail.scraped_at if detail else None,
    )


def _redact_restricted(raw_item: dict[str, Any], is_restricted: bool) -> dict[str, Any]:
    if not is_restricted:
        return dict(raw_item)
    return {**raw_item, "caseStatus": RESTRICTED_STATUS_LABEL}


def to_job_snapshot(job: Job) -> JobSnapshot:
    return JobSnapshot(
        job_id=job.id,
        state=job.state.value,
        created_at=job.created_at,
        parallelism=job.parallelism,
        progress=build_progress_data(job),
        people=[to_person_summary(run) for run in job.people],
        report=to_report_view(job.report),
    )


def to_job_list_item(job: Job) -> JobListItem:
    return JobListItem(
        job_id=job.id,
        state=job.state.value,
        created_at=job.created_at,
        total_people=len(job.people),
        progress=build_progress_data(job),
    )


def to_person_summary(run: PersonRun) -> PersonSummaryView:
    return PersonSummaryView(**_summary_fields(run))


def to_person_view(run: PersonRun) -> PersonView:
    analysis = run.analysis
    group_ids = _group_ids_by_case(run)
    cases = [_to_case_view(item, run, group_ids) for item in analysis.cases] if analysis else []
    groups = _to_group_views(analysis.identity_groups) if analysis else []
    discarded = (
        {reason.value: count for reason, count in analysis.discarded_counts.items()}
        if analysis
        else {}
    )
    return PersonView(
        **_summary_fields(run), cases=cases, identity_groups=groups, discarded_by_reason=discarded
    )


def _summary_fields(run: PersonRun) -> dict[str, Any]:
    analysis = run.analysis
    cases = analysis.cases if analysis else ()
    return {
        "index": run.index,
        "line_number": run.line_number,
        "first_name": run.person.first_name,
        "last_name": run.person.last_name,
        "date_of_birth": run.person.date_of_birth,
        "external_ref": run.person.external_ref,
        "state": run.state.value,
        "lane": run.lane,
        "query": run.query,
        "strategy": run.strategy.value if run.strategy else None,
        "failure_reason": run.failure_reason,
        "cases_found": len(cases),
        "eligible_for_details": sum(1 for item in cases if item.case.is_detail_eligible),
        "details_loaded": len(run.details),
        "discarded": analysis.discarded_total if analysis else 0,
        "truncated": run.truncated,
    }


def _group_ids_by_case(run: PersonRun) -> dict[int, int]:
    if run.analysis is None:
        return {}
    return {
        id(item.case): group_id
        for group_id, group in enumerate(run.analysis.identity_groups, start=1)
        for item in group.cases
    }


def _to_group_views(groups: tuple[Any, ...]) -> list[IdentityGroupView]:
    return [
        IdentityGroupView(
            group_id=group_id,
            date_of_birth=group.date_of_birth,
            drivers_license=group.drivers_license,
            case_count=group.case_count,
            case_keys=[item.case.case_key for item in group.cases],
        )
        for group_id, group in enumerate(groups, start=1)
    ]


def _to_case_view(item: AssessedCase, run: PersonRun, group_ids: dict[int, int]) -> CaseView:
    case = item.case
    detail = run.details.get(case.case_key)
    return CaseView(
        case_number=case.case_number,
        case_key=case.case_key,
        citation_number=case.citation_number,
        file_date=case.file_date,
        caption=case.caption,
        status=case.public_status_label,
        is_restricted=case.is_restricted,
        date_of_birth=case.date_of_birth,
        drivers_license=case.drivers_license,
        match_label=item.assessment.label.value,
        match_reasons=list(item.assessment.reasons),
        group_id=group_ids.get(id(case)),
        detail=_to_detail_view(detail) if detail else None,
        detail_error=run.detail_errors.get(case.case_key),
    )


def _to_detail_view(detail: CaseDetail) -> DetailView:
    plan = detail.payment_plan
    return DetailView(
        charges=[_to_charge_view(charge) for charge in detail.displayed_charges],
        amount_due=_to_text(detail.amount_due),
        proof_of_correction_required=detail.proof_of_correction_required,
        has_payment_plan=detail.has_payment_plan,
        payment_plan=(
            PaymentPlanView(
                past_amount_due=_to_text(plan.past_amount_due),
                monthly_amount=_to_text(plan.monthly_amount),
                remaining_balance=_to_text(plan.remaining_balance),
            )
            if plan
            else None
        ),
        is_extension_eligible=detail.is_extension_eligible,
        original_date=detail.original_date,
        extended_date=detail.extended_date,
        notices=list(detail.notices),
    )


def _to_charge_view(charge: Charge) -> ChargeView:
    return ChargeView(statute=charge.statute, description=charge.description)


def _to_text(value: object) -> str | None:
    return None if value is None else str(value)


def _to_row_view(row: ImportRow) -> RowView:
    return RowView(
        line_number=row.line_number,
        status=row.status.value,
        original=row.original,
        changes=[change.model_dump() for change in row.changes],
        issues=[
            {"code": issue.code.value, "message": issue.message, "field": issue.field}
            for issue in row.issues
        ],
        duplicate_of_line=row.duplicate_of_line,
    )


def _to_file_issue(issue: FileIssue) -> dict[str, str]:
    return {"code": issue.code.value, "severity": issue.severity.value, "message": issue.message}


__all__ = [
    "JobListItem",
    "JobSnapshot",
    "PersonState",
    "PersonView",
    "RowStatus",
    "to_job_list_item",
    "to_job_snapshot",
    "to_person_view",
    "to_report_view",
]
