# 架构设计：【码道】新声——大一新生“破冰·学业·生活”全能赋能平台

## 文档信息

| 项目 | 内容 |
| --- | --- |
| 设计依据 | `spec.md` v1.0.0（FR-001～FR-048、NFR-001～NFR-014、AC-001～AC-024） |
| 版本 | v1.0.0 |
| 日期 | 2026-11-13 |
| 状态 | 待评审 |
| 设计目标 | 轻量化、可演示、AI 真实调用、3 分钟内跑通三大模块 |
| 部署形态 | 单实例前后端分离，本地/SQLite 起步，可平滑切换华为云托管 |

---

## 1. 设计目标与原则

1. **模块化单体优先**：不拆微服务，按业务模块分包，单进程启动，降低演示环境复杂度。
2. **规则兜底、AI 增强**：匹配主逻辑用可解释规则，大模型只负责“理由润色 + 破冰话题”；笔记解析由 OCR + 大模型完成，但必须有结构校验与模板降级。
3. **接口即契约**：前后端以 REST + JSON 为唯一契约，接口路径与 spec 的 FR 编号一一映射，便于验收追溯。
4. **演示稳定优先**：所有 AI 产出支持本地缓存回放，现场断网仍可按预置数据完成 3 分钟脚本。
5. **华为云原生适配**：大模型、OCR、对象存储、内容审核均通过统一适配层接入，配置切换不改业务代码。
6. **轻量依赖**：前端不引入重型图形库，思维导图采用递归树组件自渲染；后端不引入消息队列，异步任务用进程内后台任务 + 数据库状态机。

---

## 2. 技术选型

### 2.1 前端

| 维度 | 选型 | 理由 |
| --- | --- | --- |
| 框架 | Vue 3.4 + TypeScript | 上手快、组件化清晰、CodeArts IDE 模板支持完善 |
| 构建 | Vite 5 | 冷启动快，演示构建耗时低 |
| 路由 | Vue Router 4 | 三大模块 + 管理端按路由懒加载 |
| 状态 | Pinia | 轻量，保存用户会话、画像、推荐批次 |
| UI | Element Plus（按需引入） | 表单、列表、上传、弹窗组件齐全，减少自研成本 |
| 请求 | Axios + 统一拦截器 | 注入 Bearer Token、统一错误码提示、request_id 透传 |
| 思维导图 | 自研 `MindMapTree.vue` 递归组件 | 后端返回树形 JSON，前端纯 CSS/SVG 连线渲染，零重型依赖 |
| 样式 | 原生 CSS + CSS 变量 + 媒体查询 | 375px 起响应式，避免引入额外预处理器 |
| 测试 | Vitest（可选） | 演示期仅覆盖关键工具函数 |

### 2.2 后端

| 维度 | 选型 | 理由 |
| --- | --- | --- |
| 语言/框架 | Python 3.11 + FastAPI | 异步友好、AI SDK 生态成熟、自动生成 OpenAPI 文档 |
| ASGI | Uvicorn | 单进程即可支撑 50 并发演示 |
| 数据校验 | Pydantic v2 | 请求/响应模型与 OpenAPI 同源 |
| ORM | SQLAlchemy 2.x | 轻量、支持事务与条件更新 |
| 数据库 | SQLite（WAL 模式） | 零运维，演示够用；预留 PostgreSQL 切换 |
| 认证 | JWT（HS256）+ bcrypt | 无状态会话，满足 NFR-006 |
| 异步任务 | FastAPI BackgroundTasks + 线程池 | 笔记解析异步化，避免请求阻塞；状态落库供轮询 |
| 文件存储 | 本地 `uploads/`（默认）→ 华为云 OBS（可切换） | 演示零依赖，生产可切换 |
| 日志 | 标准 logging + request_id 中间件 | 满足 NFR-010 全链路串联 |
| 文档 | FastAPI 自动 `/docs` | 评审现场可直接展示接口契约 |

### 2.3 AI 与外部服务

