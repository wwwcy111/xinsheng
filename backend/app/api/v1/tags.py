"""兴趣标签接口。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Tag
from app.schemas.auth import TagOut
from app.schemas.common import success

router = APIRouter(tags=["兴趣标签"])


@router.get("/tags")
def list_tags(db: Session = Depends(get_db)):
    """获取全部启用标签，按分类与排序号返回。"""
    tags = (
        db.query(Tag)
        .filter(Tag.status == 1)
        .order_by(Tag.category, Tag.sort_no, Tag.id)
        .all()
    )
    return success([TagOut.model_validate(tag).model_dump() for tag in tags])