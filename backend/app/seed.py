"""演示种子数据：首次启动写入兴趣标签，保证画像页有内容可选。"""

import logging

from app.core.database import SessionLocal
from app.models.entities import Tag

logger = logging.getLogger(__name__)

# (标签名, 分类, 图标)
SEED_TAGS: list[tuple[str, str, str]] = [
    ("篮球", "sports", "🏀"),
    ("足球", "sports", "⚽"),
    ("羽毛球", "sports", "🏸"),
    ("跑步", "sports", "🏃"),
    ("健身", "sports", "💪"),
    ("摄影", "arts", "📷"),
    ("绘画", "arts", "🎨"),
    ("音乐", "arts", "🎵"),
    ("舞蹈", "arts", "💃"),
    ("书法", "arts", "🖌️"),
    ("王者荣耀", "game", "🎮"),
    ("原神", "game", "🎲"),
    ("剧本杀", "game", "🕵️"),
    ("桌游", "game", "♟️"),
    ("编程", "study", "💻"),
    ("英语角", "study", "🗣️"),
    ("数学建模", "study", "📐"),
    ("考研", "study", "📚"),
    ("美食", "life", "🍜"),
    ("旅行", "life", "✈️"),
    ("追剧", "life", "🎬"),
    ("宠物", "life", "🐱"),
    ("动漫", "life", "🎌"),
]


def seed_tags() -> None:
    """标签表为空时写入预置标签。"""
    db = SessionLocal()
    try:
        if db.query(Tag).count() > 0:
            return
        for index, (name, category, icon) in enumerate(SEED_TAGS):
            db.add(Tag(tag_name=name, category=category, icon=icon, sort_no=index, status=1))
        db.commit()
        logger.info("已写入 %d 个预置兴趣标签", len(SEED_TAGS))
    finally:
        db.close()