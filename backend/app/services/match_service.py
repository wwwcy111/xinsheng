"""搭子匹配服务：规则打分 + AI 理由/话题生成。

匹配主体使用可解释规则，AI 仅负责润色与话题生成；
AI 不可用时自动降级为模板，保证接口稳定可用。
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import IcebreakerTopic, MatchRecord, Tag, User, UserTag
from app.services.ai_gateway import (
    MATCH_SYSTEM_PROMPT,
    ai_gateway,
    build_match_user_prompt,
)

logger = logging.getLogger(__name__)

MIN_TAGS = 3
MAX_TAGS = 10


def get_user_tags(db: Session, user_id: int) -> list[Tag]:
    """查询用户兴趣标签。"""
    return (
        db.query(Tag)
        .join(UserTag, UserTag.tag_id == Tag.id)
        .filter(UserTag.user_id == user_id, Tag.status == 1)
        .order_by(Tag.category, Tag.sort_no)
        .all()
    )


def personality_score(a: str, b: str) -> float:
    """性格互补度：内向-外向 1.0，内向/外向-中性 0.6，同向 0.3。"""
    if a == b:
        return 0.3
    if {a, b} == {"introvert", "extrovert"}:
        return 1.0
    return 0.6


def rule_score(my_tag_ids: set[int], other_tag_ids: set[int], my_personality: str, other_personality: str) -> tuple[int, list[int]]:
    """规则打分，返回 (0-100 分值, 共同标签ID列表)。"""
    union = my_tag_ids | other_tag_ids
    common = my_tag_ids & other_tag_ids
    jaccard = len(common) / len(union) if union else 0.0
    # 活跃度用固定值简化，避免演示数据无登录记录时分数失真
    activity = 0.5
    score = 100 * (0.55 * jaccard + 0.30 * personality_score(my_personality, other_personality) + 0.15 * activity)
    return round(score), sorted(common)


def template_reason(common_tag_names: list[str]) -> str:
    """AI 不可用时的匹配理由模板。"""
    if common_tag_names:
        return f"你们都关注{'、'.join(common_tag_names[:2])}，聊起来大概率同频。"
    return "你们的性格互补，认识一下也许会打开新的兴趣面。"


def template_topics(common_tag_names: list[str]) -> list[str]:
    """AI 不可用时的破冰话题模板。"""
    if common_tag_names:
        tag = common_tag_names[0]
        return [
            f"你平时{tag}一般去哪儿？最近有没有什么推荐？",
            f"看到你也喜欢{tag}，我最近刚开始，有什么入门建议吗？",
            f"如果周末约一次{tag}，你更倾向上午还是下午？",
        ]
    return [
        "你是哪个学院的？最近大学生活适应得怎么样？",
        "开学这段时间，有没有哪件事和你想象中不太一样？",
        "如果能给大一新生一条建议，你会说什么？",
    ]


def _load_existing(db: Session, user_id: int, batch_date: date) -> list[MatchRecord]:
    return (
        db.query(MatchRecord)
        .filter(MatchRecord.user_id == user_id, MatchRecord.batch_date == batch_date)
        .order_by(MatchRecord.score.desc())
        .all()
    )


def _build_items(db: Session, records: list[MatchRecord]) -> list[dict[str, Any]]:
    """把匹配记录组装为接口输出。"""
    items: list[dict[str, Any]] = []
    for record in records:
        target = db.get(User, record.target_user_id)
        if target is None:
            continue
        topic_rows = (
            db.query(IcebreakerTopic)
            .filter(IcebreakerTopic.match_id == record.id)
            .order_by(IcebreakerTopic.sort_no)
            .all()
        )
        common_ids: list[int] = list(record.common_tag_ids or [])
        tag_names = [t.tag_name for t in db.query(Tag).filter(Tag.id.in_(common_ids)).all()] if common_ids else []
        items.append(
            {
                "match_id": record.id,
                "target_user_id": target.id,
                "nickname": target.nickname,
                "score": record.score,
                "common_tags": tag_names,
                "reason": record.match_reason or template_reason(tag_names),
                "topics": [row.content for row in topic_rows] or template_topics(tag_names),
            }
        )
    return items


async def get_or_create_recommendations(db: Session, user: User, force_refresh: bool = False) -> tuple[date, list[dict[str, Any]]]:
    """获取当日推荐；无批次时生成 3 条，force_refresh=True 时重新生成。"""
    today = date.today()

    if not force_refresh:
        existing = _load_existing(db, user.id, today)
        if existing:
            return today, _build_items(db, existing)

    # 换一批：先清理当日旧记录（话题一并删除）
    old_records = _load_existing(db, user.id, today)
    if old_records:
        old_ids = [r.id for r in old_records]
        db.query(IcebreakerTopic).filter(IcebreakerTopic.match_id.in_(old_ids)).delete(synchronize_session=False)
        # 使用 ORM 删除，避免 SQLite 复用主键时与 identity map 冲突
        for record in old_records:
            db.delete(record)
        db.commit()

    my_tags = get_user_tags(db, user.id)
    my_tag_ids = {tag.id for tag in my_tags}
    if not (MIN_TAGS <= len(my_tag_ids) <= MAX_TAGS):
        return today, []  # 画像不完整，交由接口层提示

    # 7 日内已推荐过的搭子不再重复推荐
    recent_ids = {
        row[0]
        for row in db.query(MatchRecord.target_user_id)
        .filter(
            MatchRecord.user_id == user.id,
            MatchRecord.created_at >= datetime.now() - timedelta(days=7),
        )
        .all()
    }

    candidates = (
        db.query(User)
        .filter(User.id != user.id, User.status == 1)
        .all()
    )

    scored: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate.id in recent_ids:
            continue
        candidate_tags = get_user_tags(db, candidate.id)
        if len(candidate_tags) < MIN_TAGS:
            continue
        candidate_tag_ids = {tag.id for tag in candidate_tags}
        score, common_ids = rule_score(my_tag_ids, candidate_tag_ids, user.personality, candidate.personality)
        scored.append(
            {
                "user": candidate,
                "score": score,
                "common_ids": common_ids,
                "common_names": [t.tag_name for t in candidate_tags if t.id in common_ids],
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    top = scored[:3]
    if not top:
        return today, []

    # 调用 AI 生成理由与话题；失败则整体走模板
    ai_map: dict[int, dict[str, Any]] = {}
    prompt = build_match_user_prompt(
        {
            "nickname": user.nickname,
            "personality": user.personality,
            "social_pref": user.social_pref,
            "tags": "、".join(tag.tag_name for tag in my_tags),
        },
        [
            {
                "id": item["user"].id,
                "nickname": item["user"].nickname,
                "personality": item["user"].personality,
                "tags": "、".join(tag.tag_name for tag in get_user_tags(db, item["user"].id)),
            }
            for item in top
        ],
    )
    cache_key = f"match:{user.id}:{today}:{','.join(str(i) for i in sorted(my_tag_ids))}"
    ai_result = await ai_gateway.chat_json(MATCH_SYSTEM_PROMPT, prompt, cache_key=cache_key)
    if ai_result:
        for match in ai_result.get("matches", []):
            try:
                ai_map[int(match["target_id"])] = match
            except (KeyError, TypeError, ValueError):
                continue

    # 落库
    records: list[MatchRecord] = []
    for item in top:
        candidate = item["user"]
        ai_item = ai_map.get(candidate.id, {})
        reason = str(ai_item.get("reason") or template_reason(item["common_names"]))[:200]
        topics = ai_item.get("topics") or template_topics(item["common_names"])
        topics = [str(topic)[:100] for topic in topics[:3]]
        while len(topics) < 3:
            topics.append(template_topics(item["common_names"])[len(topics) % 3])

        record = MatchRecord(
            user_id=user.id,
            target_user_id=candidate.id,
            score=item["score"],
            common_tag_ids=item["common_ids"],
            match_reason=reason,
            batch_date=today,
            status="recommended",
        )
        db.add(record)
        db.flush()
        for index, content in enumerate(topics):
            db.add(IcebreakerTopic(match_id=record.id, content=content, sort_no=index))
        records.append(record)

    db.commit()
    for record in records:
        db.refresh(record)
    return today, _build_items(db, records)


def mark_greeted(db: Session, user_id: int, target_user_id: int) -> None:
    """把最近一条匹配记录标记为已招呼。"""
    record = (
        db.query(MatchRecord)
        .filter(MatchRecord.user_id == user_id, MatchRecord.target_user_id == target_user_id)
        .order_by(MatchRecord.created_at.desc())
        .first()
    )
    if record:
        record.status = "greeted"
        db.commit()