# Milestone 2 数据库与日志追踪验证报告

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

验证日期：2026 年 6 月 4 日

关联 WBS：`M2.9`、`M2.8`、`M2.12`

## 1. 验证目标

本轮用于推进 `M2.9 数据库与日志追踪`：让处理任务不仅记录基础参数，还能回看 Pipeline 阶段、运行日志、配图质量元数据和 PPT 写回版式诊断。

## 2. 后端变更

涉及文件：

- `backend/database.py`
- `backend/services.py`
- `backend/app.py`
- `tests/test_pipeline.py`

数据库表 `processing_jobs` 新增向后兼容字段：

| 字段 | 说明 |
|---|---|
| `chart_theme` | 图表主题 |
| `chart_type` | 语义推荐或覆盖后的图表类型 |
| `chart_image_path` | 图表文件路径 |
| `illustration_image_path` | 配图文件路径 |
| `progress` | Pipeline 完成进度 |
| `intent_json` | 语义意图和版式诊断入口 |
| `chart_spec_json` | 图表生成配置 |
| `illustration_meta_json` | 配图评分、重生成和 fallback 信息 |
| `layout_json` | PPT 写回区域、重叠分数和附加页策略 |
| `logs_json` | Pipeline 运行日志 |
| `stage_history_json` | Pipeline 阶段历史 |

说明：`init_db()` 会自动对旧 SQLite 数据库补列，不需要手工删库。

补充：直接从脚本或测试调用 service 时，如果没有经过 FastAPI `create_app()`，数据库层也会在记录上传、任务和页纲要前自动确保基础表存在，避免冷启动路径出现 `no such table: processing_jobs`。

## 3. API 变更

新增任务详情接口：

```http
GET /api/jobs/{request_id}
```

返回内容包含：

- 基础任务字段
- `intent`
- `chart_spec`
- `illustration_meta`
- `layout`
- `logs`
- `stage_history`
- `chart_image_url`
- `illustration_image_url`
- `final_pptx_url`

## 4. 前端变更

涉及文件：

- `frontend/src/services/api.js`
- `frontend/src/views/LogsView.vue`
- `docs/frontend-user-guide.md`

日志页现在支持：

- 左侧查看最近任务列表。
- 右侧选择任务后自动请求详情。
- 展示配图初始分、最终分、阈值、重生成动作、重生成次数和原因。
- 展示 PPT 写回模式、重叠分数、图片互相重叠值和原页是否保留。
- 展示历史阶段记录和运行日志。

## 5. 验证命令

```bash
./.venv/bin/python -m unittest tests.test_pipeline
cd frontend
npm run build
curl http://127.0.0.1:8000/api/jobs/{request_id}
```

## 6. 验证结果

| 检查项 | 结果 |
|---|---|
| 后端单元测试 | PASS，38 tests OK |
| 任务详情接口测试 | PASS，`/api/jobs/{request_id}` 返回日志、阶段历史和配图元数据 |
| 数据库元数据持久化测试 | PASS，demo 任务可回读 `illustration_meta`、`logs`、`stage_history` |
| 数据库冷启动测试 | PASS，删除测试 DB 后直接调用 `process_demo_text` 可自动建表并回读任务 |
| 前端生产构建 | PASS，39 modules transformed |
| 本地任务详情接口 | PASS，返回 `illustration_meta`、`logs`、`stage_history` 和资源 URL |
| 50 页烟测临时数据库 | PASS，`DATABASE_PATH=/private/tmp/m2-parser-smoke.db` 下 `processed_count=50` |
| 浏览器日志页复验 | PASS，`demo-7cc92626cf` 可在日志页显示，并可打开任务详情 |

本地接口抽样结果：

```text
GET /api/jobs/demo-b085855bc6
status=completed
progress=100
illustration_meta.regenerated=true
illustration_meta.regenerate_action=local_refined_prompt
logs=13
stage_history=5
```

浏览器复验结果：

```text
任务列表：demo-7cc92626cf / completed / local / demo / 第 1 页 · bar · 100%
任务详情：Selected Job、配图评分与重生成、Initial 6.7、Final 6.7、阶段记录、运行日志均可见
截图证据：docs/screenshots/m2-logs-detail.png
移动端复验：demo-1c60f36568 / completed / docs/screenshots/m2-mobile-logs.png
```

补充报告：`docs/milestone2-frontend-browser-validation.md`

## 7. 当前结论

`M2.9` 已具备任务级日志追踪和质量元数据回看能力。SQLite 现在能记录处理任务、阶段历史、运行日志、配图评分与重生成信息，并通过前端日志页查看最近任务详情。

仍待补充：

- 对上传会话和逐页解析记录的长期清理策略。
- 如需多人隔离，需要把任务与用户 ID 绑定并在 API 层做筛选。
