# 【码道新声】核心 AI Prompt 说明（比赛提交版）

| 项目 | 内容 |
| --- | --- |
| 适用平台 | 华为云 ModelArts Studio / 盘古大模型（OpenAI 兼容 Chat Completions） |
| 文档用途 | 比赛材料、项目文档、答辩 PPT |
| 对应代码 | `backend/app/services/ai_gateway.py` |
| 版本 | v1.0.0 |
| 更新日期 | 2026-11-13 |

---

## 一、使用说明

### 1.1 调用方式

华为云大模型统一使用 OpenAI 兼容协议：

```text
POST {AI_BASE_URL}/chat/completions
Authorization: Bearer {AI_API_KEY}
Content-Type: application/json
```

请求体：

```json
{
  "model": "pangu",
  "messages": [
    {"role": "system", "content": "系统提示词"},
    {"role": "user", "content": "用户提示词"}
  ],
  "temperature": 0.6,
  "max_tokens": 800,
  "response_format": {"type": "json_object"}
}
```

### 1.2 推荐参数

| 任务 | temperature | max_tokens | timeout | 说明 |
| --- | --- | --- | --- | --- |
| 搭子匹配 | 0.6 | 800 | 8 秒 | 需要一定表达多样性 |
| 笔记解析 | 0.3 | 2000 | 30 秒 | 要求稳定、忠实原文 |

### 1.3 在项目中配置

`.env`：

```ini
AI_ENABLED=true
AI_BASE_URL=https://你的ModelArts服务地址/v1
AI_API_KEY=你的密钥
AI_MODEL=pangu
AI_TIMEOUT=8
```

代码入口：`AiGateway.chat_json(system_prompt, user_prompt, cache_key, timeout)`。
模型返回非合法 JSON 时自动重试一次，仍失败则走本地模板兜底。

### 1.4 答辩 PPT 使用建议

- 每组 Prompt 配 1 页，左侧放 Prompt 结构图，右侧放输入/输出示例；
- 讲清“角色设定 + 输入约束 + 输出 Schema + 安全边界”四段式；
- 强调工程兜底：规则分兜底匹配、模板兜底笔记，保证现场演示不中断。

---

## 二、Prompt 1：AI 搭子匹配

### 2.1 System Prompt（完整）

```text
你是「码道新声」校园平台的 AI 搭子匹配官，服务对象是大一新生。
你的任务：根据两位新生的兴趣标签、性格倾向与社交偏好，评估他们的搭子匹配度，并生成可直接发送的破冰开场白。

评分规则（总分 100）：
1. 标签相似度（权重 55%）：共同兴趣标签越多、越具体，得分越高；仅有宽泛标签时适当降分。
2. 性格互补度（权重 30%）：内向↔外向为高度互补（90-100）；内向/外向↔中性为中度互补（60-80）；性格相同为低互补（40-60）。
3. 社交偏好契合度（权重 15%）：偏好一致得高分；一对一↔小群体为中等；差异过大适当降分。

输出要求：
1. match_score 为 0-100 的整数，必须与三项 breakdown 的加权结果一致（允许 ±3 分误差）。
2. match_reason 不超过 60 字，必须至少提到 1 个共同兴趣标签；若没有共同标签，则说明性格互补点。
3. openers 固定 3 条，每条 15-60 字，像同学之间自然开口，必须结合共同标签或性格特点，给出可继续追问的具体切口。
4. 禁止出现外貌、身材、家庭条件、成绩排名、恋爱经历等敏感内容；禁止使用“您好”“很高兴认识您”等客套模板。
5. 只输出合法 JSON，不要 Markdown 代码块，不要任何解释性文字。
```

### 2.2 User Prompt 模板

```text
请评估以下两位新生的搭子匹配度：

【当前用户】
- 昵称：{nickname}
- 兴趣标签：{tags}
- 性格：{personality}
- 社交偏好：{social_pref}

【候选搭子】
- 昵称：{nickname}
- 兴趣标签：{tags}
- 性格：{personality}
- 社交偏好：{social_pref}

字段取值：
- personality：introvert（内向）/ neutral（中性）/ extrovert（外向）
- social_pref：one_to_one（一对一深聊）/ small_group（小群体）/ random（随缘）

请严格按以下 JSON 结构输出：
{
  "match_score": 0,
  "score_breakdown": {
    "tag_similarity": 0,
    "personality_fit": 0,
    "social_fit": 0
  },
  "match_reason": "",
  "openers": ["", "", ""]
}
```

### 2.3 输入示例

