# Milestone 2 WBS 验收清单

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

依据文档：`/Users/mac/Downloads/WBS 语义驱动的 PPT 智能图表生成与多模态配图系统 .docx`

编制日期：2026 年 6 月 3 日

## 1. Milestone 2 总目标

Milestone 2 按原始 WBS 编号 `M2.1` 至 `M2.12` 推进，核心目标是把系统从“可演示原型”推进到“可稳定验收版本”。本阶段优先围绕 PPT 解析、PPT 写回、图表推荐、配图质量、任务追踪、评测体系、部署验证和汇报材料做质量收敛，不另起新的任务路线。

## 2. 验收标准

### 2.1 主流程稳定性

- 上传 `.pptx` 后，可以完成解析、图表生成、配图生成、写回和下载。
- 文本演示模式可以在无 PPT 输入时生成图表、配图预览、日志和阶段状态。
- 外部模型失败时，系统可以自动回退到本地规则或本地配图预览，不中断流程。

### 2.2 PPT 处理效果

- 至少 10 份真实 PPT 样例完成测试。
- 至少 30 页真实 PPT 页面完成解析和预览验证。
- 图表和配图可以正确写入目标页，不出现明显遮挡或错位。

### 2.3 图表与配图质量

- 图表推荐准确率在小批量测试集中达到 85% 左右。
- 配图主题不再包含图表、坐标轴、数据看板等错误视觉元素。
- 至少形成 3 类行业风格配图样例，如商务、教育、科技或医疗。

### 2.4 前端与部署

- 前端完成总工作台、日志界面、个人设置三页面结构。
- 个人 API key 和模型设置可影响实际调用。
- 本地部署和 Docker Compose 部署流程可复现，README 保持同步。

## 3. 状态枚举

后续更新本清单时，`当前状态` 只能使用以下四种状态：

- `未开始`
- `进行中`
- `待验证`
- `已完成`

## 4. WBS 工作包清单

