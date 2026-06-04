# Milestone 2 汇报演示脚本

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

适用场景：Milestone 2 阶段汇报、导师检查、组内验收复盘

预计时长：8-12 分钟

## 1. 演示目标

本脚本用于证明系统已经从“可演示原型”推进到“可稳定验收版本”的阶段状态，重点覆盖：

- PPT 上传、解析、预览、逐页诊断。
- 图表推荐、图表生成、配图生成、增强版 PPT 下载。
- 文本演示模式。
- 配图低分重生成和外部模型不可用 fallback。
- 日志与历史任务回看。
- 当前测试证据和仍待补齐的阻塞项。

## 2. 演示前准备

### 2.1 启动后端

推荐离线演示配置：

```bash
ENABLE_QWEN_API=0 ./.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

验收点：

```bash
curl http://127.0.0.1:8000/api/health
```

预期结果：

- `status=ok`
- `database_enabled=true`
- `semantic_modes` 包含 `local` 和 `qwen`
- `image_models` 包含 `local`、`flux`、`wanx`

说明：离线演示时 `qwen_enabled=false` 是可接受状态，用于证明本地规则 fallback 不依赖外部 API。

### 2.2 启动前端

```bash
cd frontend
npm run dev -- --host 127.0.0.1
```

默认访问：

```text
http://127.0.0.1:5173/
```

### 2.3 准备样例

优先使用真实样例登记表中的 PPT：

- `docs/milestone2-real-ppt-sample-register.md`
- 推荐演示样例：`/Users/mac/Downloads/24w3407组汇报ppt.pptx`
- 备选样例：`/Users/mac/Downloads/HCI项目报道 (4).pptx`

如果需要快速无文件演示，可使用文本演示模式：

```text
营收: 120
成本: 80
利润: 40
```

## 3. 演示流程

### 3.1 开场说明

建议讲法：

```text
Milestone 2 我们没有另起路线，而是按原 Word WBS 的 M2.1 到 M2.12 推进。
当前系统重点补齐了 PPT 解析、写回版式、图表推荐解释、配图评分重生成、日志追踪、前端工作台和测试报告。
```

展示材料：

- `docs/milestone2-wbs-checklist.md`
- `docs/milestone2-test-report.md`

### 3.2 PPT 上传与逐页解析

操作：

1. 登录工作台。
2. 上传真实 PPT。
3. 等待第一页预览加载。
4. 切换到“逐页解析”面板。

讲解点：

- 每页会展示 `空页 / 表格页 / 图片页 / 文本页 / 待复核`。
- 页面诊断包括表格数、图片数、文本块数、占位符和元素数。
- 这对应 `M2.2 PPT 解析增强`。

验收证据：

- `backend/ppt_parser.py`
- `frontend/src/components/SlideOutlinePanel.vue`
- `docs/milestone2-ppt-parser-enhancement-report.md`

### 3.3 单页图表与配图生成

操作：

1. 选择含表格或文本数据的页面。
2. 语义模式选择 `local`。
3. 图表类型选择 `Auto`。
4. 图表主题选择 `Business` 或 `Tech`。
5. 配图模型选择 `Local Preview`。
6. 点击生成。

讲解点：

- Pipeline 会完成解析、语义推荐、图表生成、配图生成和 PPT 写回。
- Pipeline 状态页会显示推荐图表、语义意图、推荐置信度和判断依据。
- 配图页会显示初始分、最终分、阈值、重生成动作和重生成原因。

验收证据：

- `backend/pipeline.py`
- `backend/chart_generator.py`
- `backend/insert_to_pptx.py`
- `frontend/src/components/PipelineStatus.vue`
- `docs/milestone2-chart-recommendation-report.md`
- `docs/milestone2-image-quality-regeneration-report.md`

### 3.4 下载增强版 PPT

操作：

1. 生成完成后点击增强版 PPT 下载入口。
2. 打开输出文件。
3. 检查图表、配图和原始内容关系。

讲解点：

- 表格区域优先替换为图表。
- 密集页面会保留原始页，并追加结果页，降低遮挡风险。
- 当前自动版式 QA 已通过，但人工视觉验收仍需继续填写评分表。

验收证据：

- `docs/milestone2-ppt-layout-qa-report.md`
- `docs/milestone2-manual-review-scorecard.md`

### 3.5 文本演示模式

操作：

1. 切换到文本演示模式。
2. 输入：

```text
广告投入越高，销售额通常越高。
```

3. 图表类型保持 `Auto`。
4. 点击生成。

讲解点：

- 系统应识别为相关性场景。
- 推荐图表应偏向 `scatter`。
- 无 PPT 输入时也能生成图表、配图、日志和阶段状态。

验收证据：

- `evaluator.py`
- `outputs/evaluation_summary.md`
- `docs/milestone2-chart-recommendation-report.md`

### 3.6 Fallback 场景演示

推荐演示方式一：外部语义模型 fallback。

操作：

1. 后端使用 `ENABLE_QWEN_API=0` 启动。
2. 工作台语义模式选择 `Qwen`。
3. 运行文本演示或 PPT 单页生成。

预期讲解：

```text
当前环境没有启用 Qwen，因此系统会回退到本地语义规则。
这证明外部模型不可用时主流程不会中断。
```

推荐演示方式二：外部配图模型 fallback。

操作：

1. 配图模型选择 `Wanx` 或 `Flux`。
2. 不配置真实 API key。
3. 运行生成。

预期讲解：

```text
外部配图模型不可用时，系统会回退到 Local Preview，并保留 generation_warning。
```

验收证据：

- `tests/test_pipeline.py`
- `docs/milestone2-test-report.md`
- `docs/frontend-user-guide.md`

### 3.7 日志与历史任务

操作：

1. 打开日志页。
2. 选择最近任务。
3. 查看任务详情。

讲解点：

- 任务详情包含阶段历史、运行日志、配图评分、版式诊断和资源 URL。
- 这对应 `M2.9 数据库与日志追踪`。

验收证据：

- `backend/database.py`
- `backend/app.py`
- `frontend/src/views/LogsView.vue`
- `docs/milestone2-database-log-trace-report.md`

## 4. 演示中的关键数字

| 指标 | 当前结果 | 证据 |
|---|---:|---|
| 后端单测 | 39 tests OK | `docs/milestone2-test-report.md` |
| 语义评估样本 | 60 | `outputs/evaluation_summary.md` |
| 语义准确率 | 100.00% | `outputs/evaluation_summary.md` |
| 平均 CLIP 代理分数 | 7.02 | `outputs/evaluation_summary.md` |
| 50 页烟测 | 50/50 PASS | `outputs/week7_50_slide_smoke_summary.json` |
| 真实 PPT 样例 | 10 份 / 173 页 | `docs/milestone2-real-ppt-sample-register.md` |

## 5. 当前限制说明

汇报时应主动说明：

- Docker CLI 和 Compose 配置可用，但 Docker daemon/socket 当前不可访问，容器实际启动尚未完成。
- Qwen、WANX、Flux 的真实外部模型路径需要在具备 API key 和网络环境后补测。
- 浏览器截图级前端视觉验收尚未闭环。
- 增强版 PPT 的人工版式评分仍需填写 `docs/milestone2-manual-review-scorecard.md`。

## 6. 收尾话术

建议讲法：

```text
目前 Milestone 2 已经形成自动化测试、真实 PPT smoke、统一测试报告和 WBS 验收清单。
系统主流程可以本地稳定跑通，并具备外部模型不可用时的 fallback。
剩余工作主要是 Docker daemon 环境补验证、外部模型真实调用、浏览器截图级验收和人工版式评分。
```