| 能力 | 华为云服务 | 接入方式 | 用途 |
| --- | --- | --- | --- |
| 大模型对话 | ModelArts Studio / 盘古大模型（OpenAI 兼容） | `httpx` 调用 `/v1/chat/completions` | 破冰话题、匹配理由、笔记三类产出 |
| OCR | 华为云 OCR 通用文字识别 | SDK 或 REST | 笔记图片/PDF 文本提取 |
| 内容审核 | 华为云内容审核（可选） | REST | 发布内容与 AI 产出过滤 |
| 对象存储 | 华为云 OBS | SDK / S3 兼容 | 图片、PDF 存储 |
| PDF 转图 | pypdfium2（本地库） | 本地处理 | PDF 逐页转图后送 OCR |

### 2.4 选型对比与取舍

| 备选 | 结论 | 原因 |
| --- | --- | --- |
| Spring Boot + Vue | 不选 | 启动与构建偏重，竞赛演示收益低 |
| Node.js + Express | 备选 | 可行，但 OCR/AI 的 Python SDK 更成熟 |
| React + Next.js | 不选 | SSR 对演示无增益，增加构建复杂度 |
| 微服务 + MQ | 不选 | 单实例演示无需拆分，MQ 提高部署门槛 |
| Redis | 不选（可选） | SQLite 状态字段足以支撑轮询与缓存 |

### 2.5 开发环境适配（华为云 CodeArts IDE）

1. 工作区根目录即仓库根，前后端各自独立依赖，互不干扰。
2. CodeArts 终端并行启动：`uvicorn app.main:app --reload` 与 `npm run dev`。
3. Vite 配置 `server.proxy` 将 `/api` 代理到 `http://127.0.0.1:8000`，规避跨域。
4. `.env` 管理模型地址、密钥、OCR 开关、缓存回放开关；`.env.example` 入库，真实密钥不入库。
5. 推荐安装插件：Python、ESLint、Vue - Official。

---

## 3. 总体架构

### 3.1 架构图（文字版）

```text
┌─────────────────────────────────────────────────────────────────────┐
│                          客户端层（Web 浏览器）                       │
│  Vue3 SPA：首页 / 破冰交友 / 学霸互助圈 / 生活百宝箱 / 管理端         │
│  组件：画像表单、推荐卡片、话题复制、导图树、练习题、商品与活动列表    │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTPS + JSON（Bearer Token）
┌───────────────────────────────▼─────────────────────────────────────┐
│                     接入层（Vite Dev Proxy / Nginx）                  │
│  静态资源托管、/api 反向代理、gzip、访问日志、请求超时                 │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                应用层：FastAPI 模块化单体（单进程）                   │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┬─────────┐ │
│  │ Auth     │ Profile  │ Match    │ Study    │ Life     │ Admin   │ │
│  │ 认证会话 │ 画像标签 │ 破冰匹配 │ 招募/笔记│ 二手/失物│ 审核/重置│ │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴─────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 公共能力：RequestID 中间件 / 统一异常 / 权限依赖 / 审计日志      │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────┬───────────────────────────────────┬─────────────────┘
                │                                   │
┌───────────────▼─────────────────┐   ┌─────────────▼─────────────────┐
│  领域服务层（services）          │   │  异步任务层（tasks）           │
│  MatchService：规则打分+候选过滤 │   │  NotePipeline：OCR→清洗→LLM    │
│  NoteService：笔记状态机         │   │  状态机落库，前端 2s 轮询      │
│  MarketService / LifeService     │   │  失败重试（上限 3 次）         │
│  AiGateway：对话/结构化/降级     │   │  CacheReplay：演示缓存回放     │
│  SafetyService：内容安全         │   │                               │
└───────┬──────────────┬──────────┘   └───────────────┬───────────────┘
        │              │                              │
┌───────▼──────┐ ┌─────▼──────────────┐ ┌────────────▼──────────────┐
│ 数据层        │ │ 文件层              │ │ 外部能力层（华为云）       │
│ SQLite(WAL)  │ │ 本地 uploads/       │ │ 盘古/ModelArts 大模型      │
│ 业务表+状态机 │ │ 或 OBS 对象存储     │ │ OCR 通用文字识别           │
│ 审计日志      │ │ 缓存 JSON 目录      │ │ 内容审核（可选）           │
└──────────────┘ └────────────────────┘ └───────────────────────────┘
```

