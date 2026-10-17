from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from pydantic.alias_generators import to_camel


def _to_optional_text(value: object) -> str | None:
    return None if value is None else str(value)


OptionalText = Annotated[str | None, BeforeValidator(_to_optional_text)]


class PortalModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
        frozen=True,
    )


class RawSearchItem(PortalModel):
    case_id: OptionalText = None
    case_number: OptionalText = None
    citation_number: OptionalText = None
    file_date: OptionalText = None
    case_caption: OptionalText = None
    drivers_license: OptionalText = None
    date_of_birth: OptionalText = None
    case_status: OptionalText = None


class RawBailOption(PortalModel):
    code: OptionalText = None
    text: OptionalText = None
    amount: OptionalText = None


class RawSelectData(PortalModel):
    case_number: OptionalText = None
    case_id: OptionalText = None
    party_id: OptionalText = None
    full_name: OptionalText = None
    charges: list[str] = Field(default_factory=list)
    poc_changes: list[str] = Field(default_factory=list)
    bail_options: list[RawBailOption] = Field(default_factory=list)
    bf_amount: OptionalText = None
    is_poc: bool = False
    has_payment_plan: bool = False
    is_extension_eligible: bool = False
    original_date: OptionalText = None
    extended_date: OptionalText = None
    ma_message: OptionalText = None
    user_message: OptionalText = None
    payment_total: Decimal | None = None
    payment_monthly_amount: Decimal | None = None
    payment_past_amount: Decimal | None = None
    payment_months: int | None = None
    payment_due_on: OptionalText = None
    payment_due_dates: list[str] | None = None
    payment_start_date: OptionalText = None
    payment_final_due_date: OptionalText = None
