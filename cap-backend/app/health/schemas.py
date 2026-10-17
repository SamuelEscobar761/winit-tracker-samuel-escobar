from pydantic import BaseModel

from app.config.settings import ProviderKind


class HealthResponse(BaseModel):
    status: str
    provider: ProviderKind
