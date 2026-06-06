# Milestone 2 测试与评测统一报告

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

验证日期：2026 年 6 月 6 日

关联 WBS：`M2.2`、`M2.3`、`M2.4`、`M2.5`、`M2.7`、`M2.8`、`M2.9`、`M2.10`、`M2.11`、`M2.12`

## 1. 报告目标

本报告作为 Milestone 2 当前测试证据的统一入口，汇总后端单测、语义评估、50 页烟测、前端构建、后端健康检查和 Docker 部署验证状态。后续 WBS 更新、汇报材料和验收复核优先引用本报告，再跳转到各专项报告。

## 2. 当前测试结论

| 验证项 | 命令 | 当前结果 | 状态 | 关联 WBS |
|---|---|---|---|---|
| 后端单元测试 | `./.venv/bin/python -m unittest tests.test_pipeline` | `Ran 58 tests in 1.208s`，`OK` | PASS | `M2.2`、`M2.3`、`M2.5`、`M2.6`、`M2.7`、`M2.8`、`M2.9`、`M2.10` |
| 语义识别评估 | `./.venv/bin/python evaluator.py` | 60/60，准确率 100.00%，平均 CLIP 7.02 | PASS | `M2.4`、`M2.10` |
| 50 页批量烟测 | `DATABASE_PATH=/private/tmp/m2-test-report-smoke.db ./.venv/bin/python tools/run_50_slide_smoke.py` | 50/50，增强版 PPT 生成成功，平均 CLIP 6.7 | PASS | `M2.2`、`M2.3`、`M2.5`、`M2.10` |
| 真实 PPT 版式预复核 | `./.venv/bin/python tools/run_m2_layout_prefill.py` | 10/10 份 PASS，处理页新增资产达到预期，附加页未发现越界或图片间重叠 | PASS | `M2.3`、`M2.10` |
| M2 测试 PPT 问题回归 | `DATABASE_PATH=/private/tmp/m2-dev-verified-issues.db ./.venv/bin/python -c "... process_ppt_batch(...)"` | 第 2-12 页批量处理：10 页成功、0 页失败、1 页空页跳过；第 8、9 页保留原页并追加结果页；人工复核确认修完的 PPT 无问题 | PASS | `M2.2`、`M2.3`、`M2.8`、`M2.10` |
| 前端生产构建 | `cd frontend && npm run build` | 39 modules transformed，built in 610ms | PASS | `M2.8`、`M2.10` |
| 图表/配图质量升级 demo | `DATABASE_PATH=/private/tmp/m2-quality-upgrade.db ./.venv/bin/python - <<'PY' ...` | 图表质量 9.42/10，配图质量 7.25/10，负向 prompt 和评分组件可回读 | PASS | `M2.5`、`M2.6`、`M2.7`、`M2.10` |
| 图表/配图质量样例 Gallery | `DATABASE_PATH=/private/tmp/m2-quality-gallery.db ./.venv/bin/python tools/run_m2_quality_gallery.py` | 10/10 PASS，图表和配图样例 PNG、contact sheet、报告已生成；尺寸、KB、颜色数 sanity check 通过 | PASS | `M2.5`、`M2.6`、`M2.7`、`M2.10` |
| 图表多样性回归 | `DATABASE_PATH=/private/tmp/m2-chart-diversity.db ./.venv/bin/python tools/run_m2_chart_diversity.py` | 5/5 PASS，趋势、构成、对比、相关、分布五类意图分别生成 line、pie、bar、scatter、histogram | PASS | `M2.4`、`M2.5`、`M2.10` |
| 插图多样性回归 | `DATABASE_PATH=/private/tmp/m2-illustration-diversity.db ./.venv/bin/python tools/run_m2_illustration_diversity.py` | 4/4 PASS，增长、区域、产品、营销四类商务页主题特征不同，构图变体达到 4 类 | PASS | `M2.6`、`M2.7`、`M2.10` |
| 前端浏览器验收 | Codex 内置浏览器 + `curl http://127.0.0.1:5173/api/jobs?limit=30` | 工作台、日志页、任务详情、设置页均可访问；日志页可展示 `demo-1c60f36568`；桌面和移动端 PNG 截图已落盘 | PASS | `M2.8`、`M2.9`、`M2.10` |
| 后端健康检查 | `curl http://127.0.0.1:8000/api/health` | `status=ok`，SQLite 可读，功能列表可读 | PASS | `M2.9`、`M2.11` |
| Docker Compose 解析 | `docker compose config` | 配置可解析 | PASS | `M2.11` |
| Docker Compose 启动 | `PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH" docker compose up -d --build` | Docker Hub 基础拉取可用，前端镜像构建成功；后端镜像在 Debian apt 下载阶段 EOF | BLOCKED | `M2.11` |

