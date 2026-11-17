"""ORM 模型：与 sql/schema.sql 的 12 张表一一对应。

说明：
1. 主键使用 BIGINT，在 SQLite 下自动降级为 INTEGER 以支持自增；
2. 不建立物理外键，通过索引与业务层保证一致性，便于演示数据重置；
3. 状态字段使用英文枚举码，含义见字段注释。
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# SQLite 仅 INTEGER PRIMARY KEY 支持自增，MySQL 保持 BIGINT
BigIntType = BigInteger().with_variant(Integer, "sqlite")


class User(Base):
    """用户信息表。"""

    __tablename__ = "t_user"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="昵称")
    student_no_tail4: Mapped[str] = mapped_column(String(4), nullable=False, comment="学号后四位")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="口令哈希")
    avatar_url: Mapped[str | None] = mapped_column(String(500), comment="头像")
    college: Mapped[str | None] = mapped_column(String(50), comment="学院")
    major: Mapped[str | None] = mapped_column(String(50), comment="专业")
    class_name: Mapped[str | None] = mapped_column(String(50), comment="班级")
    personality: Mapped[str] = mapped_column(
        String(10), default="neutral", nullable=False, comment="性格：introvert/neutral/extrovert"
    )
    social_pref: Mapped[str] = mapped_column(
        String(20), default="random", nullable=False, comment="社交偏好：one_to_one/small_group/random"
    )
    contact: Mapped[str | None] = mapped_column(String(50), comment="联系方式")
    bio: Mapped[str | None] = mapped_column(String(200), comment="个人简介")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, comment="1正常 0封禁")
    login_fail_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    lock_until: Mapped[datetime | None] = mapped_column(DateTime, comment="锁定截止时间")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (Index("idx_user_status", "status"), Index("idx_user_college", "college"))


class Tag(Base):
    """兴趣标签表。"""

    __tablename__ = "t_tag"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag_name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False, comment="分类码")
    icon: Mapped[str | None] = mapped_column(String(50))
    sort_no: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (Index("idx_tag_category_sort", "category", "sort_no"),)


class UserTag(Base):
    """用户-兴趣标签关联表。"""

    __tablename__ = "t_user_tag"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigIntType, nullable=False)
    tag_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "tag_id", name="uk_user_tag"),
        Index("idx_user_tag_tag", "tag_id"),
    )


class MatchRecord(Base):
    """搭子匹配记录表。"""

    __tablename__ = "t_match_record"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigIntType, nullable=False, comment="推荐接收方")
    target_user_id: Mapped[int] = mapped_column(BigIntType, nullable=False, comment="被推荐搭子")
    score: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, comment="0-100")
    common_tag_ids: Mapped[list[Any] | None] = mapped_column(JSON, comment="共同标签ID数组")
    match_reason: Mapped[str | None] = mapped_column(String(200))
    batch_date: Mapped[date] = mapped_column(Date, nullable=False, comment="推荐批次日期")
    status: Mapped[str] = mapped_column(
        String(20), default="recommended", nullable=False, comment="recommended/greeted/matched/ignored"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "target_user_id", "batch_date", name="uk_user_target_date"),
        Index("idx_match_user_batch", "user_id", "batch_date"),
        Index("idx_match_target", "target_user_id"),
    )


class IcebreakerTopic(Base):
    """破冰话题表。"""

    __tablename__ = "t_icebreaker_topic"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(BigIntType, nullable=False)
    content: Mapped[str] = mapped_column(String(100), nullable=False)
    used_flag: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    sort_no: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (Index("idx_topic_match", "match_id"),)


class StudyNote(Base):
    """笔记上传记录表。"""

    __tablename__ = "t_study_note"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(BigIntType, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="字节")
    ocr_text: Mapped[str | None] = mapped_column(Text)
    char_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mind_map: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    summaries: Mapped[list[Any] | None] = mapped_column(JSON)
    exercises: Mapped[list[Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(20), default="ocr_pending", nullable=False, comment="ocr_pending/generating/completed/failed"
    )
    retry_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_note_owner_created", "owner_id", "created_at"),
        Index("idx_note_status", "status"),
    )


class SecondhandItem(Base):
    """二手物品表。"""

    __tablename__ = "t_secondhand_item"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    seller_id: Mapped[int] = mapped_column(BigIntType, nullable=False)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    original_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    condition_level: Mapped[str] = mapped_column(String(10), nullable=False)
    category: Mapped[str] = mapped_column(String(20), default="other", nullable=False)
    trade_place: Mapped[str] = mapped_column(String(100), nullable=False)
    image_urls: Mapped[list[Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(20), default="on_sale", nullable=False, comment="on_sale/intended/sold/off_shelf"
    )
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_item_status_created", "status", "created_at"),
        Index("idx_item_seller", "seller_id"),
        Index("idx_item_category", "category"),
    )


class LostFound(Base):
    """失物招领表。"""

    __tablename__ = "t_lost_found"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    publisher_id: Mapped[int] = mapped_column(BigIntType, nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False, comment="lost/found")
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    item_desc: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(20), default="other", nullable=False)
    event_time: Mapped[datetime | None] = mapped_column(DateTime)
    event_place: Mapped[str] = mapped_column(String(100), nullable=False)
    contact: Mapped[str] = mapped_column(String(50), nullable=False)
    images: Mapped[list[Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(20), default="ongoing", nullable=False, comment="ongoing/returned/closed"
    )
    claim_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_lf_type_status", "type", "status"),
        Index("idx_lf_publisher", "publisher_id"),
    )


class Activity(Base):
    """活动信息表。"""

    __tablename__ = "t_activity"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(
        String(20), default="other", nullable=False, comment="lecture/club_recruit/sports/other"
    )
    host: Mapped[str] = mapped_column(String(100), nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    place: Mapped[str] = mapped_column(String(100), nullable=False)
    quota: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining: Mapped[int] = mapped_column(Integer, nullable=False)
    signup_deadline: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(
        String(20), default="signing", nullable=False, comment="signing/ended/cancelled"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_activity_start", "start_time"),
        Index("idx_activity_status", "status"),
    )


class StudyPost(Base):
    """学习搭子招募帖表。"""

    __tablename__ = "t_study_post"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(BigIntType, nullable=False)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="evening_study/final_review/other"
    )
    description: Mapped[str | None] = mapped_column(String(500))
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    joined_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, comment="pending/published/full/offline"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_post_status_created", "status", "created_at"),
        Index("idx_post_author", "author_id"),
    )


class StudySignup(Base):
    """招募报名表。"""

    __tablename__ = "t_study_signup"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(BigIntType, nullable=False)
    user_id: Mapped[int] = mapped_column(BigIntType, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="signed", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uk_post_user"),
        Index("idx_signup_user", "user_id"),
    )


class ActivitySignup(Base):
    """活动报名表。"""

    __tablename__ = "t_activity_signup"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(BigIntType, nullable=False)
    user_id: Mapped[int] = mapped_column(BigIntType, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="signed", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", name="uk_activity_user"),
        Index("idx_activity_signup_user", "user_id"),
    )