### 3.2 分层职责

| 层 | 职责 | 关键约束 |
| --- | --- | --- |
| 客户端层 | 页面渲染、表单校验、轮询、剪贴板、响应式 | 不直接持有模型密钥；只经 `/api` 访问 |
| 接入层 | 静态资源、反向代理、跨域处理 | 统一超时与错误页 |
| 应用层 | 路由、鉴权、参数校验、编排领域服务 | 每个接口对应明确 FR |
| 领域服务层 | 业务规则、AI 调用、降级策略 | 纯业务，不依赖 HTTP 上下文 |
| 异步任务层 | 长耗时任务与状态推进 | 任务失败必须落库可查询 |
| 数据/文件层 | 持久化与素材存储 | 事务保证名额/状态一致 |
| 外部能力层 | 大模型、OCR、审核、OBS | 全部经适配器，可开关切换 |

### 3.3 关键架构决策（ADR 摘要）

| 编号 | 决策 | 理由 | 影响 |
| --- | --- | --- | --- |
| ADR-01 | 模块化单体而非微服务 | 单实例演示、降低运维 | 后续可按模块拆分 |
| ADR-02 | 匹配采用“规则打分 + LLM 解释” | 结果可解释、稳定、可控 | LLM 失败不影响推荐可用 |
| ADR-03 | 笔记解析异步 + 数据库状态机 | 60 秒链路不阻塞请求 | 前端轮询，任务可重试 |
| ADR-04 | 统一 AiGateway + JSON Schema 校验 | 模型输出不稳定，需强约束 | 所有 AI 调用收敛到一处 |
| ADR-05 | 缓存回放开关 | 演示现场网络不可控 | 命中缓存不发起外部调用 |
| ADR-06 | SQLite 条件更新保证名额一致 | 避免并发超卖（R-08） | `UPDATE ... WHERE remaining > 0` |

---

## 4. 模块与接口规划

### 4.1 通用约定

- 基础路径：`/api/v1`
- 鉴权：`Authorization: Bearer <token>`；白名单：注册、登录、健康检查、静态资源
- 响应包：`{ "code": 0, "message": "ok", "data": {...}, "request_id": "..." }`
- 业务错误码：`40001` 参数错误、`40101` 未登录、`40301` 无权限、`40401` 不存在、`40901` 状态冲突、`42901` 频率超限、`50001` 服务异常、`50301` AI 降级
- 分页：`page`、`page_size`（默认 10，上限 50），返回 `items`、`total`
- 每个接口在 OpenAPI `tags` 中标注模块，描述中标注追溯 FR 编号

### 4.2 认证与画像

| 方法 | 路径 | 说明 | 追溯 |
| --- | --- | --- | --- |
| POST | `/auth/register` | 昵称 + 学号后四位 + 口令注册 | FR-043 |
| POST | `/auth/login` | 登录，签发 JWT；连续 5 次失败锁定 10 分钟 | FR-043/044 |
| POST | `/auth/logout` | 注销会话 | FR-043 |
| GET | `/users/me` | 当前用户与画像 | FR-002 |
| PUT | `/users/me/profile` | 保存兴趣标签、性格、社交偏好 | FR-001~003 |
| GET | `/tags` | 预置兴趣标签（≥20 个） | FR-003 |

### 4.3 模块 A：AI 破冰交友

| 方法 | 路径 | 说明 | 追溯 |
| --- | --- | --- | --- |
| GET | `/match/recommendations` | 获取当日推荐批次（无则生成 3 条） | FR-004~007 |
| POST | `/match/recommendations/refresh` | 换一批（当日限 1 次） | FR-010 |
| GET | `/match/recommendations/{match_id}/topics` | 获取该推荐下的破冰话题 | FR-008 |
| POST | `/match/greetings` | 发送招呼（留言 ≤100 字，24h 内 ≤3 次） | FR-011/012 |
| GET | `/match/greetings/received` | 收到的招呼列表 | FR-011 |
| GET | `/match/greetings/sent` | 发出的招呼列表 | FR-011 |

请求/响应要点：

