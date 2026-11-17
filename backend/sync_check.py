"""同步回归脚本：不依赖 asyncio 事件循环，验证核心业务逻辑。

适用场景：受限环境无法绑定本地端口时，直接驱动服务层函数。
运行：
    .venv\\Scripts\\python.exe sync_check.py
"""

from app.core.database import SessionLocal, init_db
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.models.entities import StudyNote, Tag, User, UserTag
from app.seed import seed_tags
from app.services.match_service import get_or_create_recommendations, get_user_tags
from app.services.note_service import parse_note

PROFILE = [
    ("回归甲", "introvert", [1, 2, 3, 4]),
    ("回归乙", "extrovert", [1, 2, 5, 6]),
    ("回归丙", "neutral", [1, 3, 7, 8]),
]


def run_coro(coro):
    """驱动无真实 I/O 挂起的协程（AI 未启用时业务协程一次跑完）。"""
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise RuntimeError("协程出现真实挂起，当前环境无法驱动")


def main() -> None:
    init_db()
    seed_tags()

    db = SessionLocal()
    try:
        # 清理上次回归数据
        db.query(UserTag).filter(UserTag.user_id.in_([u.id for u in db.query(User).filter(User.nickname.like("回归%")).all()] or [0])).delete(synchronize_session=False)
        db.query(User).filter(User.nickname.like("回归%")).delete(synchronize_session=False)
        db.commit()

        assert db.query(Tag).count() >= 20, "预置标签不足"

        # 口令与令牌
        stored = hash_password("123456")
        assert verify_password("123456", stored) and not verify_password("bad", stored), "口令校验异常"

        users: list[User] = []
        for nickname, personality, tag_ids in PROFILE:
            user = User(
                nickname=nickname,
                student_no_tail4="0001",
                password_hash=hash_password("123456"),
                personality=personality,
                social_pref="random",
            )
            db.add(user)
            db.flush()
            for tag_id in tag_ids:
                db.add(UserTag(user_id=user.id, tag_id=tag_id))
            users.append(user)
        db.commit()
        for user in users:
            db.refresh(user)

        token = create_access_token(users[0].id)
        assert decode_access_token(token) == users[0].id, "令牌解析异常"
        assert len(get_user_tags(db, users[0].id)) == 4, "标签读取异常"

        # 匹配：首次生成
        batch_date, items = run_coro(get_or_create_recommendations(db, users[0]))
        assert items, "未生成推荐"
        assert len(items[0]["topics"]) == 3 and items[0]["reason"], "理由或话题缺失"
        print(f"PASS 首次推荐 {len(items)} 条，批次 {batch_date}，首条分数 {items[0]['score']}")

        # 匹配：换一批（验证 ORM 删除后重建无冲突）
        _, refreshed = run_coro(get_or_create_recommendations(db, users[0], force_refresh=True))
        assert refreshed, "换一批失败"
        print(f"PASS 换一批 {len(refreshed)} 条")

        # 笔记解析：无 AI 时走模板兜底
        note = StudyNote(
            owner_id=users[0].id,
            file_name="高数笔记.png",
            file_url="/uploads/demo.png",
            file_type="png",
            file_size=1024,
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        note = run_coro(parse_note(db, note))
        assert note.status == "completed", f"笔记状态异常：{note.status}"
        assert note.mind_map and note.mind_map.get("title"), "导图缺失"
        assert len(note.summaries or []) >= 5, "摘要不足"
        assert len(note.exercises or []) >= 5, "练习题不足"
        print(f"PASS 笔记解析完成，摘要 {len(note.summaries)} 条，练习题 {len(note.exercises)} 道")

        print("\n同步回归全部通过。")
    finally:
        db.close()


if __name__ == "__main__":
    main()