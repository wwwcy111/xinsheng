"""搭子匹配相关 Schema。"""

from datetime import date, datetime

from pydantic import BaseModel, Field


class TopicOut(BaseModel):
    content: str


class MatchItemOut(BaseModel):
    match_id: int
    target_user_id: int
    nickname: str
    score: int
    common_tags: list[str] = Field(default_factory=list)
    reason: str
    topics: list[str] = Field(default_factory=list)


class RecommendationOut(BaseModel):
    batch_date: date
    items: list[MatchItemOut]


class GreetingCreate(BaseModel):
    target_user_id: int
    message: str = Field(min_length=1, max_length=100, description="招呼留言，100 字以内")


class GreetingOut(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    message: str
    created_at: datetime