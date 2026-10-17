from typing import Annotated

from fastapi import APIRouter, Depends

from app.config.dependencies import get_settings
from app.config.settings import Settings
from app.health.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health")
def read_health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(status="ok", provider=settings.cap_provider)