```json
{
  "current_user": {
    "nickname": "阿码",
    "tags": ["篮球", "编程", "摄影"],
    "personality": "introvert",
    "social_pref": "one_to_one"
  },
  "candidate": {
    "nickname": "小新",
    "tags": ["篮球", "旅行", "摄影"],
    "personality": "extrovert",
    "social_pref": "one_to_one"
  }
}
```

### 2.4 输出示例

```json
{
  "match_score": 86,
  "score_breakdown": {
    "tag_similarity": 88,
    "personality_fit": 95,
    "social_fit": 90
  },
  "match_reason": "你们都爱篮球和摄影，一个慢热一个外向，刚好互补。",
  "openers": [
    "看到你也喜欢篮球，最近学校里哪块球场人比较少？",
    "你平时拍照用手机还是相机？我最近想入门摄影。",
    "如果周末约一次校园扫街拍照，你更想去老校区还是新校区？"
  ]
}
```

### 2.5 输出字段说明

| 字段 | 类型 | 约束 | 用途 |
| --- | --- | --- | --- |
| `match_score` | int | 0-100 | 展示匹配度 |
| `score_breakdown.tag_similarity` | int | 0-100 | 标签相似度 |
| `score_breakdown.personality_fit` | int | 0-100 | 性格互补度 |
| `score_breakdown.social_fit` | int | 0-100 | 社交偏好契合度 |
| `match_reason` | string | ≤60 字 | 推荐理由 |
| `openers` | string[] | 3 条，各 15-60 字 | 破冰开场白 |

### 2.6 工程落地说明

- 规则分与 Prompt 权重保持一致：`0.55 × 标签 Jaccard + 0.30 × 性格互补 + 0.15 × 活跃度`；
- 推荐展示分可采用融合策略：`round(0.6 × 规则分 + 0.4 × match_score)`，避免模型分数波动；
- 模型不可用时，`match_reason` 与 `openers` 使用模板兜底（见 `match_service.py`）。

---

## 三、Prompt 2：AI 笔记解析

### 3.1 System Prompt（完整）

```text
你是「码道新声」平台的 AI 笔记整理助手，服务对象是大一新生。
用户会提供一段课程笔记的 OCR 文本（可能含识别噪声）。请完成四项任务：

1. 核心考点：提取 5-8 个考试或复习最可能涉及的知识点，标注重要度（high/medium/low），每条不超过 60 字。
2. 思维导图：以课程主题为根节点，提炼 2-4 个一级分支，每个分支 2-4 个子节点，节点文字不超过 20 字。
3. 配套练习题：生成至少 5 道题，题型混合（choice 选择 / fill 填空 / short 简答），每题给出答案与解析。
4. 一句话总结：不超过 50 字，概括本次笔记的核心。

要求：
1. 只依据 OCR 文本，不得编造文本中不存在的公式、定理或结论。
2. OCR 明显错字可按上下文纠正，但不得改变原意。
3. 练习题必须能在原文中找到依据；解析要指出对应知识点。
4. 只输出合法 JSON，不要 Markdown 代码块，不要任何解释性文字。
```

### 3.2 User Prompt 模板

```text
课程名称：{course_name}
笔记 OCR 文本：
{ocr_text}

请严格按以下 JSON 结构输出：
{
  "course": "",
  "summary": "",
  "core_points": [
    {
      "point": "",
      "importance": "high",
      "note": ""
    }
  ],
  "mind_map": {
    "title": "",
    "children": [
      {
        "title": "",
        "children": [
          {"title": ""}
        ]
      }
    ]
  },
  "exercises": [
    {
      "type": "choice",
      "question": "",
      "answer": "",
      "analysis": ""
    }
  ]
}
```

### 3.3 输入示例

```text
课程名称：高等数学
笔记 OCR 文本：
第一章 函数与极限
1. 函数的概念：设 x 和 y 是两个变量，D 是实数集的子集。
2. 极限的定义：当 x 无限趋近于 x0 时，函数值无限趋近于 A。
3. 重要极限：lim(x→0) sinx/x = 1；lim(x→∞) (1+1/x)^x = e。
4. 连续的定义：函数在一点的极限等于该点函数值。
易错点：判断极限存在需要左右极限都存在且相等。
复习建议：先掌握定义，再练习夹逼准则与等价无穷小替换。
```

### 3.4 输出示例

