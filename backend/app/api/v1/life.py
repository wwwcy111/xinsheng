"""校园生活板块接口：二手闲置、失物招领、活动聚合与报名。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.entities import Activity, ActivitySignup, LostFound, SecondhandItem, User
from app.schemas.common import BusinessError, paginate, success
from app.schemas.life import (
    ActivityCreate,
    ActivityOut,
    ItemCreate,
    ItemOut,
    ItemStatusUpdate,
    LostFoundCreate,
    LostFoundOut,
    LostFoundStatusUpdate,
    SignupResult,
)

router = APIRouter(tags=["校园生活百宝箱"])


# ------------------------- 二手闲置 -------------------------


@router.get("/market/items")
def list_items(
    keyword: str | None = Query(default=None, max_length=50),
    category: str | None = Query(default=None, max_length=20),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """在售商品列表，支持关键词与分类筛选。"""
    query = db.query(SecondhandItem).filter(SecondhandItem.status == "on_sale")
    if keyword:
        query = query.filter(SecondhandItem.title.like(f"%{keyword}%"))
    if category:
        query = query.filter(SecondhandItem.category == category)
    total = query.count()
    rows = (
        query.order_by(SecondhandItem.created_at.desc(), SecondhandItem.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [ItemOut.model_validate(row).model_dump() for row in rows]
    return success(paginate(items, total, page, page_size))


@router.post("/market/items")
def create_item(
    payload: ItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发布二手商品。"""
    item = SecondhandItem(seller_id=user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return success(ItemOut.model_validate(item).model_dump(), "发布成功")


@router.get("/market/items/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    """商品详情，浏览量自增。"""
    item = db.get(SecondhandItem, item_id)
    if item is None:
        raise BusinessError(40401, "商品不存在")
    item.view_count += 1
    db.commit()
    db.refresh(item)
    return success(ItemOut.model_validate(item).model_dump())


@router.patch("/market/items/{item_id}/status")
def update_item_status(
    item_id: int,
    payload: ItemStatusUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """卖家更新商品状态：有意向、已售、下架。"""
    item = db.get(SecondhandItem, item_id)
    if item is None:
        raise BusinessError(40401, "商品不存在")
    if item.seller_id != user.id:
        raise BusinessError(40301, "只能操作自己发布的商品")
    item.status = payload.status
    db.commit()
    db.refresh(item)
    return success(ItemOut.model_validate(item).model_dump(), "状态已更新")


# ------------------------- 失物招领 -------------------------


@router.get("/lostfound")
def list_lost_found(
    type: str | None = Query(default=None, pattern="^(lost|found)$"),
    status: str | None = Query(default="ongoing", pattern="^(ongoing|returned|closed)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """失物/招领列表，默认只看进行中。"""
    query = db.query(LostFound)
    if type:
        query = query.filter(LostFound.type == type)
    if status:
        query = query.filter(LostFound.status == status)
    total = query.count()
    rows = (
        query.order_by(LostFound.created_at.desc(), LostFound.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [LostFoundOut.model_validate(row).model_dump() for row in rows]
    return success(paginate(items, total, page, page_size))


@router.post("/lostfound")
def create_lost_found(
    payload: LostFoundCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发布失物或招领信息。"""
    record = LostFound(publisher_id=user.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return success(LostFoundOut.model_validate(record).model_dump(), "发布成功")


@router.patch("/lostfound/{record_id}/status")
def update_lost_found_status(
    record_id: int,
    payload: LostFoundStatusUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发布者更新失物招领状态：已归还、已关闭。"""
    record = db.get(LostFound, record_id)
    if record is None:
        raise BusinessError(40401, "记录不存在")
    if record.publisher_id != user.id:
        raise BusinessError(40301, "只能操作自己发布的信息")
    record.status = payload.status
    db.commit()
    db.refresh(record)
    return success(LostFoundOut.model_validate(record).model_dump(), "状态已更新")


# ------------------------- 活动聚合 -------------------------


@router.get("/activities")
def list_activities(
    type: str | None = Query(default=None, max_length=20),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """活动列表：报名中优先，按开始时间升序。"""
    query = db.query(Activity).filter(Activity.status == "signing")
    if type:
        query = query.filter(Activity.type == type)
    total = query.count()
    rows = (
        query.order_by(Activity.start_time.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [ActivityOut.model_validate(row).model_dump() for row in rows]
    return success(paginate(items, total, page, page_size))


@router.post("/activities")
def create_activity(
    payload: ActivityCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建活动（演示期所有登录用户可创建，生产应收敛到管理员）。"""
    if payload.end_time <= payload.start_time:
        raise BusinessError(40001, "结束时间必须晚于开始时间")
    activity = Activity(
        **payload.model_dump(),
        remaining=payload.quota,
        status="signing",
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return success(ActivityOut.model_validate(activity).model_dump(), "活动创建成功")


@router.post("/activities/{activity_id}/signup")
def signup_activity(
    activity_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """活动报名：条件扣减名额，唯一键保证不重复报名。"""
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise BusinessError(40401, "活动不存在")
    if activity.status != "signing":
        raise BusinessError(40901, "活动已结束或已取消")

    existing = (
        db.query(ActivitySignup)
        .filter(ActivitySignup.activity_id == activity_id, ActivitySignup.user_id == user.id)
        .first()
    )
    if existing is not None:
        raise BusinessError(40901, "你已报名该活动")

    updated = (
        db.query(Activity)
        .filter(Activity.id == activity_id, Activity.remaining > 0)
        .update({Activity.remaining: Activity.remaining - 1}, synchronize_session=False)
    )
    if not updated:
        db.rollback()
        raise BusinessError(40901, "名额已满")

    db.add(ActivitySignup(activity_id=activity_id, user_id=user.id, status="signed"))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BusinessError(40901, "你已报名该活动")

    db.refresh(activity)
    return success(
        SignupResult(
            activity_id=activity.id,
            user_id=user.id,
            status="signed",
            remaining=activity.remaining,
        ).model_dump(),
        "报名成功",
    )