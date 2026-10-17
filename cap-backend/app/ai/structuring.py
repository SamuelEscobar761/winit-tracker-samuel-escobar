import json
import re
from typing import Literal

from pydantic import BaseModel

from app.ai.model import StructuredModel

SYSTEM_PROMPT = (
    "You turn free-text court notices into structured items. Copy the excerpt exactly from the "
    "notice. Only fill date or amount when it is written in that excerpt, exactly as written. "
    "Use kind 'other' when unsure."
)
NoticeKind = Literal["payment_due", "extension", "proof_of_correction", "warning", "other"]


class NoticeItem(BaseModel):
    kind: NoticeKind
    excerpt: str
    date_text: str | None
    amount_text: str | None


class NoticeDraft(BaseModel):
    items: list[NoticeItem]


class StructuredNotices(BaseModel):
    items: list[NoticeItem]
    dropped_items: int
    model: str
    ai_generated: bool = True


class NoticeStructurer:
    def __init__(self, model: StructuredModel) -> None:
        self._model = model

    async def structure(self, notices: list[str]) -> StructuredNotices:
        draft = await self._model.ask(SYSTEM_PROMPT, json.dumps({"notices": notices}), NoticeDraft)
        kept = [item for item in draft.items if _is_traceable(item, notices)]
        return StructuredNotices(
            items=kept, dropped_items=len(draft.items) - len(kept), model=self._model.name
        )


def _is_traceable(item: NoticeItem, notices: list[str]) -> bool:
    source = next((text for text in notices if _squash(item.excerpt) in _squash(text)), None)
    if source is None:
        return False
    return all(_appears(value, source) for value in (item.date_text, item.amount_text) if value)


def _appears(value: str, source: str) -> bool:
    return _squash(value) in _squash(source)


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()
