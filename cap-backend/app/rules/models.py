import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

_SELECTOR = re.compile(r"^[A-Za-z0-9_#.\[\]=\"'*>+~,:()^$|\- /]{1,200}$")
_LABEL = re.compile(r"^[\w .,'()\-/&]{1,60}$")
_PATH = re.compile(r"^/[A-Za-z0-9_\-./]{0,100}$")
_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,40}$")
_CSS_CLASS = re.compile(r"^[A-Za-z][A-Za-z0-9_\-]{0,40}$")
_PATTERN = re.compile(r"^[\w .,'()\-/&]{1,80}$")

SEARCH_ITEM_KEYS = (
    "caseId",
    "caseNumber",
    "citationNumber",
    "fileDate",
    "caseCaption",
    "driversLicense",
    "dateOfBirth",
    "caseStatus",
)
SELECT_DATA_KEYS = (
    "caseNumber",
    "caseId",
    "partyId",
    "fullName",
    "charges",
    "pocChanges",
    "bailOptions",
    "bfAmount",
    "isPoc",
    "hasPaymentPlan",
    "isExtensionEligible",
    "originalDate",
    "extendedDate",
    "maMessage",
    "userMessage",
    "paymentTotal",
    "paymentMonthlyAmount",
    "paymentPastAmount",
    "paymentMonths",
    "paymentDueOn",
    "paymentDueDates",
    "paymentStartDate",
    "paymentFinalDueDate",
)


def _check(pattern: re.Pattern[str], what: str):  # type: ignore[no-untyped-def]
    def validate(value: str) -> str:
        if not pattern.match(value):
            raise ValueError(f"{what} contains characters that are not allowed: {value!r}")
        return value

    return AfterValidator(validate)


Selector = Annotated[str, _check(_SELECTOR, "selector")]
Label = Annotated[str, _check(_LABEL, "label")]
ApiPath = Annotated[str, _check(_PATH, "path")]
JsonKey = Annotated[str, _check(_KEY, "json key")]
CssClass = Annotated[str, _check(_CSS_CLASS, "css class")]
Pattern = Annotated[str, _check(_PATTERN, "pattern")]


class UiRules(BaseModel):
    model_config = ConfigDict(frozen=True)

    party_name_button: Label = "Party Name"
    query_input: Selector = "#number"
    search_button: Selector = 'button[type="submit"]'
    search_again_button: Label = "Search Again"
    select_button: Label = "Select"
    results_rows: Selector = "table.table-striped tbody tr"
    selected_button_class: CssClass = "btn-primary"
    captcha: Selector = 'iframe[src*="recaptcha"], .g-recaptcha, iframe[title*="reCAPTCHA"]'


class ApiRules(BaseModel):
    model_config = ConfigDict(frozen=True)

    search_path: ApiPath = "/api/traffic/search"
    select_path_prefix: ApiPath = "/api/traffic/select/"
    maintenance_path: ApiPath = "/api/maintenance"
    application_mode_path: ApiPath = "/api/applicationmode"
    normal_mode: Label = "NORMAL"


class ResponseRules(BaseModel):
    model_config = ConfigDict(frozen=True)

    data_key: JsonKey = "data"
    result_key: JsonKey = "result"
    message_key: JsonKey = "message"
    success_result: int = Field(default=0, ge=0, le=1000)
    session_expired_pattern: Pattern = "session expired"
    no_results_pattern: Pattern = "no case"


def _identity(keys: tuple[str, ...]) -> dict[str, str]:
    return {key: key for key in keys}


class FieldRules(BaseModel):
    """Maps the names this app uses to the names the portal currently sends."""

    model_config = ConfigDict(frozen=True)

    search_item: dict[str, JsonKey] = Field(default_factory=lambda: _identity(SEARCH_ITEM_KEYS))
    select_data: dict[str, JsonKey] = Field(default_factory=lambda: _identity(SELECT_DATA_KEYS))

    @model_validator(mode="after")
    def only_known_fields_and_complete(self) -> "FieldRules":
        _require_known(self.search_item, SEARCH_ITEM_KEYS, "search_item")
        _require_known(self.select_data, SELECT_DATA_KEYS, "select_data")
        return self


def _require_known(mapping: dict[str, str], known: tuple[str, ...], name: str) -> None:
    unknown = set(mapping) - set(known)
    if unknown:
        raise ValueError(f"{name} has unknown fields: {sorted(unknown)}")


class PortalRules(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    version: int = Field(default=1, ge=1)
    ui: UiRules = Field(default_factory=UiRules)
    api: ApiRules = Field(default_factory=ApiRules)
    responses: ResponseRules = Field(default_factory=ResponseRules)
    fields: FieldRules = Field(default_factory=FieldRules)

    def complete_fields(self) -> "PortalRules":
        search = {**_identity(SEARCH_ITEM_KEYS), **self.fields.search_item}
        select = {**_identity(SELECT_DATA_KEYS), **self.fields.select_data}
        return self.model_copy(
            update={"fields": FieldRules(search_item=search, select_data=select)}
        )


def default_rules() -> PortalRules:
    return PortalRules()
