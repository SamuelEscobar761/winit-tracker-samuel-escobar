from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.cases.status import STATUSES_WITHOUT_DETAIL, CaseStatus

RESTRICTED_STATUS_LABEL = "Restricted by portal"


class CaseSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    portal_case_id: str | None
    case_number: str
    case_key: str
    citation_number: str | None
    file_date: date | None
    caption: str
    drivers_license: str | None
    date_of_birth: date | None
    status: CaseStatus
    raw_status: str
    raw_item: dict[str, Any] = Field(default_factory=dict, repr=False)

    @property
    def is_restricted(self) -> bool:
        return self.status is CaseStatus.WARRANT

    @property
    def is_detail_eligible(self) -> bool:
        return self.status not in STATUSES_WITHOUT_DETAIL

    @property
    def public_status_label(self) -> str:
        return RESTRICTED_STATUS_LABEL if self.is_restricted else self.status.value


class Charge(BaseModel):
    model_config = ConfigDict(frozen=True)

    statute: str
    description: str
    raw: str


class PaymentOption(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str | None
    text: str
    amount: Decimal | None


class PaymentPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    past_amount_due: Decimal | None
    monthly_amount: Decimal | None
    remaining_balance: Decimal | None
    total: Decimal | None
    months: int | None
    due_day: str | None
    start_date: date | None
    final_due_date: date | None
    due_dates: tuple[date, ...]


class CaseDetail(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_key: str
    portal_case_id: str | None
    party_id: str | None
    full_name: str | None
    charges: tuple[Charge, ...]
    proof_of_correction_required: bool
    proof_of_correction_charges: tuple[Charge, ...]
    amount_due: Decimal | None
    payment_options: tuple[PaymentOption, ...]
    has_payment_plan: bool
    payment_plan: PaymentPlan | None
    is_extension_eligible: bool
    original_date: date | None
    extended_date: date | None
    notices: tuple[str, ...]

    @property
    def displayed_charges(self) -> tuple[Charge, ...]:
        """Cases with a payment plan report their charges only in the proof-of-correction list."""
        return self.charges or self.proof_of_correction_charges