- `GET /match/recommendations` 返回 `batch_date`、`items[{match_id, nickname, common_tags[], score, reason, topics[]}]`
- `POST /match/greetings` 入参 `{target_user_id, message}`；超限返回 `42901`
- 所有推荐生成前校验画像完整性，不完整返回 `40001` 并携带缺失项

### 4.4 模块 B：学霸互助圈

| 方法 | 路径 | 说明 | 追溯 |
| --- | --- | --- | --- |
| GET | `/study/posts` | 招募帖列表，支持 `type`、`keyword` 筛选 | FR-016 |
| POST | `/study/posts` | 发布招募帖（待审核/演示直发） | FR-014/015 |
| GET | `/study/posts/{post_id}` | 招募帖详情与报名状态 | FR-016 |
| POST | `/study/posts/{post_id}/signup` | 报名，名额条件扣减 | FR-017/018/042 |
| DELETE | `/study/posts/{post_id}/signup` | 取消报名并释放名额 | FR-019 |
| POST | `/study/notes` | `multipart/form-data` 上传笔记，返回 `note_id` | FR-020/021 |
| GET | `/study/notes` | 我的笔记列表（倒序） | FR-030 |
| GET | `/study/notes/{note_id}` | 笔记详情：导图、摘要、练习题 | FR-024~027 |
| GET | `/study/notes/{note_id}/status` | 处理状态（识别中/生成中/完成/失败） | FR-023 |
| POST | `/study/notes/{note_id}/regenerate` | 基于已有 OCR 文本重新生成（≤3 次） | FR-029 |

请求/响应要点：

- 上传校验：`jpg/png/webp/pdf`、≤20MB，不合法返回 `40001`
- 详情返回：`mind_map: {title, children[]}`、`summaries: string[]`、`exercises: [{question, answer, analysis}]`
- 状态接口轻量返回 `{status, progress, error_message}`，前端 2 秒轮询

### 4.5 模块 C：校园生活百宝箱

| 方法 | 路径 | 说明 | 追溯 |
| --- | --- | --- | --- |
| GET | `/market/items` | 在售商品列表，支持关键词/价格区间 | FR-033 |
| POST | `/market/items` | 发布商品（1~6 张图） | FR-031/032 |
| GET | `/market/items/{item_id}` | 商品详情 | FR-033 |
| POST | `/market/items/{item_id}/intents` | 提交购买意向，商品转“有意向” | FR-034 |
| PATCH | `/market/items/{item_id}/status` | 卖家标记已售/下架并关闭意向 | FR-035 |
| GET | `/lostfound` | 失物/招领分栏列表 | FR-036 |
| POST | `/lostfound` | 发布失物或招领 | FR-036 |
| POST | `/lostfound/{lf_id}/claims` | 提交认领说明（≥10 字） | FR-037 |
| POST | `/lostfound/{lf_id}/claims/{claim_id}/confirm` | 发布者确认归还 | FR-037 |
| GET | `/clubs` | 社团列表 | FR-038 |
| GET | `/activities` | 活动列表（开始时间升序，未结束） | FR-039 |
| POST | `/activities/{activity_id}/signup` | 活动报名，名额条件扣减 | FR-040/042 |
| DELETE | `/activities/{activity_id}/signup` | 活动开始前取消报名 | FR-041 |

### 4.6 管理端与系统

| 方法 | 路径 | 说明 | 追溯 |
| --- | --- | --- | --- |
| GET | `/admin/audits` | 待审核内容列表 | FR-045 |
| POST | `/admin/audits/{audit_id}/approve` | 审核通过 | FR-045 |
| POST | `/admin/audits/{audit_id}/reject` | 审核拒绝/下架 | FR-046 |
| POST | `/admin/reset-demo` | 一键重置演示数据 | FR-047 |
| GET | `/admin/logs` | 关键操作日志 | FR-048 |
| GET | `/health` | 服务与依赖健康检查 | NFR-014 |

### 4.7 接口清单汇总

