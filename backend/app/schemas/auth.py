"""认证与用户画像相关 Schema。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Personality = Literal["introvert", "neutral", "extrovert"]
SocialPref = Literal["one_to_one", "small_group", "random"]


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tag_name: str
    category: str
    icon: str | None = None


class RegisterRequest(BaseModel):
    """注册请求：昵称 + 学号后四位 + 口令，可同时录入兴趣标签。"""

    nickname: str = Field(min_length=1, max_length=20, description="昵称，平台内唯一")
    student_no_tail4: str = Field(pattern=r"^\d{4}$", description="学号后四位")
    password: str = Field(min_length=6, max_length=32, description="口令，6-32 位")
    tag_ids: list[int] = Field(default_factory=list, description="兴趣标签 ID 列表，建议 3-10 个")
    personality: Personality = "neutral"
    social_pref: SocialPref = "random"
    college: str | None = Field(default=None, max_length=50)
    major: str | None = Field(default=None, max_length=50)
    contact: str | None = Field(default=None, max_length=50)
    bio: str | None = Field(default=None, max_length=200)


class LoginRequest(BaseModel):
    nickname: str
    password: str


class ProfileUpdateRequest(BaseModel):
    """画像更新：字段均可选，只更新传入项。"""

    tag_ids: list[int] | None = None
    personality: Personality | None = None
    social_pref: SocialPref | None = None
    contact: str | None = Field(default=None, max_length=50)
    bio: str | None = Field(default=None, max_length=200)
    college: str | None = Field(default=None, max_length=50)
    major: str | None = Field(default=None, max_length=50)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    student_no_tail4: str
    personality: Personality
    social_pref: SocialPref
    college: str | None = None
    major: str | None = None
    class_name: str | None = None
    contact: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    status: int
    created_at: datetime
    tags: list[TagOut] = Field(default_factory=list)
    profile_complete: bool = False


class TokenOut(BaseModel):
    token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserOut