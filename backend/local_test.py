"""进程内接口验证：使用 FastAPI TestClient，不绑定网络端口。

适用于受限环境或快速回归；真实联调仍使用 smoke_test.py。
"""

import os
import socket
import tempfile
import time

from fastapi.testclient import TestClient

from app.main import app

# 部分受限环境会拦截 127.0.0.1 的 socketpair 连接，
# 这里在验证脚本内改用 Windows 支持的 AF_UNIX 实现；不影响业务代码。
_seq = 0
_original_socketpair = socket.socketpair


def _af_unix_socketpair(family=None, type=socket.SOCK_STREAM, proto=0):
    global _seq
    if family is not None:
        return _original_socketpair(family, type, proto)
    _seq += 1
    path = os.path.join(tempfile.gettempdir(), f"xs_sp_{os.getpid()}_{_seq}.sock")
    if os.path.exists(path):
        os.unlink(path)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(path)
        listener.listen(1)
        client.connect(path)
        server, _ = listener.accept()
    finally:
        listener.close()
        if os.path.exists(path):
            os.unlink(path)
    return server, client


if hasattr(socket, "AF_UNIX"):
    socket.socketpair = _af_unix_socketpair

SUFFIX = str(int(time.time()))[-6:]


def expect_ok(name, response):
    payload = response.json()
    ok = response.status_code == 200 and payload.get("code") == 0
    print(("PASS" if ok else "FAIL"), name, response.status_code, str(payload)[:200])
    if not ok:
        raise SystemExit(1)
    return payload["data"]


def main() -> None:
    with TestClient(app) as client:
        expect_ok("健康检查", client.get("/api/v1/health"))
        tags = expect_ok("标签列表", client.get("/api/v1/tags"))
        assert len(tags) >= 20, "标签数量不足"

        a = expect_ok(
            "注册用户A",
            client.post(
                "/api/v1/auth/register",
                json={
                    "nickname": f"阿码{SUFFIX}",
                    "student_no_tail4": "0001",
                    "password": "123456",
                    "tag_ids": [1, 2, 3, 4],
                    "personality": "introvert",
                },
            ),
        )
        b = expect_ok(
            "注册用户B",
            client.post(
                "/api/v1/auth/register",
                json={
                    "nickname": f"小新{SUFFIX}",
                    "student_no_tail4": "0002",
                    "password": "123456",
                    "tag_ids": [1, 2, 5, 6],
                    "personality": "extrovert",
                },
            ),
        )
        expect_ok(
            "注册用户C",
            client.post(
                "/api/v1/auth/register",
                json={
                    "nickname": f"同学{SUFFIX}",
                    "student_no_tail4": "0003",
                    "password": "123456",
                    "tag_ids": [1, 3, 7, 8],
                    "personality": "neutral",
                },
            ),
        )

        ha = {"Authorization": f"Bearer {a['token']}"}
        hb = {"Authorization": f"Bearer {b['token']}"}

        me = expect_ok("当前用户", client.get("/api/v1/users/me", headers=ha))
        assert len(me["tags"]) == 4 and me["profile_complete"], "画像异常"

        rec = expect_ok("搭子推荐", client.get("/api/v1/match/recommendations", headers=ha))
        assert rec["items"], "未生成推荐"
        first = rec["items"][0]
        assert len(first["topics"]) == 3 and first["reason"], "理由/话题缺失"
        print(f"     推荐 {len(rec['items'])} 条，首条分数 {first['score']}")

        expect_ok("获取话题", client.get(f"/api/v1/match/recommendations/{first['match_id']}/topics", headers=ha))
        expect_ok(
            "发送招呼",
            client.post("/api/v1/match/greetings", json={"target_user_id": first["target_user_id"], "message": "一起打球吗"}, headers=ha),
        )
        expect_ok("换一批", client.post("/api/v1/match/recommendations/refresh", headers=ha))

        item = expect_ok(
            "发布二手",
            client.post(
                "/api/v1/market/items",
                json={
                    "title": "考研数学教材",
                    "description": "九成新",
                    "price": 25.5,
                    "original_price": 68,
                    "condition_level": "nine",
                    "category": "textbook",
                    "trade_place": "一食堂门口",
                    "image_urls": [],
                },
                headers=ha,
            ),
        )
        listing = expect_ok("二手列表", client.get("/api/v1/market/items"))
        assert listing["total"] >= 1, "二手列表为空"
        expect_ok("二手详情", client.get(f"/api/v1/market/items/{item['id']}"))

        lost = expect_ok(
            "发布失物",
            client.post(
                "/api/v1/lostfound",
                json={
                    "type": "lost",
                    "title": "丢失校园卡",
                    "item_desc": "蓝色卡套",
                    "category": "card",
                    "event_place": "图书馆三楼",
                    "contact": "微信 demo",
                },
                headers=ha,
            ),
        )
        expect_ok("失物列表", client.get("/api/v1/lostfound?type=lost"))
        expect_ok("失物状态", client.patch(f"/api/v1/lostfound/{lost['id']}/status", json={"status": "returned"}, headers=ha))

        activity = expect_ok(
            "创建活动",
            client.post(
                "/api/v1/activities",
                json={
                    "title": "新生编程入门讲座",
                    "type": "lecture",
                    "host": "计算机学院学生会",
                    "description": "零基础友好",
                    "start_time": "2026-12-01T19:00:00",
                    "end_time": "2026-12-01T20:30:00",
                    "place": "报告厅",
                    "quota": 2,
                },
                headers=ha,
            ),
        )
        expect_ok("活动列表", client.get("/api/v1/activities"))
        signup = expect_ok("活动报名", client.post(f"/api/v1/activities/{activity['id']}/signup", headers=hb))
        assert signup["remaining"] == 1, "名额扣减异常"

        note = expect_ok(
            "上传笔记",
            client.post(
                "/api/v1/study/notes",
                files={"file": ("note.png", b"\x89PNG\r\n\x1a\n" + b"0" * 256, "image/png")},
                headers=ha,
            ),
        )
        expect_ok(
            "写入OCR文本",
            client.post(f"/api/v1/study/notes/{note['id']}/ocr-text", json={"text": "第一章 函数与极限。" * 10}, headers=ha),
        )
        parsed = expect_ok("解析笔记", client.post(f"/api/v1/study/notes/{note['id']}/parse", headers=ha))
        assert parsed["status"] == "completed" and parsed["mind_map"] and len(parsed["exercises"]) >= 3, "笔记产出不完整"
        expect_ok("笔记状态", client.get(f"/api/v1/study/notes/{note['id']}/status", headers=ha))
        expect_ok("笔记列表", client.get("/api/v1/study/notes", headers=ha))

        print("\n全部进程内验证通过。")


if __name__ == "__main__":
    main()