import asyncio
from typing import Any

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

from app.api.dependencies import get_job_system
from app.auth.dependencies import authorize_websocket, check_origin, require_session
from app.jobs.container import JobSystem
from app.live.frames import Frame
from app.live.input import InputEvent
from app.live.lanes import LaneStatus

STATUS_POLL_SECONDS = 0.25
POLICY_VIOLATION = 1008

rest_router = APIRouter(
    prefix="/lanes", tags=["lanes"], dependencies=[Depends(require_session), Depends(check_origin)]
)
websocket_router = APIRouter(tags=["lanes"])


class LaneStatusView(BaseModel):
    lane: int
    job_id: str | None
    person_index: int | None
    person_state: str | None
    awaiting_captcha: bool


@rest_router.get("")
async def list_lanes(request: Request) -> list[LaneStatusView]:
    system = get_job_system(request)
    return [_to_view(system.registry.status(lane)) for lane in system.registry.lanes()]


@websocket_router.websocket("/ws/lanes/{lane}")
async def stream_lane(websocket: WebSocket, lane: int) -> None:
    """Frames go out as JSON (base64 JPEG); a person's input comes in while a CAPTCHA waits."""
    if not authorize_websocket(websocket):
        await websocket.close(code=POLICY_VIOLATION)
        return
    await websocket.accept()
    system: JobSystem = websocket.app.state.job_system
    sender = asyncio.create_task(_send_frames_and_status(websocket, system, lane))
    receiver = asyncio.create_task(_receive_input(websocket, system, lane))
    _, pending = await asyncio.wait({sender, receiver}, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()


async def _send_frames_and_status(websocket: WebSocket, system: JobSystem, lane: int) -> None:
    channel = system.registry.channel_for(lane)
    last_status: LaneStatus | None = None
    with channel.frames.subscribe() as queue:
        while True:
            last_status = await _send_status_if_changed(websocket, system, lane, last_status)
            try:
                frame = await asyncio.wait_for(queue.get(), STATUS_POLL_SECONDS)
            except TimeoutError:
                continue
            await websocket.send_json(_frame_message(frame))


async def _send_status_if_changed(
    websocket: WebSocket, system: JobSystem, lane: int, previous: LaneStatus | None
) -> LaneStatus:
    status = system.registry.status(lane)
    if status != previous:
        await websocket.send_json({"type": "status", **_to_view(status).model_dump()})
    return status


async def _receive_input(websocket: WebSocket, system: JobSystem, lane: int) -> None:
    try:
        while True:
            raw = await websocket.receive_json()
            await websocket.send_json(await _handle_input(system, lane, raw))
    except WebSocketDisconnect:
        return


async def _handle_input(system: JobSystem, lane: int, raw: Any) -> dict[str, str]:
    try:
        event = InputEvent.model_validate(raw)
    except ValidationError:
        return {"type": "input", "outcome": "invalid"}
    outcome = await system.input_router.route(lane, event)
    return {"type": "input", "outcome": outcome.value}


def _frame_message(frame: Frame) -> dict[str, Any]:
    return {
        "type": "frame",
        "lane": frame.lane,
        "sequence": frame.sequence,
        "width": frame.width,
        "height": frame.height,
        "mime_type": frame.mime_type,
        "data": frame.data_base64,
    }


def _to_view(status: LaneStatus) -> LaneStatusView:
    return LaneStatusView(
        lane=status.lane,
        job_id=status.job_id,
        person_index=status.person_index,
        person_state=status.person_state,
        awaiting_captcha=status.awaiting_captcha,
    )
