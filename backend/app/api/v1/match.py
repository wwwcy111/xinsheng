"""搭子匹配接口。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.entities import IcebreakerTopic, MatchRecord, User
from app.schemas.common import BusinessError, success
from app.schemas.match import (
    GreetingCreate,
    MatchItemOut,
    RecommendationOut,
    TopicOut,
)
from app.services.match_service import get_or_create_recommendations, get_user_tags, mark_greeted

router = APIRouter(tags=["AI 破冰交友"])

MIN_TAGS = 3
MAX_TAGS = 10


def _ensure_profile(db: Session, user: User) -> None:
    """匹配前校验画像完整性。"""
    tag_count = len(get_user_tags(db, user.id))
    if not (MIN_TAGS <= tag_count <= MAX_TAGS):
        raise BusinessError(40001, f"请先在画像中选择 {MIN_TAGS}-{MAX_TAGS} 个兴趣标签")


@router.get("/match/recommendations")
async def get_recommendations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当日搭子推荐，无批次时生成 3 条。"""
    _ensure_profile(db, user)
    batch_date, items = await get_or_create_recommendations(db, user)
    payload = RecommendationOut(
        batch_date=batch_date,
        items=[MatchItemOut(**item) for item in items],
    )
    return success(payload.model_dump())


@router.post("/match/recommendations/refresh")
async def refresh_recommendations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """换一批：重新生成当日推荐。"""
    _ensure_profile(db, user)
    batch_date, items = await get_or_create_recommendations(db, user, force_refresh=True)
    payload = RecommendationOut(
        batch_date=batch_date,
        items=[MatchItemOut(**item) for item in items],
    )
    return success(payload.model_dump())


@router.get("/match/recommendations/{match_id}/topics")
def get_topics(
    match_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取某条匹配记录的破冰话题。"""
    record = db.get(MatchRecord, match_id)
    if record is None or record.user_id != user.id:
        raise BusinessError(40401, "匹配记录不存在")
    rows = (
        db.query(IcebreakerTopic)
        .filter(IcebreakerTopic.match_id == match_id)
        .order_by(IcebreakerTopic.sort_no)
        .all()
    )
    return success([TopicOut(content=row.content).model_dump() for row in rows])


@router.post("/match/greetings")
def send_greeting(
    payload: GreetingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发送招呼：本期仅更新匹配状态，留言由前端展示。"""
    target = db.get(User, payload.target_user_id)
    if target is None:
        raise BusinessError(40401, "对方用户不存在")
    mark_greeted(db, user.id, payload.target_user_id)
    return success(
        {
            "target_user_id": payload.target_user_id,
            "message": payload.message,
            "status": "greeted",
        },
        "招呼已发送",
    )