## 3. 详细结果

### 3.1 后端单元测试

命令：

```bash
./.venv/bin/python -m unittest tests.test_pipeline
```

结果：

```text
Ran 58 tests in 1.208s
OK
```

覆盖范围包括：

- Pipeline 主流程阶段。
- PPT 解析、空页、图片页、多文本块阅读顺序。
- PPT 写回与版式避让。
- 批量空页跳过、原页 shapes 参与写回避让，以及密集文本 / 图片页追加结果页回归。
- 批量手动布局写回接口与 `manual_override` 布局元数据。
- 8 类图表生成、异常数据 fallback、质量分数、质量门禁、轴刻度、值标签、负值零基线和饼图 Other 聚合。
- 文本演示模式保留年份、区间标签和重复双指标数据，相关性样例使用真实双轴 scatter。
- WANX / Flux 配图客户端缺 key、WANX 下载、FLUX 直返和轮询解析。
- 配图评分、评分组件、负向 prompt、行业风格本地预览特征、内容感知插图主题与低分重生成。
- 数据库冷启动、任务元数据持久化和任务详情接口。
- 五类图表推荐意图：对比、趋势、构成、分布、相关性。

说明：运行时出现 `urllib3` 的 LibreSSL 版本警告，不影响测试通过。

### 3.2 语义识别与推荐评估

命令：

```bash
./.venv/bin/python evaluator.py
```

结果：

```text
总样本数：60
预测正确：60
准确率：100.00%（目标 >= 88%）
平均 CLIP 匹配分数：7.02（目标 >= 6.5）
平均单样本耗时：0.01 ms
PASS
```

输出文件：

- `outputs/evaluation_report.csv`
- `outputs/evaluation_summary.json`
- `outputs/evaluation_summary.md`

说明：本次 evaluator 自动回退到 local 引擎，原因是 LLM parser 依赖导入失败：`cannot import name 'masked' from 'numpy.ma'`。本地兜底规则达到当前验收目标；Qwen 真实调用路径仍需在完整外部模型环境下追加验证。

### 3.3 50 页批量烟测

命令：

```bash
DATABASE_PATH=/private/tmp/m2-test-report-smoke.db ./.venv/bin/python tools/run_50_slide_smoke.py
```

结果：

```json
{
  "source_ppt": "outputs/week7_50_slide_smoke_source.pptx",
  "final_pptx_path": "outputs/week7_50_slide_smoke_source_batch_enhanced.pptx",
  "requested_slides": 50,
  "processed_count": 50,
  "completed_count": 50,
  "final_pptx_exists": true,
  "average_clip_score": 6.7,
  "elapsed_seconds": 3.52,
  "pass": true
}
```

说明：本次烟测使用临时数据库路径，避免修改仓库内 `data/app.db`。该结果验证批量处理、图表生成、配图生成、PPT 写回和数据库冷启动路径可以一起工作。

### 3.4 真实 PPT 版式预复核

命令：

```bash
./.venv/bin/python tools/run_m2_layout_prefill.py
```

结果：

```text
10 份批量增强版 PPT 均可被 python-pptx 打开。
按“处理页新增资产 + 附加结果页图片”的口径，10/10 份达到 3 个代表页所需的 6 张新增资产。
附加结果页中的图片未发现越界或图片间重叠。
PASS
```

输出文件：

- `docs/milestone2-layout-prefill-report.md`

说明：该检查是结构化预复核，覆盖 10 份真实 PPT、每份 3 个代表页。它可以证明增强版 PPT 可打开、处理页资产数量符合预期、附加页图片在边界内且不互相重叠；但不能替代人工打开 PPT 或渲染截图级视觉验收。

### 3.4.1 M2 测试 PPT 问题回归

背景：2026 年 6 月 6 日使用 `tools/create_m2_test_ppt.py` 生成 12 页 Milestone 2 测试 PPT，并对前一次人工验收发现的问题进行回归：

