"""数据库连接与会话管理。

演示默认 SQLite，模型同时兼容 MySQL（字段类型均为 SQLAlchemy 通用类型）。
切换 MySQL 只需修改 .env 中的 DATABASE_URL。
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# SQLite 需要关闭线程检查；MySQL 不需要该参数
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：每个请求一个会话，结束后自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """创建所有表（演示环境使用；生产建议改用迁移脚本）。"""
    # 必须先导入模型，Base.metadata 才有表定义
    from app.models import entities  # noqa: F401

    Base.metadata.create_all(bind=engine)