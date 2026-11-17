"""认证与用户画像接口。"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.entities import Tag, User, UserTag
from app.schemas.auth import (
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    TagOut,
    TokenOut,
    UserOut,
)
from app.schemas.common import BusinessError, success

router = APIRouter(tags=["认证与画像"])

MAX_LOGIN_FAILS = 5
LOCK_MINUTES = 10
MIN_TAGS = 3
MAX_TAGS = 10


def _bind_tags(db: Session, user_id: int, tag_ids: list[int]) -> None:
    """校验并绑定兴趣标签，重复传入自动去重。"""
    unique_ids = sorted(set(tag_ids))
    if not unique_ids:
        return
    if len(unique_ids) > MAX_TAGS:
        raise BusinessError(40001, f"兴趣标签最多选择 {MAX_TAGS} 个")

    existing = {tag.id for tag in db.query(Tag).filter(Tag.id.in_(unique_ids), Tag.status == 1).all()}
    missing = [str(tag_id) for tag_id in unique_ids if tag_id not in existing]
    if missing:
        raise BusinessError(40001, f"标签不存在或已停用：{','.join(missing)}")

    db.query(UserTag).filter(UserTag.user_id == user_id).delete(synchronize_session=False)
    for tag_id in unique_ids:
        db.add(UserTag(user_id=user_id, tag_id=tag_id))
    db.flush()


def build_user_out(db: Session, user: User) -> UserOut:
    """组装用户输出，附带标签与画像完整度。"""
    tags = (
        db.query(Tag)
        .join(UserTag, UserTag.tag_id == Tag.id)
        .filter(UserTag.user_id == user.id)
        .order_by(Tag.category, Tag.sort_no)
        .all()
    )
    return UserOut(
        id=user.id,
        nickname=user.nickname,
        student_no_tail4=user.student_no_tail4,
        personality=user.personality,
        social_pref=user.social_pref,
        college=user.college,
        major=user.major,
        class_name=user.class_name,
        contact=user.contact,
        bio=user.bio,
        avatar_url=user.avatar_url,
        status=user.status,
        created_at=user.created_at,
        tags=[TagOut.model_validate(tag) for tag in tags],
        profile_complete=MIN_TAGS <= len(tags) <= MAX_TAGS,
    )


@router.post("/auth/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册，可同时录入兴趣标签与性格信息。"""
    if db.query(User).filter(User.nickname == payload.nickname).first():
        raise BusinessError(40901, "昵称已被占用，请换一个")

    user = User(
        nickname=payload.nickname,
        student_no_tail4=payload.student_no_tail4,
        password_hash=hash_password(payload.password),
        personality=payload.personality,
        social_pref=payload.social_pref,
        college=payload.college,
        major=payload.major,
        contact=payload.contact,
        bio=payload.bio,
    )
    db.add(user)
    db.flush()

    _bind_tags(db, user.id, payload.tag_ids)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return success(
        TokenOut(
            token=token,
            expires_in=settings.TOKEN_EXPIRE_MINUTES * 60,
            user=build_user_out(db, user),
        ).model_dump()
    )


@router.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """登录：连续失败 5 次锁定 10 分钟。"""
    user = db.query(User).filter(User.nickname == payload.nickname).first()
    if user is None:
        raise BusinessError(40101, "昵称或口令错误")

    if user.lock_until and user.lock_until > datetime.now():
        remain = int((user.lock_until - datetime.now()).total_seconds() // 60) + 1
        raise BusinessError(42901, f"账号已锁定，请 {remain} 分钟后再试")

    if not verify_password(payload.password, user.password_hash):
        user.login_fail_count += 1
        if user.login_fail_count >= MAX_LOGIN_FAILS:
            user.lock_until = datetime.now() + timedelta(minutes=LOCK_MINUTES)
            user.login_fail_count = 0
        db.commit()
        raise BusinessError(40101, "昵称或口令错误")

    user.login_fail_count = 0
    user.lock_until = None
    user.last_login_at = datetime.now()
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return success(
        TokenOut(
            token=token,
            expires_in=settings.TOKEN_EXPIRE_MINUTES * 60,
            user=build_user_out(db, user),
        ).model_dump()
    )


@router.get("/users/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户与画像。"""
    return success(build_user_out(db, user).model_dump())


@router.put("/users/me/profile")
def update_profile(
    payload: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新画像：标签、性格、社交偏好等，只更新传入字段。"""
    if payload.tag_ids is not None:
        _bind_tags(db, user.id, payload.tag_ids)
    if payload.personality is not None:
        user.personality = payload.personality
    if payload.social_pref is not None:
        user.social_pref = payload.social_pref
    for field in ("contact", "bio", "college", "major"):
        value = getattr(payload, field)
        if value is not None:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return success(build_user_out(db, user).model_dump())