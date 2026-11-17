"""AI 笔记助手服务：OCR 文本 → 思维导图 / 摘要 / 练习题。

演示模式说明：
- 未接入 OCR 时，可用占位文本或人工粘贴文本走通大模型链路；
- 未启用 AI 或模型失败时，使用本地模板产出，保证 3 分钟 Demo 不中断。
"""

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import StudyNote
from app.services.ai_gateway import (
    NOTE_SYSTEM_PROMPT,
    ai_gateway,
    build_note_user_prompt,
)

logger = logging.getLogger(__name__)

# 演示模式占位文本：模拟一页大一高数笔记的 OCR 结果
DEMO_OCR_TEXT = """
第一章 函数与极限
1. 函数的概念：设 x 和 y 是两个变量，D 是实数集的子集。
2. 极限的定义：当 x 无限趋近于 x0 时，函数值无限趋近于 A。
3. 重要极限：lim(x→0) sinx/x = 1；lim(x→∞) (1+1/x)^x = e。
4. 连续的定义：函数在一点的极限等于该点函数值。
易错点：判断极限存在需要左右极限都存在且相等。
复习建议：先掌握定义，再练习夹逼准则与等价无穷小替换。
"""


def template_pack(note: StudyNote) -> dict[str, Any]:
    """AI 不可用时的本地模板产出，保证接口可演示。"""
    title = note.file_name.rsplit(".", 1)[0][:20] or "课堂笔记"
    return {
        "mind_map": {
            "title": title,
            "children": [
                {"title": "核心概念", "children": [{"title": "定义与条件"}, {"title": "关键结论"}]},
                {"title": "重点公式", "children": [{"title": "公式一"}, {"title": "公式二"}]},
                {"title": "易错点", "children": [{"title": "条件遗漏"}, {"title": "符号混淆"}]},
            ],
        },
        "summaries": [
            "先厘清本章核心概念的定义与适用条件。",
            "重点公式需要结合例题理解，而不是死记。",
            "易错点集中在条件判断与符号处理。",
            "复习时先做基础题，再做综合题。",
            "建议用自己的话复述一遍知识点。",
        ],
        "exercises": [
            {
                "question": "本章核心概念的定义是什么？",
                "answer": "参考笔记中的定义表述。",
                "analysis": "回答时注意定义中的前提条件，漏掉条件会失分。",
            },
            {
                "question": "列举本章的两个重点公式。",
                "answer": "参考笔记中的公式。",
                "analysis": "记忆公式时同时记住适用条件。",
            },
            {
                "question": "本章最容易出错的地方是什么？",
                "answer": "条件遗漏与符号混淆。",
                "analysis": "做题时先圈出条件，再进行计算。",
            },
            {
                "question": "如何安排本章的复习顺序？",
                "answer": "概念 → 公式 → 例题 → 综合题。",
                "analysis": "由浅入深，避免直接刷综合题。",
            },
            {
                "question": "用自己的话总结本章内容。",
                "answer": "围绕定义、公式、易错点三部分展开。",
                "analysis": "能复述说明真正理解。",
            },
        ],
    }


def _is_valid_pack(data: dict[str, Any] | None) -> bool:
    """校验模型结构化产出是否满足最低要求。"""
    if not isinstance(data, dict):
        return False
    mind_map = data.get("mind_map")
    summaries = data.get("summaries")
    exercises = data.get("exercises")
    if not isinstance(mind_map, dict) or not mind_map.get("title"):
        return False
    if not isinstance(summaries, list) or len(summaries) < 3:
        return False
    if not isinstance(exercises, list) or len(exercises) < 3:
        return False
    return True


async def parse_note(db: Session, note: StudyNote) -> StudyNote:
    """执行笔记解析，更新状态与产出。"""
    note.status = "generating"
    note.error_message = None
    db.commit()

    text = (note.ocr_text or DEMO_OCR_TEXT).strip()
    note.char_count = len(text)

    # 字符过少视为识别失败（对应 FR-028）
    if len(text) < 20:
        note.status = "failed"
        note.error_message = "识别文本过少，请重新上传清晰的笔记图片或 PDF"
        db.commit()
        return note

    prompt = build_note_user_prompt(text[:6000])
    cache_key = f"note:{note.id}:{hash(text)}"
    result = await ai_gateway.chat_json(NOTE_SYSTEM_PROMPT, prompt, cache_key=cache_key, timeout=30)

    pack = result if _is_valid_pack(result) else None
    if pack is None:
        logger.info("笔记 %s 使用本地模板兜底", note.id)
        pack = template_pack(note)

    note.mind_map = pack["mind_map"]
    note.summaries = pack["summaries"]
    note.exercises = pack["exercises"]
    note.status = "completed"
    note.error_message = None
    db.commit()
    db.refresh(note)
    return note


def set_ocr_text(db: Session, note: StudyNote, text: str) -> StudyNote:
    """写入 OCR 文本（供 OCR 服务或人工粘贴调用）。"""
    note.ocr_text = text
    note.char_count = len(text)
    db.commit()
    db.refresh(note)
    return note


def pack_to_json(note: StudyNote) -> str:
    """导出笔记产出，便于缓存或前端下载。"""
    return json.dumps(
        {
            "mind_map": note.mind_map,
            "summaries": note.summaries,
            "exercises": note.exercises,
        },
        ensure_ascii=False,
        indent=2,
    )