| WBS 编号 | 工作包 | 负责人 | 计划工时 | 任务内容 | 完成标准 | 证据位置 | 当前状态 |
|---|---|---|---:|---|---|---|---|
| M2.1 | 问题收敛与验收标准确认 | 阿曼卓勒 | 6 | 梳理当前问题；明确 Milestone 2 验收指标；冻结主流程范围；确定测试样例标准。 | 形成统一验收清单；所有后续任务均可映射到 WBS；主流程范围不再随意扩张。 | `docs/milestone2-wbs-checklist.md`、`docs/milestone2-baseline-verification.md`、`docs/milestone2-action-plan.md`、`docs/next-milestone-action-plan-rbs-wbs.md` | 已完成 |
| M2.2 | PPT 解析增强 | 许君达 | 12 | 增强复杂表格解析；改进文本型数据识别；处理空页、图片占位、复杂多栏文本等边界场景。 | 真实 PPT 样例中标题、正文、表格数量、文本型数据和页面元素信息可被稳定提取；异常页面不导致流程中断。 | `backend/ppt_parser.py`、`frontend/src/components/SlideOutlinePanel.vue`、`tests/test_pipeline.py`、`docs/milestone2-ppt-parser-enhancement-report.md`、`docs/milestone2-real-ppt-sample-register.md`、`docs/milestone2-real-ppt-smoke-report.md`、`docs/milestone2-real-ppt-multipage-smoke-report.md`、`docs/milestone2-baseline-verification.md`、`docs/milestone2-test-report.md`、`docs/week5-8-task-audit.md` | 待验证 |
| M2.3 | PPT 写回与版式优化 | 许君达 | 10 | 优化图表和配图插入位置；支持替换原表格区域；提升增强版 PPT 的可用性和美观度。 | 增强版 PPT 中图表和配图写入目标页；不明显遮挡原有核心内容；多页批量输出写回到同一个增强版 PPT。 | `backend/insert_to_pptx.py`、`tests/test_pipeline.py`、`tools/run_m2_layout_prefill.py`、`docs/milestone2-ppt-layout-qa-report.md`、`docs/milestone2-layout-prefill-report.md`、`docs/milestone2-real-ppt-sample-register.md`、`docs/milestone2-real-ppt-smoke-report.md`、`docs/milestone2-real-ppt-multipage-smoke-report.md`、`outputs/week7_50_slide_smoke_source_batch_enhanced.pptx`、`docs/milestone2-baseline-verification.md`、`docs/milestone2-test-report.md` | 进行中 |
| M2.4 | 图表推荐质量提升 | 吴昀洁 / 阿曼卓勒 | 14 | 优化本地规则；完善千问 Prompt；补充图表推荐解释；提高趋势、占比、相关性等场景判断准确率。 | 小批量测试中图表推荐准确率达到 85% 左右；趋势、对比、构成、分布、相关性五类意图均有覆盖。 | `backend/pipeline.py`、`frontend/src/components/PipelineStatus.vue`、`tests/test_pipeline.py`、`evaluator.py`、`outputs/evaluation_summary.md`、`outputs/evaluation_report.csv`、`docs/milestone2-chart-recommendation-report.md`、`docs/milestone2-baseline-verification.md`、`docs/final-prompt-template.md` | 待验证 |
| M2.5 | 图表生成稳定性优化 | 阿曼卓勒 | 8 | 完善多图表类型生成；处理异常数据、缺失值和无数据场景；提升图表输出一致性。 | `bar`、`line`、`pie`、`scatter`、`area`、`histogram`、`box`、`heatmap` 生成路径稳定；异常数据有 fallback；输出 PNG 可被前端展示和 PPT 写回。 | `backend/chart_generator.py`、`tests/test_pipeline.py`、`docs/milestone2-chart-stability-report.md`、`docs/milestone2-baseline-verification.md`、`docs/milestone2-test-report.md` | 待验证 |
| M2.6 | 配图生成质量优化 | 陈奕炫 | 14 | 调整配图 Prompt；完善通义万相 / Flux 调用；补充行业风格模板；避免生成图表元素。 | 本地、WANX、Flux 三类配图模型入口可配置；外部模型不可用时自动回退；商务、教育、科技、医疗等风格模板有明确提示词。 | `backend/image_clients.py`、`backend/pipeline.py`、`tests/test_pipeline.py`、`docs/prompt-engineering-notes.md`、`docs/final-prompt-template.md`、`docs/milestone2-image-quality-regeneration-report.md`、`docs/milestone2-test-report.md` | 待验证 |
| M2.7 | 配图评分与重生成 | 陈奕炫 | 10 | 增加配图质量评分字段；设计低分重生成策略；整理配图质量对比样例。 | Pipeline 输出配图评分或代理分数字段；低分结果有重生成或人工重试依据；报告中包含配图质量对比说明。 | `backend/pipeline.py`、`tests/test_pipeline.py`、`docs/milestone2-image-quality-regeneration-report.md`、`docs/milestone2-baseline-verification.md`、`docs/milestone2-test-report.md`、`outputs/evaluation_summary.md` | 待验证 |
| M2.8 | 前端工作台优化 | 阿曼卓勒 | 12 | 优化总工作台、日志界面、个人设置界面；完善 API key、模型选择和错误提示交互。 | 工作台、日志页、设置页可访问；API key、语义模式、配图模型和配图风格配置可影响请求；错误提示可被用户理解。 | `frontend/src/`、`frontend/src/views/DashboardView.vue`、`frontend/src/components/PipelineStatus.vue`、`frontend/src/components/SlideOutlinePanel.vue`、`frontend/src/views/LogsView.vue`、`docs/milestone2-frontend-quality-fields-report.md`、`docs/milestone2-frontend-browser-validation.md`、`docs/screenshots/m2-workspace.png`、`docs/screenshots/m2-logs-detail.png`、`docs/screenshots/m2-settings.png`、`docs/screenshots/m2-mobile-workspace.png`、`docs/screenshots/m2-mobile-logs.png`、`docs/screenshots/m2-mobile-settings.png`、`docs/milestone2-database-log-trace-report.md`、`docs/milestone2-baseline-verification.md`、`docs/frontend-user-guide.md`、`README.md` | 待验证 |
| M2.9 | 数据库与日志追踪 | 阿曼卓勒 | 10 | 完善用户、上传会话、处理任务、逐页解析记录；支持日志界面查看历史任务。 | SQLite 能记录用户、上传会话、处理任务和逐页解析记录；前端日志页能读取最近任务；数据库路径可通过环境变量配置。 | `backend/database.py`、`backend/services.py`、`backend/app.py`、`frontend/src/views/LogsView.vue`、`tests/test_pipeline.py`、`docs/milestone2-database-log-trace-report.md`、`docs/milestone2-baseline-verification.md`、`docs/frontend-user-guide.md` | 待验证 |
| M2.10 | 测试样例与评测体系 | 吴昀洁 / 全体 | 16 | 建立至少 10 份真实 PPT 小批量测试集；统计图表推荐准确率、配图匹配度和端到端成功率。 | 评估脚本、50 页烟测、后端单测、前端构建均形成结果；真实 PPT 测试样例和人工评分表可用于 Milestone 2 汇报。 | `evaluator.py`、`tools/run_50_slide_smoke.py`、`tools/run_m2_layout_prefill.py`、`docs/milestone2-chart-stability-report.md`、`docs/milestone2-real-ppt-sample-register.md`、`docs/milestone2-real-ppt-smoke-report.md`、`docs/milestone2-real-ppt-multipage-smoke-report.md`、`docs/milestone2-layout-prefill-report.md`、`docs/milestone2-frontend-browser-validation.md`、`docs/screenshots/`、`docs/milestone2-manual-review-scorecard.md`、`docs/milestone2-baseline-verification.md`、`docs/milestone2-test-report.md`、`docs/week5-8-task-audit.md` | 待验证 |
| M2.11 | 部署与环境验证 | 阿曼卓勒 / 全体 | 8 | 验证 Docker 启动；检查环境变量、静态资源代理、模型 key 配置和数据库路径。 | 本地部署和 Docker Compose 均可启动；`/api/health` 返回模型配置状态；前端 `/api` 和 `/assets` 代理正常。 | `README.md`、`docker-compose.yml`、`Dockerfile.backend`、`frontend/Dockerfile`、`docs/milestone2-docker-validation.md`、`docs/milestone2-baseline-verification.md` | 进行中 |
| M2.12 | 文档与汇报材料 | 全体 | 8 | 更新 README、接口说明、Prompt 工程说明、Milestone 2 汇报材料和演示脚本。 | README、前端使用说明、Prompt 文档、测试报告、WBS 验收清单和汇报材料一致；演示脚本能覆盖主流程和 fallback 场景。 | `README.md`、`docs/milestone2-wbs-checklist.md`、`docs/milestone2-baseline-verification.md`、`docs/frontend-user-guide.md`、`docs/final-prompt-template.md`、`docs/prompt-engineering-notes.md`、`docs/milestone2-api-reference.md`、`docs/milestone2-image-quality-regeneration-report.md`、`docs/milestone2-frontend-quality-fields-report.md`、`docs/milestone2-database-log-trace-report.md`、`docs/milestone2-test-report.md`、`docs/milestone2-demo-script.md`、`docs/milestone2-manual-review-scorecard.md` | 进行中 |

## 5. 主要验证命令

后续执行 WBS 验收时，优先使用以下命令作为证据来源：

```bash
python -m unittest tests.test_pipeline
python evaluator.py
python tools/run_50_slide_smoke.py
cd frontend
npm run build
docker compose up -d --build
curl http://127.0.0.1:8000/api/health
```

说明：如果使用虚拟环境，应将 `python` 替换为当前环境对应的解释器，例如 `./.venv/bin/python`。

## 6. 更新规则

- 每完成一个工作包，先补充证据位置，再将状态更新为 `待验证`。
- 只有测试命令、截图、输出文件、报告或人工验收记录齐全后，才能将状态更新为 `已完成`。
- 不修改 WBS 编号、负责人和计划工时；如果任务范围发生变化，应新增备注，不覆盖原始 WBS。
- 后续开发、测试和汇报均以本清单为统一入口。
