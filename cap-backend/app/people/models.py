from datetime import date

from pydantic import BaseModel, ConfigDict


class Person(BaseModel):
    model_config = ConfigDict(frozen=True)

    first_name: str
    last_name: str
    date_of_birth: date | None = None
    external_ref: str | None = None
