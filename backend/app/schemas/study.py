"""AI 笔记助手相关 Schema。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_url: str
    file_type: str
    file_size: int
    status: str
    char_count: int
    mind_map: dict[str, Any] | None = None
    summaries: list[Any] | None = None
    exercises: list[Any] | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class NoteStatusOut(BaseModel):
    note_id: int
    status: str
    progress: int = 0
    error_message: str | None = None