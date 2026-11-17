"""AI 笔记助手接口：上传、状态查询、解析。"""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.entities import StudyNote, User
from app.schemas.common import BusinessError, paginate, success
from app.schemas.study import NoteOut, NoteStatusOut
from app.services.note_service import parse_note, set_ocr_text

router = APIRouter(tags=["学霸互助圈"])


class OcrTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000, description="OCR 文本或人工粘贴的笔记内容")


def _get_owned_note(db: Session, note_id: int, user: User) -> StudyNote:
    note = db.get(StudyNote, note_id)
    if note is None or note.owner_id != user.id:
        raise BusinessError(40401, "笔记不存在")
    return note


@router.post("/study/notes")
async def upload_note(
    file: UploadFile = File(..., description="笔记图片或 PDF"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """接收笔记文件：校验类型与大小后落盘，状态置为识别中。"""
    filename = file.filename or "note"
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in settings.ALLOWED_NOTE_TYPES:
        raise BusinessError(40001, "仅支持 jpg/png/webp/pdf 格式")

    content = await file.read()
    if not content:
        raise BusinessError(40001, "文件内容为空")
    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise BusinessError(40001, f"文件不能超过 {settings.MAX_UPLOAD_MB}MB")

    stored_name = f"{uuid4().hex}.{ext}"
    (settings.UPLOAD_DIR / stored_name).write_bytes(content)

    note = StudyNote(
        owner_id=user.id,
        file_name=filename[:255],
        file_url=f"/uploads/{stored_name}",
        file_type=ext,
        file_size=len(content),
        status="ocr_pending",
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return success(NoteOut.model_validate(note).model_dump(), "上传成功")


@router.get("/study/notes")
def list_notes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我的笔记列表，按上传时间倒序。"""
    query = db.query(StudyNote).filter(StudyNote.owner_id == user.id)
    total = query.count()
    rows = (
        query.order_by(StudyNote.created_at.desc(), StudyNote.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [NoteOut.model_validate(row).model_dump() for row in rows]
    return success(paginate(items, total, page, page_size))


@router.get("/study/notes/{note_id}")
def get_note(
    note_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """笔记详情：含导图、摘要、练习题。"""
    note = _get_owned_note(db, note_id, user)
    return success(NoteOut.model_validate(note).model_dump())


@router.get("/study/notes/{note_id}/status")
def get_note_status(
    note_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """轻量状态查询，前端每 2 秒轮询。"""
    note = _get_owned_note(db, note_id, user)
    progress = {"ocr_pending": 20, "generating": 60, "completed": 100, "failed": 100}.get(note.status, 0)
    return success(NoteStatusOut(note_id=note.id, status=note.status, progress=progress, error_message=note.error_message).model_dump())


@router.post("/study/notes/{note_id}/ocr-text")
def save_ocr_text(
    note_id: int,
    payload: OcrTextRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """写入 OCR 文本。演示环境可人工粘贴笔记内容，跳过真实 OCR。"""
    note = _get_owned_note(db, note_id, user)
    note = set_ocr_text(db, note, payload.text)
    return success(NoteOut.model_validate(note).model_dump(), "OCR 文本已保存")


@router.post("/study/notes/{note_id}/parse")
async def parse(
    note_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """触发解析：生成思维导图、摘要与练习题。

    未启用 AI 时使用本地模板兜底，保证演示可完成。
    """
    note = _get_owned_note(db, note_id, user)
    if note.status == "generating":
        raise BusinessError(40901, "笔记正在生成中，请稍后")
    note = await parse_note(db, note)
    return success(NoteOut.model_validate(note).model_dump(), "解析完成")