| 模块 | 接口数 | 关键写操作 | 幂等/并发策略 |
| --- | --- | --- | --- |
| 认证与画像 | 6 | 注册、登录、画像保存 | 昵称唯一索引；登录失败计数 |
| 模块 A | 6 | 生成批次、换一批、发招呼 | 当日批次唯一；招呼按时间窗计数 |
| 模块 B | 10 | 发帖、报名、上传、重新生成 | 报名唯一索引 + 条件扣减；任务状态机 |
| 模块 C | 13 | 发布、意向、认领、报名 | 报名唯一索引 + 条件扣减 |
| 管理/系统 | 6 | 审核、重置 | 重置使用事务 + 幂等键 |
| 合计 | 41 | — | — |

---

## 5. 华为云 AI 能力接入设计

### 5.1 统一 AI 网关（AiGateway）

所有 AI 调用收敛到 `services/ai_gateway.py`，对外暴露三个方法：

| 方法 | 输入 | 输出 | 用途 |
| --- | --- | --- | --- |
| `chat_text(system, user, timeout)` | 提示词 | 纯文本 | 兜底与自由生成 |
| `chat_json(system, user, schema, timeout)` | 提示词 + JSON Schema | 已校验对象 | 结构性产出 |
| `embed(texts)`（可选） | 文本列表 | 向量 | 标签语义相似度增强 |

网关内部职责：

1. **模型路由**：主模型 → 备用模型（配置项 `LLM_PRIMARY` / `LLM_FALLBACK`）。
2. **超时控制**：话题 8 秒、笔记生成 30 秒（对应 NFR-002）。
3. **结构化约束**：强制 `response_format=json_object` + Pydantic 校验，失败重试 1 次。
4. **内容安全**：调用 `SafetyService` 过滤，命中则丢弃并重试 1 次，再失败走模板。
5. **缓存回放**：`CACHE_REPLAY=on` 时按 `task + hash(input)` 读取 `cache/*.json`，不发起外部调用（NFR-012）。
6. **可观测**：记录模型名、耗时、token 数、状态码、request_id。

### 5.2 核心任务一：搭子匹配调用链路

**定位**：规则主导匹配，大模型负责“匹配理由 + 破冰话题”，保证可解释、可降级。

```text
前端 GET /match/recommendations
  → Auth 依赖解析用户
  → MatchService.get_daily_batch(user)
      1. 校验画像完整（标签 3~10、性格、社交偏好）         [FR-001]
      2. 查询当日批次：命中则直接返回，不重复生成            [FR-004/005]
      3. 构造候选池：排除本人、已屏蔽、7 日内已推荐、画像不全 [FR-013]
      4. 规则打分：
         score = 100 * (0.55 * 标签Jaccard + 0.30 * 性格互补 + 0.15 * 活跃度)
         性格互补矩阵：内向↔外向=1.0，内向↔中性=0.6，同向=0.3
      5. 取 Top 3 作为推荐对象                              [FR-006]
      6. 调用 AiGateway.chat_json 一次批量生成：
         input  = 双方昵称 + 共同/差异标签 + 性格枚举（不含隐私字段）
         output = [{target_id, reason, topics:[3 条]}]
      7. SafetyService 过滤话题；失败则模板兜底
      8. 事务写入 match_record + icebreaker_topic，标记 batch_date
  → 返回 items（含 score、reason、topics）
```

**提示词结构（要点）**

- System：角色设定 + 输出必须是合法 JSON + 话题 15~60 字 + 禁止敏感内容
- User：结构化画像（JSON）+ 候选列表 + 输出 schema
- 温度 0.7，`max_tokens` 800

**降级链**：主模型 → 备用模型 → 规则模板（`“你们都关注{共同标签}，可以从最近一次相关经历聊起。”`）→ 缓存回放。

### 5.3 核心任务二：笔记解析调用链路

**定位**：异步流水线，OCR + 大模型结构化，状态机驱动前端轮询。