```json
{
  "course": "高等数学",
  "summary": "本章围绕函数、极限与连续展开，重点掌握极限定义与两个重要极限。",
  "core_points": [
    {"point": "函数的概念与定义域", "importance": "medium", "note": "注意定义域与对应关系"},
    {"point": "极限的 ε-δ 定义", "importance": "high", "note": "考试高频，注意任意与存在的顺序"},
    {"point": "两个重要极限", "importance": "high", "note": "sinx/x 与 (1+1/x)^x"},
    {"point": "函数连续的定义", "importance": "high", "note": "极限值等于函数值"},
    {"point": "左右极限与极限存在的关系", "importance": "high", "note": "左右极限存在且相等"}
  ],
  "mind_map": {
    "title": "第一章 函数与极限",
    "children": [
      {
        "title": "函数",
        "children": [{"title": "函数概念"}, {"title": "定义域"}]
      },
      {
        "title": "极限",
        "children": [{"title": "极限定义"}, {"title": "两个重要极限"}]
      },
      {
        "title": "连续",
        "children": [{"title": "连续定义"}, {"title": "左右极限"}]
      }
    ]
  },
  "exercises": [
    {
      "type": "choice",
      "question": "下列极限中，值为 1 的是（ ）\nA. lim(x→0) sinx/x\nB. lim(x→∞) sinx/x\nC. lim(x→0) (1+1/x)^x\nD. lim(x→∞) (1+1/x)^x",
      "answer": "A",
      "analysis": "重要极限 lim(x→0) sinx/x = 1，对应“两个重要极限”考点。"
    },
    {
      "type": "fill",
      "question": "函数 f(x) 在 x0 处连续的充要条件是：______。",
      "answer": "lim(x→x0) f(x) = f(x0)",
      "analysis": "连续的定义要求极限值等于函数值，对应“连续的定义”考点。"
    },
    {
      "type": "short",
      "question": "判断函数极限存在需要满足什么条件？",
      "answer": "左右极限都存在且相等。",
      "analysis": "易错点：只验证单侧极限不能说明极限存在。"
    },
    {
      "type": "choice",
      "question": "lim(x→∞) (1+1/x)^x 的值为（ ）\nA. 0\nB. 1\nC. e\nD. 不存在",
      "answer": "C",
      "analysis": "第二个重要极限，结果为自然常数 e。"
    },
    {
      "type": "short",
      "question": "复习本章时，建议的顺序是什么？",
      "answer": "先掌握定义，再练习夹逼准则与等价无穷小替换。",
      "analysis": "原文复习建议，强调由定义到方法的顺序。"
    }
  ]
}
```

### 3.5 输出字段说明

| 字段 | 类型 | 约束 | 用途 |
| --- | --- | --- | --- |
| `course` | string | 课程名 | 笔记归类 |
| `summary` | string | ≤50 字 | 一句话总结 |
| `core_points[].point` | string | 5-8 条，≤60 字 | 核心考点 |
| `core_points[].importance` | string | high/medium/low | 重要度 |
| `core_points[].note` | string | ≤40 字 | 考点提示 |
| `mind_map.title` | string | 根节点 | 导图根 |
| `mind_map.children[]` | object[] | 2-4 个一级分支 | 导图结构 |
| `exercises[].type` | string | choice/fill/short | 题型 |
| `exercises[].question` | string | ≥5 道 | 题干（选择题选项写在题干内） |
| `exercises[].answer` | string | 必填 | 答案 |
| `exercises[].analysis` | string | 必填 | 解析 |

### 3.6 工程落地说明

- 模型输出映射到数据库字段：
  - `core_points[].point` → `t_study_note.summaries`
  - `mind_map` → `t_study_note.mind_map`
  - `exercises` → `t_study_note.exercises`
- 文本超过 6000 字时分块生成，合并导图与考点；
- 模型失败或输出不合法时，使用本地模板兜底，页面标注“降级结果”。

---

## 四、质量与安全约束

### 4.1 质量评估指标

| 指标 | 目标值 | 说明 |
| --- | --- | --- |
| JSON 合法率 | ≥98% | 解析失败自动重试一次 |
| 共同标签引用率 | 100% | 有共同标签时理由必须引用 |
| 开场白可用率 | ≥90% | 人工抽检 20 组 |
| 练习题原文依据率 | ≥95% | 解析需指向原文考点 |
| 敏感内容命中率 | 0 | 生成后二次过滤 |

### 4.2 安全边界

- 输入只传昵称、标签、性格与笔记文本，不传学号、联系方式；
- 输出经内容安全过滤，命中敏感词整条丢弃并重试；
- 笔记 Prompt 明确禁止编造原文不存在的公式或结论；
- 所有 AI 产出落库前做结构校验，避免脏数据。

### 4.3 答辩讲解要点（30 秒版）

1. 两组 Prompt 都采用“角色 + 规则 + JSON Schema + 安全边界”四段式，模型输出可直接入库；
2. 搭子匹配把评分维度写进提示词，规则分与模型分双轨，保证稳定与可解释；
3. 笔记解析坚持“只依据原文”，从源头抑制模型幻觉，并用模板兜底保证演示不中断。