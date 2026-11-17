# 新声平台前端（Vue 3 + Vite）

轻量化移动优先 Web 前端，覆盖登录注册、兴趣标签、AI 搭子匹配、AI 笔记助手、校园生活广场五大页面。

## 一、环境要求

- Node.js 18 及以上（推荐 20 LTS）
- 后端服务已启动在 `http://127.0.0.1:8000`

> 当前机器暂未检测到 Node.js，如 `npm -v` 报错，请先安装 Node LTS：https://nodejs.org/

## 二、启动步骤

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务

```bash
npm run dev
```

访问 http://localhost:5173

Vite 已配置代理：

- `/api` → `http://127.0.0.1:8000`
- `/uploads` → `http://127.0.0.1:8000`

### 3. 构建与类型检查

```bash
npm run build
npm run typecheck
```

## 三、页面与接口对应

| 页面 | 路由 | 主要接口 |
| --- | --- | --- |
| 登录注册 | `/login` | `POST /auth/register`、`POST /auth/login` |
| 兴趣标签 | `/tags` | `GET /tags`、`PUT /users/me/profile` |
| AI 搭子首页 | `/home` | `GET /match/recommendations`、`POST /match/recommendations/refresh`、`POST /match/greetings` |
| AI 笔记助手 | `/notes` | `POST /study/notes`、`POST /study/notes/{id}/ocr-text`、`POST /study/notes/{id}/parse`、`GET /study/notes` |
| 生活广场 | `/plaza` | `/market/items`、`/lostfound`、`/activities` 列表与发布、活动报名 |

## 四、演示流程（约 2 分钟）

1. 打开 `/login`，注册第一个账号，进入标签页选择 3-10 个兴趣；
2. 另开无痕窗口注册第二个账号，选择有交集的兴趣与互补性格；
3. 回到第一个账号首页，展示匹配分、匹配理由与 3 条破冰话题，点击话题自动复制；
4. 进入笔记页，上传任意图片，使用示例文本点击“生成导图 · 摘要 · 练习题”；
5. 进入广场，发布二手、失物，创建活动并报名。

## 五、目录结构

```text
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
└── src/
    ├── main.ts
    ├── App.vue
    ├── types.ts
    ├── router/index.ts
    ├── stores/auth.ts
    ├── api/
    │   ├── http.ts        # Axios 实例、Token、统一解包
    │   ├── auth.ts
    │   ├── match.ts
    │   ├── study.ts
    │   └── life.ts
    ├── composables/useToast.ts
    ├── components/
    │   ├── AppShell.vue   # 顶栏 + 底部导航
    │   ├── MatchCard.vue  # 匹配卡片 + 话题复制
    │   └── MindMapTree.vue
    ├── views/
    │   ├── LoginView.vue
    │   ├── TagsView.vue
    │   ├── HomeView.vue
    │   ├── NotesView.vue
    │   └── PlazaView.vue
    └── styles/main.css    # 设计系统：配色、卡片、按钮、动画
```

## 六、设计说明

- 风格：Apple Minimalist 骨架 + 青春配色（清透蓝 `#3D7BFF`、薄荷绿 `#2ED3B7`、珊瑚橙 `#FF7A6B`）；
- 布局：移动优先，桌面居中 520px 卡片式呈现，适合投屏演示；
- 交互：卡片渐入、分数环、话题一键复制、底部导航、底部发布面板；
- 零重型 UI 库：全部组件自研，依赖仅 Vue、Vue Router、Pinia、Axios。

## 七、注意事项

- 演示时请先启动后端，否则接口会提示网络异常；
- 后端返回统一结构 `{ code, message, data }`，`http.ts` 已自动解包；
- 登录态存 `localStorage` 的 `xs_token`，退出登录会清除；
- 笔记演示模式可直接使用内置示例文本，无需真实 OCR 服务。