```text
前端 POST /study/notes（文件）
  → 校验格式/大小（jpg/png/webp/pdf，≤20MB）              [FR-020/021]
  → 存储文件（本地 uploads/ 或 OBS）                        [D4]
  → 创建 Note(status=ocr_pending)，返回 note_id
  → BackgroundTasks 触发 NotePipeline.run(note_id)

NotePipeline（tasks/note_pipeline.py）：
  1. OCR：PDF 先逐页转图，再调用华为云 OCR               [FR-022]
  2. 文本清洗：去页眉页脚、合并断行、去重
  3. 有效性校验：有效字符 < 20 → status=failed + 明确提示  [FR-028]
  4. 分块：按 ≤6000 字切分，保留小节标题
  5. 状态置 generating，调用 AiGateway.chat_json：
     output schema = {
       mind_map: {title, children[]},           // 层级≥2，节点≥8  [FR-024]
       summaries: string[],                      // 5~10 条，单条≤80 字 [FR-025]
       exercises: [{question, answer, analysis}] // ≥5 道            [FR-026]
     }
  6. 结构校验：层级/节点数/条数不达标 → 局部重试 1 次
  7. SafetyService 二次过滤
  8. 事务写入 mind_map + summary + exercise，status=completed
  9. 任一步失败：保留 OCR 文本，status=failed，允许 regenerate    [FR-029]

前端 GET /study/notes/{id}/status 每 2 秒轮询                  [FR-023]
完成后 GET /study/notes/{id} 渲染导图树、摘要、练习题
```

**长文本策略**

| 文本长度 | 策略 |
| --- | --- |
| ≤ 6000 字 | 单次调用返回三类产出 |
| 6000~18000 字 | 按小节分块，逐块生成后合并；导图取二级合并 |
| > 18000 字 | 仅取前 3 个分块生成，页面标注“基于前 N 页” |

**降级链**：OCR 失败 → `failed` + 重新上传引导；LLM 失败 → 缓存回放 → 模板产出（导图取标题层级、摘要取首句、练习题给通用自测题）并标注“降级结果”（NFR-011）。

### 5.4 结构化输出规范

1. 统一使用 JSON Schema 约束，禁止模型自由发挥字段名。
2. 解析失败时执行“修复重试”：将错误信息回填提示词再请求 1 次。
3. 所有枚举字段（性格、类型、状态）在 Pydantic 中定义 `Literal`。
4. 模型输出不得包含用户联系方式、学号等隐私字段（接口约束 2）。

### 5.5 内容安全与合规

| 环节 | 措施 |
| --- | --- |
| 用户发布 | 违规词本地过滤 + 命中转“待审核”（FR-045） |
| AI 生成 | 生成后二次过滤；命中整条丢弃并重试 1 次，再失败用模板（NFR-008） |
| 提示词 | 仅传昵称、标签、性格枚举，不传学号/联系方式（接口约束 2） |
| 日志 | 联系方式、口令、学号脱敏后落日志 |

---

## 6. 数据设计

### 6.1 表清单（与 spec 第 7 章实体映射）

| 表 | 关键字段 | 关键索引/约束 |
| --- | --- | --- |
| `user` | id, nickname, student_no_tail4, password_hash, personality, social_pref, contact, status | `uk_nickname` |
| `tag` / `user_tag` | id, name, category / user_id, tag_id | `uk_user_tag(user_id, tag_id)` |
| `match_record` | id, user_id, target_user_id, score, reason, batch_date, status | `uk_batch(user_id, target_user_id, batch_date)` |
| `icebreaker_topic` | id, match_id, content, used_flag | `idx_match_id` |
| `greeting` | id, from_user_id, to_user_id, message, created_at | `idx_pair_time(from_user_id, to_user_id, created_at)` |
| `study_post` | id, author_id, title, type, start_time, location, capacity, joined_count, status | `idx_status_type` |
| `study_signup` | id, post_id, user_id, status | `uk_active(post_id, user_id)` |
| `note` | id, owner_id, file_url, file_type, file_size, status, retry_count, created_at | `idx_owner_time` |
| `ocr_text` | id, note_id, raw_text, char_count | `uk_note_id` |
| `mind_map` / `summary` / `exercise` | note_id + 结构字段 | `idx_note_id` |
| `secondhand_item` | id, seller_id, title, price, condition, trade_place, image_urls, status | `idx_status_time` |
| `purchase_intent` | id, item_id, buyer_id, message, status | `idx_item_id` |
| `lost_found` | id, owner_id, type, item_desc, event_time, event_place, contact, status | `idx_type_status` |
| `claim_request` | id, lf_id, applicant_id, description, status | `idx_lf_id` |
| `club` / `activity` | 展示与名额字段 | `idx_activity_start` |
| `activity_signup` | id, activity_id, user_id, status | `uk_active(activity_id, user_id)` |
| `audit_log` | id, target_type, target_id, result, operator_id, created_at | `idx_target` |
| `operation_log` | id, user_id, action, target, request_id, created_at | `idx_created_at` |

