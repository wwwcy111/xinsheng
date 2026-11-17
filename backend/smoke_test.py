"""端到端冒烟测试：覆盖注册、匹配、笔记、生活板块主流程。

运行前先启动服务：
    uvicorn app.main:app --port 8000
然后执行：
    .venv\\Scripts\\python.exe smoke_test.py
"""

import json
import time

import httpx

BASE = "http://127.0.0.1:8000/api/v1"
SUFFIX = str(int(time.time()))[-6:]
client = httpx.Client(timeout=30)


def check(name: str, response: httpx.Response):
    payload = response.json()
    ok = response.status_code == 200 and payload.get("code") == 0
    print(("PASS" if ok else "FAIL"), name, response.status_code, json.dumps(payload, ensure_ascii=False)[:240])
    if not ok:
        raise SystemExit(1)
    return payload["data"]


def register(nickname: str, tag_ids: list[int], personality: str) -> tuple[str, int]:
    data = check(
        f"注册 {nickname}",
        client.post(
            f"{BASE}/auth/register",
            json={
                "nickname": nickname,
                "student_no_tail4": "0001",
                "password": "123456",
                "tag_ids": tag_ids,
                "personality": personality,
                "social_pref": "random",
                "college": "计算机学院",
            },
        ),
    )
    return data["token"], data["user"]["id"]


def main() -> None:
    check("健康检查", client.get(f"{BASE}/health"))
    tags = check("标签列表", client.get(f"{BASE}/tags"))
    print(f"     预置标签数量：{len(tags)}")
    if len(tags) < 20:
        print("FAIL 标签数量不足 20")
        raise SystemExit(1)

    token_a, uid_a = register(f"阿码{SUFFIX}", [1, 2, 3, 4], "introvert")
    token_b, _ = register(f"小新{SUFFIX}", [1, 2, 5, 6], "extrovert")
    register(f"同学{SUFFIX}", [1, 3, 7, 8], "neutral")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    me = check("当前用户", client.get(f"{BASE}/users/me", headers=headers_a))
    if len(me["tags"]) != 4 or not me["profile_complete"]:
        print("FAIL 画像标签或完整度不正确")
        raise SystemExit(1)

    rec = check("搭子推荐", client.get(f"{BASE}/match/recommendations", headers=headers_a))
    print(f"     推荐数量：{len(rec['items'])}，首条匹配分：{rec['items'][0]['score']}")
    if not rec["items"]:
        print("FAIL 未生成推荐")
        raise SystemExit(1)
    first = rec["items"][0]
    if len(first["topics"]) != 3 or not first["reason"]:
        print("FAIL 破冰话题或匹配理由缺失")
        raise SystemExit(1)

    check("获取话题", client.get(f"{BASE}/match/recommendations/{first['match_id']}/topics", headers=headers_a))
    check("发送招呼", client.post(f"{BASE}/match/greetings", json={"target_user_id": first["target_user_id"], "message": "一起去打球吗？"}, headers=headers_a))
    refreshed = check("换一批", client.post(f"{BASE}/match/recommendations/refresh", headers=headers_a))
    print(f"     换一批后数量：{len(refreshed['items'])}")

    item = check(
        "发布二手商品",
        client.post(
            f"{BASE}/market/items",
            json={
                "title": "考研数学教材（九成新）",
                "description": "只翻过前两章",
                "price": 25.5,
                "original_price": 68,
                "condition_level": "nine",
                "category": "textbook",
                "trade_place": "一食堂门口",
                "image_urls": [],
            },
            headers=headers_a,
        ),
    )
    listing = check("二手列表", client.get(f"{BASE}/market/items"))
    if listing["total"] < 1:
        print("FAIL 二手列表为空")
        raise SystemExit(1)
    check("商品详情", client.get(f"{BASE}/market/items/{item['id']}"))

    lost = check(
        "发布失物",
        client.post(
            f"{BASE}/lostfound",
            json={
                "type": "lost",
                "title": "丢失校园卡",
                "item_desc": "蓝色卡套，姓名首字母 M",
                "category": "card",
                "event_place": "图书馆三楼",
                "contact": "微信：demo",
            },
            headers=headers_a,
        ),
    )
    check("失物列表", client.get(f"{BASE}/lostfound?type=lost"))
    check("失物状态更新", client.patch(f"{BASE}/lostfound/{lost['id']}/status", json={"status": "returned"}, headers=headers_a))

    activity = check(
        "创建活动",
        client.post(
            f"{BASE}/activities",
            json={
                "title": "新生编程入门讲座",
                "type": "lecture",
                "host": "计算机学院学生会",
                "description": "面向零基础新生",
                "start_time": "2026-12-01T19:00:00",
                "end_time": "2026-12-01T20:30:00",
                "place": "报告厅",
                "quota": 2,
            },
            headers=headers_a,
        ),
    )
    check("活动列表", client.get(f"{BASE}/activities"))
    signup = check("活动报名", client.post(f"{BASE}/activities/{activity['id']}/signup", headers=headers_b))
    if signup["remaining"] != 1:
        print("FAIL 名额扣减不正确")
        raise SystemExit(1)

    note = check(
        "上传笔记",
        client.post(
            f"{BASE}/study/notes",
            files={"file": ("note.png", b"\x89PNG\r\n\x1a\n" + b"0" * 256, "image/png")},
            headers=headers_a,
        ),
    )
    check("写入 OCR 文本", client.post(f"{BASE}/study/notes/{note['id']}/ocr-text", json={"text": "第一章 函数与极限。" * 10}, headers=headers_a))
    parsed = check("解析笔记", client.post(f"{BASE}/study/notes/{note['id']}/parse", headers=headers_a))
    if parsed["status"] != "completed" or not parsed["mind_map"] or len(parsed["exercises"]) < 3:
        print("FAIL 笔记解析产出不完整")
        raise SystemExit(1)
    check("笔记状态", client.get(f"{BASE}/study/notes/{note['id']}/status", headers=headers_a))
    check("笔记列表", client.get(f"{BASE}/study/notes", headers=headers_a))

    print("\n全部冒烟测试通过。注册用户 ID：", uid_a)


if __name__ == "__main__":
    main()