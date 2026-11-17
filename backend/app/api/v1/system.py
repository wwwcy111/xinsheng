"""服务健康检查。"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.common import success

router = APIRouter(tags=["系统"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """探活接口：检查数据库连通性与 AI 开关状态。"""
    db.execute(text("SELECT 1"))
    return success(
        {
            "status": "ok",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "ai_enabled": settings.AI_ENABLED,
            "cache_replay": settings.CACHE_REPLAY,
        }
    )