### 6.2 一致性策略

1. **名额扣减**：`UPDATE ... SET joined_count = joined_count + 1 WHERE id = ? AND joined_count < capacity`，受影响行数为 0 即满员（FR-018/040）。
2. **报名幂等**：唯一索引 + `INSERT OR IGNORE`，重复报名返回 `40901`（FR-042）。
3. **笔记状态机**：`ocr_pending → generating → completed | failed`，只允许单向迁移。
4. **重置演示数据**：单事务内按预置快照恢复，保留上传素材文件（FR-047）。

---

## 7. 工程目录结构

```text
kaifa/
├── spec.md                         # 需求规范
├── design.md                       # 本架构设计
├── README.md                       # 启动与演示说明
├── .env.example                    # 环境变量样例（不含真实密钥）
├── .gitignore
├── docs/
│   ├── api.md                      # 接口补充说明
│   └── demo-script.md              # 3 分钟演示脚本
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口、路由注册、中间件
│   │   ├── core/
│   │   │   ├── config.py           # 配置项（模型、OCR、缓存开关）
│   │   │   ├── security.py         # JWT、口令哈希、登录锁定
│   │   │   ├── logging.py          # request_id、结构化日志
│   │   │   ├── errors.py           # 统一异常与业务错误码
│   │   │   └── deps.py             # 鉴权、分页、数据库依赖
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── profile.py
│   │   │       ├── match.py
│   │   │       ├── study.py
│   │   │       ├── life.py
│   │   │       ├── admin.py
│   │   │       └── system.py
│   │   ├── models/                 # SQLAlchemy 模型
│   │   │   ├── user.py
│   │   │   ├── match.py
│   │   │   ├── study.py
│   │   │   ├── life.py
│   │   │   └── audit.py
│   │   ├── schemas/                # Pydantic 请求/响应模型
│   │   │   ├── auth.py
│   │   │   ├── match.py
│   │   │   ├── study.py
│   │   │   └── life.py
│   │   ├── services/
│   │   │   ├── match_service.py    # 规则打分 + 候选过滤
│   │   │   ├── note_service.py     # 笔记状态机与查询
│   │   │   ├── life_service.py     # 二手/失物/活动
│   │   │   ├── ai_gateway.py       # 大模型统一入口
│   │   │   ├── ocr_client.py       # 华为云 OCR 适配
│   │   │   ├── storage.py          # 本地/OBS 存储适配
│   │   │   ├── safety_service.py   # 内容安全过滤
│   │   │   └── cache_replay.py     # 演示缓存回放
│   │   ├── tasks/
│   │   │   └── note_pipeline.py    # OCR→清洗→LLM→落库
│   │   ├── utils/
│   │   │   ├── pdf.py              # PDF 转图
│   │   │   └── text.py             # 清洗、分块、字符统计
│   │   └── static/
│   │       └── cache/              # 演示缓存 JSON
│   ├── tests/
│   │   ├── test_match_service.py
│   │   ├── test_study_signup.py
│   │   └── test_note_pipeline.py
│   ├── uploads/                    # 本地文件目录（.gitignore）
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/index.ts
│   │   ├── stores/
│   │   │   ├── auth.ts
│   │   │   ├── profile.ts
│   │   │   └── match.ts
│   │   ├── api/
│   │   │   ├── http.ts             # Axios 实例与拦截器
│   │   │   ├── auth.ts
│   │   │   ├── match.ts
│   │   │   ├── study.ts
│   │   │   └── life.ts
│   │   ├── views/
│   │   │   ├── HomeView.vue
│   │   │   ├── auth/LoginView.vue
│   │   │   ├── icebreak/ProfileView.vue
│   │   │   ├── icebreak/RecommendView.vue
│   │   │   ├── study/StudyCircleView.vue
│   │   │   ├── study/NoteUploadView.vue
│   │   │   ├── study/NoteDetailView.vue
│   │   │   ├── life/MarketView.vue
│   │   │   ├── life/LostFoundView.vue
│   │   │   ├── life/ActivityView.vue
│   │   │   └── admin/AdminView.vue
│   │   ├── components/
│   │   │   ├── TagSelector.vue
│   │   │   ├── MatchCard.vue
│   │   │   ├── TopicCopy.vue
│   │   │   ├── MindMapTree.vue     # 递归树渲染思维导图
│   │   │   ├── ExerciseList.vue
│   │   │   └── StatusPoller.vue
│   │   ├── styles/
│   │   └── utils/
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
└── deploy/
    ├── nginx.conf
    ├── start-dev.ps1               # 并行启动前后端
    └── seed_demo.py                # 预置演示数据
```

