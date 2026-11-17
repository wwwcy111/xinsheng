# 新声平台后端（FastAPI）

面向大一新生的“破冰·学业·生活”全能赋能平台后端，基于 FastAPI + SQLAlchemy，
默认 SQLite 零配置启动，可切换 MySQL；华为云大模型调用已预留统一入口。

## 一、环境要求

- Python 3.10 及以上（推荐 3.11/3.13）
- 无需安装 MySQL（演示默认 SQLite）

## 二、启动步骤

### 1. 进入后端目录并创建虚拟环境

```bash
cd backend
python -m venv .venv
```

Windows 激活：

```bash
.venv\Scripts\activate
```

macOS/Linux 激活：

```bash
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量（可选）

```bash
copy .env.example .env
```

不创建 `.env` 也能启动，默认使用 SQLite 与本地模板兜底。

### 4. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

或：

```bash
python run.py
```

启动后访问：

- 接口文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/v1/health

## 三、接口清单

| 模块 | 方法与路径 | 说明 |
| --- | --- | --- |
| 认证 | POST `/api/v1/auth/register` | 注册，可同时录入标签与性格 |
| 认证 | POST `/api/v1/auth/login` | 登录，返回 JWT |
| 画像 | GET `/api/v1/users/me` | 当前用户与标签 |
| 画像 | PUT `/api/v1/users/me/profile` | 更新标签、性格、社交偏好 |
| 标签 | GET `/api/v1/tags` | 预置兴趣标签列表 |
| 匹配 | GET `/api/v1/match/recommendations` | 当日搭子推荐（含话题） |
| 匹配 | POST `/api/v1/match/recommendations/refresh` | 换一批 |
| 匹配 | GET `/api/v1/match/recommendations/{id}/topics` | 获取破冰话题 |
| 匹配 | POST `/api/v1/match/greetings` | 发送招呼 |
| 笔记 | POST `/api/v1/study/notes` | 上传笔记（jpg/png/webp/pdf） |
| 笔记 | POST `/api/v1/study/notes/{id}/ocr-text` | 写入 OCR 文本（演示用） |
| 笔记 | POST `/api/v1/study/notes/{id}/parse` | 生成导图/摘要/练习题 |
| 笔记 | GET `/api/v1/study/notes/{id}/status` | 轮询处理状态 |
| 二手 | GET/POST `/api/v1/market/items` | 列表/发布 |
| 二手 | GET `/api/v1/market/items/{id}` | 详情 |
| 二手 | PATCH `/api/v1/market/items/{id}/status` | 更新状态 |
| 失物 | GET/POST `/api/v1/lostfound` | 列表/发布 |
| 失物 | PATCH `/api/v1/lostfound/{id}/status` | 更新状态 |
| 活动 | GET/POST `/api/v1/activities` | 列表/创建 |
| 活动 | POST `/api/v1/activities/{id}/signup` | 报名（名额条件扣减） |

## 四、3 分钟 Demo 建议流程

1. 注册两个账号，分别选择 3-10 个兴趣标签；
2. 账号 A 调用 `GET /match/recommendations`，展示匹配分、理由、3 条破冰话题；
3. 上传一张笔记图片，调用 `POST /study/notes/{id}/parse`，展示导图、摘要、练习题；
4. 发布二手商品与失物招领，创建活动并报名；
5. 打开 `/docs` 展示完整接口契约。

## 五、接入华为云大模型

编辑 `.env`：

```ini
AI_ENABLED=true
AI_BASE_URL=https://你的ModelArts服务地址/v1
AI_API_KEY=你的密钥
AI_MODEL=pangu
```

两个核心 Prompt 的完整内容位于 `app/services/ai_gateway.py` 顶部注释：

1. 搭子匹配：生成匹配理由与 3 条破冰话题；
2. 笔记解析：生成思维导图、知识点摘要与复习练习题。

未配置 AI 或调用失败时，平台自动使用本地模板兜底，不影响演示流程。

## 六、切换 MySQL

```ini
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/xinsheng?charset=utf8mb4
```

并安装驱动：

```bash
pip install pymysql
```

建表脚本见项目根目录 `sql/schema.sql`。演示环境也可由程序自动建表。

## 七、目录说明

```text
backend/
├── app/
│   ├── main.py              # 应用入口
│   ├── seed.py              # 预置标签
│   ├── core/                # 配置、数据库、安全、依赖
│   ├── models/              # ORM 模型
│   ├── schemas/             # 请求/响应模型
│   ├── services/            # 匹配、笔记、AI 网关
│   └── api/v1/              # 业务接口
├── requirements.txt
├── .env.example
└── run.py
```