- 第 8 页复杂文本页，生成资产不应覆盖原始文本卡片。
- 第 9 页图片页，生成资产不应覆盖原始主图片。
- 第 12 页空白页，不应强行生成图表和配图。
- 批量逐页预览应能看到原 PPT 页底图，便于判断遮挡并手动微调。

验证命令：

```bash
./.venv/bin/python tools/create_m2_test_ppt.py
DATABASE_PATH=/private/tmp/m2-dev-verified-issues.db PYTHONPYCACHEPREFIX=/private/tmp/ppt-smart-chart-pycache ./.venv/bin/python -c "... process_ppt_batch('outputs/milestone2_manual_test_input.pptx', slide_start=2, slide_end=12, image_model='local') ..."
```

结果摘要：

```text
message Batch pipeline completed with skipped slides.
success 10 failed 0 skipped 1
第 8 页：appendix，original_slide_preserved=True
第 9 页：appendix，original_slide_preserved=True
第 12 页：skipped，Empty slide skipped.
final_slides 15
```

输出文件：

- `outputs/milestone2_manual_test_input.pptx`
- `outputs/milestone2_manual_test_input_batch-6ac17a1f0e_batch_enhanced.pptx`

人工复核结论：用户已确认修完的 PPT 没有问题。本轮修复后，空页跳过、图片页避让、复杂文本页保留原页和批量预览原稿底图均通过回归。

### 3.5 前端生产构建

命令：

```bash
cd frontend
npm run build
```

结果：

```text
vite v5.4.21 building for production...
39 modules transformed
built in 442ms
```

说明：工作台、日志页、设置页、逐页解析诊断、配图质量字段和图表推荐解释展示均通过构建检查。

### 3.6 前端浏览器验收

验证方式：

```bash
DATABASE_PATH=/private/tmp/milestone2-browser-validation.db ENABLE_QWEN_API=0 ./.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
cd frontend
npm run dev -- --host 127.0.0.1
curl http://127.0.0.1:5173/api/jobs?limit=30
```

浏览器检查结果：

```text
登录页：PASS，可输入测试账号 m2-browser-check 并进入应用。
总工作台：PASS，可见生成工作台、上传与生成、结果主画布、图表/配图/流程/逐页解析入口。
日志界面：PASS，可见 demo-1c60f36568 任务卡片，状态 completed。
任务详情：PASS，可见配图评分与重生成、阶段记录、运行日志。
个人设置：PASS，可见 Qwen / WANX / Flux key 输入框和默认语义/配图配置。
移动端：PASS，390 x 844 视口下顶部导航、工作台、日志详情和设置表单可读。
```

输出文件：

- `docs/milestone2-frontend-browser-validation.md`
- `docs/screenshots/m2-workspace.png`
- `docs/screenshots/m2-logs-detail.png`
- `docs/screenshots/m2-settings.png`
- `docs/screenshots/m2-mobile-workspace.png`
- `docs/screenshots/m2-mobile-logs.png`
- `docs/screenshots/m2-mobile-settings.png`

说明：浏览器首次打开日志页时出现 `Failed to fetch`，排查确认是本地前后端 dev server 在验证过程中退出。重启后端和 Vite dev server 后，Vite 代理返回任务列表，浏览器日志页和任务详情均通过。桌面截图分辨率为 `1280 x 720`，移动端截图分辨率为 `390 x 844`。

### 3.7 后端健康检查

命令：

```bash
curl http://127.0.0.1:8000/api/health
```

结果摘要：

```json
{
  "status": "ok",
  "frontend": "vue",
  "pipeline_engine": "langgraph",
  "qwen_enabled": false,
  "wanx_enabled": true,
  "flux_enabled": true,
  "database_enabled": true,
  "database_engine": "sqlite",
  "database_path": "/private/tmp/milestone2-log-trace-dev.db",
  "database_exists": true
}
```

说明：当前本地后端以 `ENABLE_QWEN_API=0` 启动，因此健康检查中 `qwen_enabled=false`。该状态符合本地 fallback 验证目的；外部 Qwen 路径仍需用真实 key 和启用配置补测。

### 3.8 Docker 部署验证

当前证据见 `docs/milestone2-docker-validation.md`。

已通过：

