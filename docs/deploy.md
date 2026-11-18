# 【码道新声】公网部署说明（GitHub Pages + 后端托管）

本文档用于把演示站点发布到公网，方便评委在电脑和手机上直接访问，不依赖本机开机。

> **当前方案：腾讯云 CloudBase 云托管**，完整步骤以 `docs/deploy-cloudbase.md` 为准。
> 下文 Render 章节仅作备用记录：Render 免费实例要求绑定海外支付方式验证，当前无法完成。

## 一、部署架构

| 部分 | 托管平台 | 说明 |
| --- | --- | --- |
| 前端（Vue 3 静态站） | GitHub Pages | 由仓库内置工作流自动构建发布 |
| 后端（FastAPI） | Render 免费 Web Service | 读取仓库根目录 `render.yaml` 一键部署 |
| 数据库 | SQLite（容器内临时文件） | 启动时自动建表并写入种子标签 |

约定：

- GitHub 账号：`wwwcy111`，仓库：`https://github.com/wwwcy111/xinsheng`，必须为 **Public**。
- 前端访问地址：`https://wwwcy111.github.io/xinsheng/`
- 后端接口地址：`https://xinsheng-api.onrender.com/api/v1`（若控制台显示带随机后缀，以实际地址为准）

## 二、部署后端（Render）

1. 打开 `https://dashboard.render.com`，选择 **Sign in with GitHub** 登录。
2. 右上角 **New +** → 选择 **Blueprint**。
3. 在仓库列表中选择 `wwwcy111/xinsheng` → 点击 **Connect**。
4. Render 会自动读取 `render.yaml`，确认服务名 `xinsheng-api`、Region 为 **Singapore**、Plan 为 **Free**，点击 **Apply**。
5. 等待构建与首次启动完成（首次约 2-5 分钟），在服务页顶部复制访问地址。
6. 浏览器打开 `https://<服务地址>/api/v1/health`，返回 `{"code":0,"message":"ok",...}` 即为成功。

## 三、对接前端（GitHub Pages）

1. 打开仓库 **Settings → Secrets and variables → Actions → Variables**。
2. 点击 **New repository variable**：
   - Name：`VITE_API_BASE`
   - Value：`https://<服务地址>/api/v1`
3. 打开 **Settings → Pages**，确认 **Build and deployment → Source** 为 **GitHub Actions**。
4. 打开仓库 **Actions** → 选择 `Deploy Frontend to GitHub Pages` → **Run workflow**（分支 `main`）。
5. 等待 `build` 与 `deploy` 两个任务都变绿，访问 `https://wwwcy111.github.io/xinsheng/` 验证。

> 说明：`VITE_API_BASE` 只在构建时注入，修改后必须重新运行一次工作流才会生效。

## 四、验收清单

- [ ] `https://<服务地址>/api/v1/health` 返回 `code = 0`
- [ ] `https://<服务地址>/docs` 可打开接口文档
- [ ] 前端页面可正常打开，浏览器控制台无跨域报错
- [ ] 注册新账号 → 选择兴趣标签 → 进入首页
- [ ] 搭子匹配返回匹配分、理由与 3 条破冰话题
- [ ] 上传笔记图片 → 生成思维导图、摘要、练习题
- [ ] 生活板块可发布二手商品、失物招领、活动报名
- [ ] 手机浏览器访问同一地址，页面布局正常

## 五、免费实例限制与演示注意事项

1. **自动休眠**：Render 免费实例 15 分钟无访问会休眠，再次访问需 30-60 秒唤醒。演示开始前先打开一次 `/api/v1/health` 预热。
2. **数据不持久**：免费实例没有持久磁盘，休眠重启或重新部署后 SQLite 数据会清空。程序启动时自动重建表并写入种子标签，但**已注册账号需重新注册**，建议演示当天提前走一遍注册流程。
3. **上传文件不持久**：`uploads/` 目录同样在临时磁盘，重启后上传的图片会失效，演示时重新上传即可。
4. **密钥固定**：`render.yaml` 中 `SECRET_KEY` 使用固定演示值，保证休眠重启后已登录状态不失效；正式生产环境应改为随机密钥。
5. **构建失败排查**：若提示 Python 版本不可用，把 `PYTHON_VERSION` 改为 `3.12.12` 或删除该项让 Render 使用默认版本；也可在 Render 服务设置中把 Runtime 改为 Docker，仓库已提供 `backend/Dockerfile`。

## 六、常见问题

| 现象 | 原因与处理 |
| --- | --- |
| 页面打开后接口全部失败 | `VITE_API_BASE` 未配置或配置后未重新运行 Actions 工作流 |
| 接口返回 CORS 错误 | 确认 `CORS_ORIGINS` 为 `*`（`render.yaml` 已配置），并在后端服务环境变量页核对 |
| 首页正常、刷新子路由 404 | 工作流中的 `404.html` 回退未生成，检查 `SPA fallback` 步骤是否成功 |
| 首次访问接口很慢或 502 | 免费实例冷启动，等待 30-60 秒后重试 |
| 登录后过一段时间提示未登录 | 实例休眠重启导致数据库重置，重新注册/登录即可 |
| Blueprint 报服务名冲突 | Render 会为服务名追加随机后缀，以控制台实际地址为准并同步更新 `VITE_API_BASE` |

## 七、切换 MySQL（可选）

Render 中新建 PostgreSQL/MySQL 实例或在环境变量中配置：

```ini
DATABASE_URL=mysql+pymysql://用户名:密码@主机:3306/xinsheng?charset=utf8mb4
```

同时在 `backend/requirements.txt` 增加 `pymysql` 依赖并重新部署。建表脚本见 `sql/schema.sql`，字段均带中文注释。