# Milestone 2 前端浏览器验收报告

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

验证日期：2026 年 6 月 4 日

关联 WBS：`M2.8`、`M2.9`、`M2.10`

## 1. 验证目标

本报告用于补齐前端从“构建通过”到“浏览器真实可用”的验收证据，重点检查总工作台、日志界面、个人设置三页是否可访问，以及日志页是否可以读取处理任务和任务详情。

## 2. 验证环境

| 项 | 值 |
|---|---|
| 前端地址 | `http://127.0.0.1:5173/` |
| 后端地址 | `http://127.0.0.1:8000/` |
| 后端数据库 | `/private/tmp/milestone2-browser-screenshots.db` |
| 语义模式 | `ENABLE_QWEN_API=0`，本地规则 |
| 浏览器 | Codex 内置浏览器 |

启动命令：

```bash
DATABASE_PATH=/private/tmp/milestone2-browser-screenshots.db ENABLE_QWEN_API=0 ./.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
cd frontend
npm run dev -- --host 127.0.0.1
```

## 3. 前置接口验证

| 检查项 | 命令 | 结果 |
|---|---|---|
| 后端健康检查 | `curl http://127.0.0.1:8000/api/health` | PASS，`status=ok`，数据库路径为 `/private/tmp/milestone2-browser-screenshots.db` |
| 文本演示任务 | `curl -X POST http://127.0.0.1:8000/api/demo-chart ...` | PASS，生成 `demo-7cc92626cf`，状态 `completed` |
| Vite 代理任务列表 | `curl http://127.0.0.1:5173/api/jobs?limit=30` | PASS，返回 `demo-7cc92626cf` |

文本演示任务使用输入：

```text
营收: 120 成本: 80 利润: 40
```

补充说明：移动端复验另生成 `demo-1c60f36568`，用于 `390 x 844` 视口下的日志页截图。

## 4. 浏览器页面验证

| 页面 | 操作 | 关键可见信号 | 结果 |
|---|---|---|---|
| 登录页 | 打开 `/workspace`，输入测试账号 `m2-screenshot-check` | `登录 SmartChart 工作台`、用户名、密码、`进入工作台` | PASS |
| 总工作台 | 登录后进入工作台 | `生成工作台`、`上传与生成`、`结果主画布`、`图表结果`、`配图结果`、`逐页 PPT 解析`、`调用配置` | PASS |
| 日志界面 | 点击侧边栏 `日志界面`，刷新任务列表 | `demo-7cc92626cf`、`completed`、`local`、`第 1 页 · bar · 100%` | PASS |
| 任务详情 | 点击 `demo-7cc92626cf` 任务卡片 | `Selected Job`、`配图评分与重生成`、`Initial 6.7`、`Final 6.7`、`阶段记录`、`运行日志` | PASS |
| 个人设置 | 点击侧边栏 `个人设置` | `Qwen API Key`、`Qwen 模型`、`WANX API Key`、`FLUX API Key`、`默认语义模式`、`默认配图模型`、`默认配图风格` | PASS |

## 5. 截图证据

| 页面 | 截图 |
|---|---|
| 桌面总工作台 | `docs/screenshots/m2-workspace.png` |
| 桌面日志任务详情 | `docs/screenshots/m2-logs-detail.png` |
| 桌面个人设置 | `docs/screenshots/m2-settings.png` |
| 移动端总工作台 | `docs/screenshots/m2-mobile-workspace.png` |
| 移动端日志任务详情 | `docs/screenshots/m2-mobile-logs.png` |
| 移动端个人设置 | `docs/screenshots/m2-mobile-settings.png` |

桌面截图文件均为 PNG，分辨率 `1280 x 720`；移动端截图文件均为 PNG，分辨率 `390 x 844`。已使用 `file` 和 Pillow 检查文件格式与尺寸。

## 6. 移动端修复与复验

初次移动端截图发现 `390 x 844` 视口下左侧侧边栏会挤压主内容，导致标题和正文被压缩成竖排。已完成以下修复：

- `frontend/src/components/AppShell.vue`：移动端改为顶部导航和用户信息区，桌面端保留左侧栏。
- `frontend/src/views/DashboardView.vue`：移动端收紧页面内边距和标题字号。
- `frontend/src/views/LogsView.vue`：移动端日志列表和任务详情改为上下布局。
- `frontend/src/views/SettingsView.vue`：移动端收紧页面内边距和标题字号。

复验结果：

| 视口 | 页面 | 结果 |
|---|---|---|
| `390 x 844` | 总工作台 | PASS，顶部导航、账号区、生成工作台和上传区可读 |
| `390 x 844` | 日志界面 | PASS，任务卡片和任务详情可读 |
| `390 x 844` | 个人设置 | PASS，Key 输入区和默认配置区可读 |

## 7. 发现与处理

浏览器首次打开日志页时出现 `Failed to fetch`。排查后确认原因不是日志页代码缺陷，而是本地后端与 Vite dev server 在验证过程中先后退出：

- `curl http://127.0.0.1:8000/api/jobs?limit=30` 曾返回 connection refused。
- `curl http://127.0.0.1:5173/api/jobs?limit=30` 曾返回 connection refused。

重新启动后端和前端后，Vite 代理可以正常返回任务列表，浏览器日志页刷新后显示任务卡片；点击任务卡片后，任务详情、配图质量、阶段记录和运行日志均可见。

## 8. 当前结论

`M2.8` 已具备浏览器级可用性证据：总工作台、日志界面、个人设置三页均可访问；日志页可以读取历史任务并展示任务详情；个人设置页可以展示 API key、模型和默认调用配置入口。

`M2.9` 的前端日志读取路径也得到补充验证：`/api/jobs` 和 `/api/jobs/{request_id}` 的数据可以在日志页展示。

桌面端和移动端截图证据已持久化到 `docs/screenshots/`，可直接用于 Milestone 2 汇报材料。
