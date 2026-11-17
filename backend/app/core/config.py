"""全局配置：从 .env 读取，提供演示默认值。"""

import os
from pathlib import Path

from dotenv import load_dotenv

# backend 目录：app/core/config.py -> app -> backend
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Settings:
    """轻量配置对象，避免额外引入 pydantic-settings。"""

    APP_NAME: str = "新声平台后端"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-please-change-me-2026")
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "120"))

    # 演示默认 SQLite；生产可切 MySQL：
    # mysql+pymysql://user:pass@host:3306/xinsheng?charset=utf8mb4
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'xinsheng.db'}")

    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "20"))

    # 华为云大模型：OpenAI Chat Completions 兼容协议
    AI_ENABLED: bool = os.getenv("AI_ENABLED", "false").lower() == "true"
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "").rstrip("/")
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "pangu")
    AI_TIMEOUT: float = float(os.getenv("AI_TIMEOUT", "8"))

    # 演示缓存回放
    CACHE_REPLAY: bool = os.getenv("CACHE_REPLAY", "true").lower() == "true"
    CACHE_DIR: Path = Path(os.getenv("CACHE_DIR", str(BASE_DIR / "app" / "static" / "cache")))

    CORS_ORIGINS: list[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

    # 允许的笔记文件类型
    ALLOWED_NOTE_TYPES: set[str] = {"jpg", "jpeg", "png", "webp", "pdf"}

    # 生活板块商品图片允许类型
    ALLOWED_IMAGE_TYPES: set[str] = {"jpg", "jpeg", "png", "webp"}


settings = Settings()

# 启动即创建上传目录，避免首次上传报错
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)