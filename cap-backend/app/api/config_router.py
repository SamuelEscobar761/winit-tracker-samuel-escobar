from fastapi import APIRouter, Depends, Request

from app.api.views import ConfigView
from app.auth.dependencies import require_session
from app.config.settings import Settings

router = APIRouter(prefix="/config", tags=["config"], dependencies=[Depends(require_session)])


@router.get("")
async def read_config(request: Request) -> ConfigView:
    settings: Settings = request.app.state.settings
    return ConfigView(
        provider=settings.cap_provider.value,
        max_workers=settings.max_workers,
        default_parallelism=min(settings.default_parallelism, settings.max_workers),
        csv_max_bytes=settings.csv_max_bytes,
        csv_max_rows=settings.csv_max_rows,
    )