---

## 8. 部署与运行

### 8.1 本地/演示启动（CodeArts IDE）

```text
终端 1（后端）：cd backend && uvicorn app.main:app --reload --port 8000
终端 2（前端）：cd frontend && npm run dev
浏览器：http://localhost:5173
```

### 8.2 生产/演示环境

| 组件 | 方案 |
| --- | --- |
| 前端 | `npm run build` 产物由 Nginx 托管 |
| 后端 | Uvicorn 单进程（可 `--workers 2`） |
| 反向代理 | Nginx：`/api` → `127.0.0.1:8000`，静态资源 gzip |
| 数据 | SQLite 文件挂载持久化；可选 PostgreSQL |
| 文件 | 本地目录或 OBS |
| 健康检查 | `/api/v1/health` 接入探活 |

### 8.3 演示保障

1. `SEED_DEMO=1` 启动时写入预置账号、候选用户、商品、活动。
2. `CACHE_REPLAY=on` 时关键 AI 产出读缓存，现场断网可完整演示。
3. 管理员 `/admin/reset-demo` 一键恢复初始状态。

---

## 9. 非功能落地映射

| NFR | 设计落点 |
| --- | --- |
| NFR-001 首屏 ≤2s | Vite 按路由懒加载、接口分页、首屏只取必要字段 |
| NFR-002 AI 时限 | 网关超时 8s/30s，异步任务 + 轮询 |
| NFR-003 50 并发 | 单进程 + SQLite WAL + 条件更新 |
| NFR-005 持久化 | SQLite 落盘 + 事务 |
| NFR-006 会话安全 | bcrypt + JWT 过期 2h，401 统一拦截 |
| NFR-007 隐私最小化 | 联系方式按关系返回，日志脱敏 |
| NFR-008 内容安全 | SafetyService 双层过滤 |
| NFR-010 可维护性 | request_id 中间件 + 结构化日志 |
| NFR-011 AI 降级 | 主模型→备用→模板，页面标注 |
| NFR-012 演示稳定 | cache_replay 开关 |
| NFR-014 可观测 | /health 返回依赖连通性 |

---

## 10. 实施顺序与风险

### 10.1 实施顺序

| 阶段 | 内容 | 对应里程碑 |
| --- | --- | --- |
| 1 | 工程骨架、配置、数据库、鉴权、健康检查 | M1 |
| 2 | 画像 + 匹配规则 + AI 话题 + 招呼 | M2 |
| 3 | 招募帖 + 报名 + 笔记流水线 | M3 |
| 4 | 二手 + 失物 + 社团活动 + 管理端 | M4 |
| 5 | 缓存回放、降级演练、演示彩排 | M5 |

### 10.2 架构风险

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 模型 JSON 不稳定 | 渲染失败 | Schema 校验 + 修复重试 + 模板 |
| OCR 对拍照件识别差 | 笔记不可用 | 演示用扫描件；失败引导重传 |
| 并发报名超卖 | 数据不一致 | 条件更新 + 唯一索引 |
| 现场网络中断 | AI 不可用 | 缓存回放 + 备用模型 |
| 中文路径/编码 | 上传与日志异常 | 统一 UTF-8，文件路径做安全化处理 |

---

**文档结束**｜版本 v1.0.0｜接口 41 个｜核心 AI 任务 2 条