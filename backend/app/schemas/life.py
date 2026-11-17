"""校园生活板块 Schema：二手、失物招领、活动。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ConditionLevel = Literal["new", "nine", "seven", "usable"]
ItemCategory = Literal["textbook", "digital", "life", "sports", "other"]
ItemStatus = Literal["on_sale", "intended", "sold", "off_shelf"]
LostFoundType = Literal["lost", "found"]
LostFoundStatus = Literal["ongoing", "returned", "closed"]
ActivityType = Literal["lecture", "club_recruit", "sports", "other"]


class ItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(ge=0, le=9999)
    original_price: float | None = Field(default=None, ge=0, le=99999)
    condition_level: ConditionLevel
    category: ItemCategory = "other"
    trade_place: str = Field(min_length=1, max_length=100)
    image_urls: list[str] = Field(default_factory=list, max_length=6)


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    seller_id: int
    title: str
    description: str | None = None
    price: float
    original_price: float | None = None
    condition_level: ConditionLevel
    category: ItemCategory
    trade_place: str
    image_urls: list[str] | None = None
    status: ItemStatus
    view_count: int
    created_at: datetime


class ItemStatusUpdate(BaseModel):
    status: Literal["intended", "sold", "off_shelf"]


class LostFoundCreate(BaseModel):
    type: LostFoundType
    title: str = Field(min_length=1, max_length=50)
    item_desc: str = Field(min_length=1, max_length=500)
    category: str = Field(default="other", max_length=20)
    event_time: datetime | None = None
    event_place: str = Field(min_length=1, max_length=100)
    contact: str = Field(min_length=1, max_length=50)
    images: list[str] = Field(default_factory=list, max_length=6)


class LostFoundOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    publisher_id: int
    type: LostFoundType
    title: str
    item_desc: str
    category: str
    event_time: datetime | None = None
    event_place: str
    contact: str
    images: list[str] | None = None
    status: LostFoundStatus
    claim_count: int
    created_at: datetime


class LostFoundStatusUpdate(BaseModel):
    status: LostFoundStatus


class ActivityCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    type: ActivityType = "other"
    host: str = Field(min_length=1, max_length=100)
    cover_url: str | None = None
    description: str | None = None
    start_time: datetime
    end_time: datetime
    place: str = Field(min_length=1, max_length=100)
    quota: int = Field(ge=1, le=10000)
    signup_deadline: datetime | None = None


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    type: ActivityType
    host: str
    cover_url: str | None = None
    description: str | None = None
    start_time: datetime
    end_time: datetime
    place: str
    quota: int
    remaining: int
    signup_deadline: datetime | None = None
    status: str
    created_at: datetime


class SignupResult(BaseModel):
    activity_id: int
    user_id: int
    status: str
    remaining: int