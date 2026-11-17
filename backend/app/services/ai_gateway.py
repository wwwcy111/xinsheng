"""华为云大模型统一调用入口。

对接方式：华为云 ModelArts Studio / 盘古大模型提供的 OpenAI 兼容
Chat Completions 接口（POST {AI_BASE_URL}/chat/completions）。

设计原则：
1. 未开启 AI_ENABLED 或未配置地址时，本模块返回 None，由业务层使用
   本地模板兜底，保证演示环境零外部依赖也能跑通；
2. 所有异常均吞掉并记日志，绝不向接口层抛出，避免 AI 故障阻断主流程；
3. 支持本地缓存回放（CACHE_REPLAY=true），现场断网仍可展示 AI 效果；
4. 提示词集中在本文件，两个核心 Prompt 的完整内容写在下方注释中。

=====================================================================
核心 Prompt 1：搭子匹配（生成匹配理由 + 3 条破冰话题）
=====================================================================
【System】
你是“新声”校园平台的社交破冰助手，服务对象是大一新生。
你的任务：根据平台给出的两位新生画像，输出一条匹配理由和 3 条破冰聊天话题。

要求：
1. 匹配理由必须至少提到 1 个共同兴趣标签，语气真诚、具体，不超过 60 字；
2. 每条破冰话题 15-60 字，像同学之间自然开口，禁止“您好”“很高兴认识您”等客套模板；
3. 话题要结合共同标签或性格互补点，给出一个可以继续追问的具体切口；
4. 禁止涉及外貌、身材、家庭条件、成绩排名、恋爱经历等敏感内容；
5. 只输出 JSON，不要任何解释性文字，结构如下：
{"matches":[{"target_id":123,"reason":"...","topics":["...","...","..."]}]}

【User】
当前用户：{nickname}，性格：{personality}，社交偏好：{social_pref}，兴趣标签：{tags}
候选搭子：
1. target_id={id}，昵称={nickname}，性格={personality}，兴趣标签={tags}
2. ...
请为每位候选人生成 reason 与 topics，topics 固定 3 条。

=====================================================================
核心 Prompt 2：AI 笔记解析（导图 + 摘要 + 练习题）
=====================================================================
【System】
你是一名面向大一新生的学习笔记整理助手。用户会提供课堂笔记的 OCR 文本。
请完成三件事：
1. 生成思维导图：以笔记主题为根节点，提炼 2-4 个一级分支，每个分支 2-4 个子节点，
   节点文字不超过 20 字；
2. 生成知识点摘要：5-10 条，每条不超过 80 字，覆盖定义、公式、易错点；
3. 生成复习练习题：至少 5 道，题型混合（选择/填空/简答），每题给出答案与解析。

要求：
1. 只依据 OCR 文本，不得编造文本中不存在的公式或结论；
2. 若文本存在明显 OCR 错字，可按上下文合理纠正，但不得改变原意；
3. 只输出 JSON，结构如下：
{"mind_map":{"title":"...","children":[{"title":"...","children":[{"title":"..."}]}]},
 "summaries":["..."],
 "exercises":[{"question":"...","answer":"...","analysis":"..."}]}

【User】
以下是笔记 OCR 文本（可能含识别噪声）：
{ocr_text}
请按要求输出 JSON。
=====================================================================
"""

import hashlib
import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# 与上方注释保持一致，实际调用时使用这两个常量
MATCH_SYSTEM_PROMPT = """你是“新声”校园平台的社交破冰助手，服务对象是大一新生。
你的任务：根据平台给出的两位新生画像，输出一条匹配理由和 3 条破冰聊天话题。
要求：
1. 匹配理由必须至少提到 1 个共同兴趣标签，语气真诚、具体，不超过 60 字；
2. 每条破冰话题 15-60 字，像同学之间自然开口，禁止“您好”“很高兴认识您”等客套模板；
3. 话题要结合共同标签或性格互补点，给出一个可以继续追问的具体切口；
4. 禁止涉及外貌、身材、家庭条件、成绩排名、恋爱经历等敏感内容；
5. 只输出 JSON，不要任何解释性文字，结构如下：
{"matches":[{"target_id":123,"reason":"...","topics":["...","...","..."]}]}"""

NOTE_SYSTEM_PROMPT = """你是一名面向大一新生的学习笔记整理助手。用户会提供课堂笔记的 OCR 文本。
请完成三件事：
1. 生成思维导图：以笔记主题为根节点，提炼 2-4 个一级分支，每个分支 2-4 个子节点，节点文字不超过 20 字；
2. 生成知识点摘要：5-10 条，每条不超过 80 字，覆盖定义、公式、易错点；
3. 生成复习练习题：至少 5 道，题型混合（选择/填空/简答），每题给出答案与解析。
要求：
1. 只依据 OCR 文本，不得编造文本中不存在的公式或结论；
2. 若文本存在明显 OCR 错字，可按上下文合理纠正，但不得改变原意；
3. 只输出 JSON，结构如下：
{"mind_map":{"title":"...","children":[{"title":"...","children":[{"title":"..."}]}]},
 "summaries":["..."],
 "exercises":[{"question":"...","answer":"...","analysis":"..."}]}"""


def build_match_user_prompt(current: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    """拼装搭子匹配的 User Prompt。"""
    lines = [
        "当前用户：{nickname}，性格：{personality}，社交偏好：{social_pref}，兴趣标签：{tags}".format(**current),
        "候选搭子：",
    ]
    for index, item in enumerate(candidates, start=1):
        lines.append(
            "{idx}. target_id={id}，昵称={nickname}，性格={personality}，兴趣标签={tags}".format(
                idx=index, **item
            )
        )
    lines.append("请为每位候选人生成 reason 与 topics，topics 固定 3 条。")
    return "\n".join(lines)


def build_note_user_prompt(ocr_text: str) -> str:
    """拼装笔记解析的 User Prompt。"""
    return f"以下是笔记 OCR 文本（可能含识别噪声）：\n{ocr_text}\n请按要求输出 JSON。"


class AiGateway:
    """大模型调用网关。"""

    @property
    def available(self) -> bool:
        return bool(settings.AI_ENABLED and settings.AI_BASE_URL and settings.AI_API_KEY)

    async def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        cache_key: str | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any] | None:
        """调用大模型并解析 JSON；任何失败返回 None，由业务层降级。"""
        if cache_key and settings.CACHE_REPLAY:
            cached = self._read_cache(cache_key)
            if cached is not None:
                logger.info("AI 命中本地缓存：%s", cache_key)
                return cached

        if not self.available:
            logger.info("AI 未启用，走本地模板兜底：%s", cache_key or "no-cache")
            return None

        payload = {
            "model": settings.AI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7 if cache_key is None else 0.3,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {settings.AI_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=timeout or settings.AI_TIMEOUT) as client:
                response = await client.post(
                    f"{settings.AI_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                data = json.loads(content)
                if not isinstance(data, dict):
                    raise ValueError("模型返回的不是 JSON 对象")
                if cache_key:
                    self._write_cache(cache_key, data)
                return data
        except Exception as exc:  # noqa: BLE001 - AI 故障不得阻断主流程
            logger.warning("AI 调用失败，降级处理：%s", exc)
            return None

    def _cache_path(self, key: str):
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return settings.CACHE_DIR / f"{digest}.json"

    def _read_cache(self, key: str) -> dict[str, Any] | None:
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _write_cache(self, key: str, data: dict[str, Any]) -> None:
        try:
            settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            self._cache_path(key).write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            logger.warning("AI 缓存写入失败：%s", exc)


ai_gateway = AiGateway()