- `docker --version`
- `docker compose version`
- `docker compose config`
- `docker pull hello-world:latest`

2026 年 6 月 4 日复验新增证据：

```text
docker info --format '{{.ServerVersion}} {{.OSType}}/{{.Architecture}}'
29.4.3 linux/aarch64
```

说明：提权后 Docker daemon 可达，Docker Hub 基础镜像拉取通道可用。首次 Compose 构建曾因 `docker-credential-desktop` 不在普通 PATH 中失败；将 Docker Desktop 资源目录临时加入 PATH 后，该问题已解除。

新增通过项：

```text
docker pull hello-world:latest
Status: Downloaded newer image for hello-world:latest

frontend:
RUN npm ci
RUN npm run build
39 modules transformed
built in 558ms
naming to docker.io/library/ppt-smart-chart-generator-frontend:latest done
```

仍阻塞：

```text
PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH" docker compose up -d --build
RUN apt-get update && apt-get install -y --no-install-recommends gcc libgomp1 curl
E: Failed to fetch http://deb.debian.org/debian/pool/main/b/binutils/libbinutils_2.44-3_arm64.deb
500 writing response to deb.debian.org:80: reading HTTP GET: unexpected EOF
E: Unable to fetch some archives, maybe run apt-get update or try with --fix-missing?
target backend: failed to solve
```

结论：Docker CLI、Compose、配置解析、daemon 访问和 Docker Hub 基础拉取已通过；前端镜像已成功构建。当前剩余阻塞点是后端镜像构建时 Debian apt 下载 EOF，容器未进入双服务 running 状态，`M2.11` 不能标记为已完成。

已采取缓解措施：`Dockerfile.backend` 已为 apt 阶段加入 `APT_RETRIES=5`、HTTP 超时和 HTTPS 超时参数。该改动不改变后端依赖，只提升 Debian apt 下载阶段的容错能力；仍需下一轮完整 Docker Compose 构建复验。

## 4. 专项报告索引

| 报告 | 主要覆盖 |
|---|---|
| `docs/milestone2-ppt-parser-enhancement-report.md` | `M2.2` PPT 解析增强 |
| `docs/milestone2-ppt-layout-qa-report.md` | `M2.3` PPT 写回与版式优化 |
| `docs/milestone2-layout-prefill-report.md` | `M2.3`、`M2.10` 真实 PPT 版式预复核 |
| `docs/milestone2-chart-recommendation-report.md` | `M2.4` 图表推荐质量 |
| `docs/milestone2-chart-stability-report.md` | `M2.5` 图表生成稳定性 |
| `docs/milestone2-image-quality-regeneration-report.md` | `M2.6`、`M2.7` 配图质量与重生成 |
| `docs/milestone2-quality-gallery-report.md` | `M2.5`、`M2.6`、`M2.7` 图表与配图质量样例 Gallery |
| `docs/milestone2-frontend-quality-fields-report.md` | `M2.8` 前端字段展示 |
| `docs/milestone2-frontend-browser-validation.md` | `M2.8`、`M2.9`、`M2.10` 前端浏览器验收 |
| `docs/milestone2-database-log-trace-report.md` | `M2.9` 数据库与日志追踪 |
| `docs/milestone2-docker-validation.md` | `M2.11` Docker 部署验证 |
| `docs/milestone2-api-reference.md` | `M2.12` API 接口说明 |

## 5. 当前待补证据

- Docker daemon 稳定后的 `PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH" docker compose up -d --build`、`curl http://127.0.0.1:8080` 和 Nginx 代理验证。
- Qwen、WANX、Flux 在真实 API key 环境下的外部模型路径验证。
- 将 2026 年 6 月 6 日 M2 测试 PPT 人工复核结论同步到 `docs/milestone2-manual-review-scorecard.md` 或最终汇报材料。

## 6. 当前结论

`M2.10` 已具备自动化测试、语义评估、50 页烟测、前端构建和 M2 测试 PPT 人工回归证据，能够支撑 Milestone 2 阶段性汇报。2026 年 6 月 6 日已完成空页、图片页、复杂文本页和批量预览原稿底图的回归验证，用户确认修复后的增强版 PPT 无问题。当前剩余风险主要集中在 Docker Compose 后端镜像完整启动，以及 Qwen、WANX、Flux 真实 API key 环境下的外部模型路径验证。
