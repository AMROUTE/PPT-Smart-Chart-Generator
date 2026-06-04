# Milestone 2 前端配图质量字段展示验证报告

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

验证日期：2026 年 6 月 4 日

关联 WBS：`M2.2`、`M2.4`、`M2.8`、`M2.12`

## 1. 验证目标

本轮用于把 `M2.6`、`M2.7` 产生的配图评分与重生成字段接入前端工作台，使用户在生成后可以直接查看质量状态，不必打开原始接口 JSON。

补充目标：接入 `M2.2` 的 PPT 解析诊断字段，让用户在选择处理页之前能识别空页、表格页、图片页和文本页；接入 `M2.4` 的图表推荐解释字段，让用户能看到推荐意图、置信度和命中信号。

## 2. 前端变更

涉及文件：

- `frontend/src/views/DashboardView.vue`
- `frontend/src/components/PipelineStatus.vue`
- `frontend/src/components/SlideOutlinePanel.vue`
- `docs/frontend-user-guide.md`

展示位置：

| 页面区域 | 展示内容 |
|---|---|
| 工作台总览 | 配图质量状态：`待生成`、`通过`、`已重生成`、`待复核` |
| 配图结果卡片 | 初始分、最终分、阈值、分数提升 |
| 配图详情页 | 配图质量门禁、重生成动作、重生成次数、重生成原因 |
| Pipeline 日志与状态页 | 完整 `illustration_meta` 评分和重生成字段 |
| 逐页解析面板 | 页面类型、图片数、占位符数、文本块数、文本推断表格和元素数量 |
| Pipeline 语义区 | 图表推荐意图、推荐置信度、判断依据和命中信号 |

## 3. 接入字段

前端已读取并展示以下后端字段：

- `illustration_meta.clip_score`
- `illustration_meta.initial_clip_score`
- `illustration_meta.score_threshold`
- `illustration_meta.regenerate_hint`
- `illustration_meta.regenerated`
- `illustration_meta.regenerate_attempts`
- `illustration_meta.regenerate_action`
- `illustration_meta.regenerate_reason`

逐页解析面板已读取并展示以下字段：

- `is_empty`
- `picture_count`
- `placeholder_count`
- `diagnostics.table_count`
- `diagnostics.picture_count`
- `diagnostics.placeholder_count`
- `diagnostics.non_empty_text_shape_count`
- `diagnostics.shape_count`
- `diagnostics.has_inferred_table`

Pipeline 语义区已读取并展示以下字段：

- `intent.intent_category`
- `intent.recommendation_confidence`
- `intent.recommendation_signals`
- `intent.reason`

## 4. 验证命令

```bash
cd frontend
npm run build

cd ..
./.venv/bin/python -m unittest tests.test_pipeline
curl http://127.0.0.1:8000/api/health
```

## 5. 验证结果

| 检查项 | 结果 |
|---|---|
| 前端生产构建 | PASS，39 modules transformed |
| 后端单元测试 | PASS，43 tests OK |
| Vite 本地启动 | PASS，`http://127.0.0.1:5173/` |
| 后端健康检查 | PASS，`status=ok`，`database_enabled=true` |
| 浏览器工作台验证 | PASS，登录后可见总工作台、上传与生成、结果主画布、配图质量入口 |
| 浏览器日志页验证 | PASS，可显示 `demo-7cc92626cf` / `demo-1c60f36568` 任务列表与任务详情 |
| 浏览器设置页验证 | PASS，可见 Qwen / WANX / Flux key 输入框和默认调用配置 |
| 前端截图文件 | PASS，`docs/screenshots/m2-workspace.png`、`docs/screenshots/m2-logs-detail.png`、`docs/screenshots/m2-settings.png` |
| 移动端响应式验证 | PASS，`390 x 844` 视口下工作台、日志详情、个人设置均可读 |

补充说明：已通过 Codex 内置浏览器完成工作台、日志页、设置页的桌面与移动端浏览器级检查，详见 `docs/milestone2-frontend-browser-validation.md`。桌面与移动端截图已持久化到 `docs/screenshots/`，文件格式为 PNG。

## 6. 当前结论

`M2.8` 已新增配图质量字段展示能力，并通过前端构建验证。该能力让工作台能直接呈现低分重生成与人工复核依据，支撑 `M2.7` 的验收证据闭环。

逐页解析面板也已接入 `M2.2` 诊断字段，用户可以在上传 PPT 后直接判断每页的处理价值，减少误选空页或纯图片页。Pipeline 语义区已接入 `M2.4` 推荐解释字段，可显示推荐意图、置信度和命中信号。

仍待补充：

- 更大范围的平板断点视觉检查。

已在 `docs/milestone2-database-log-trace-report.md` 中补齐历史任务详情：后端已持久化 `illustration_meta`，并新增 `/api/jobs/{request_id}` 任务详情接口；日志页可回看历史任务的配图质量字段。
