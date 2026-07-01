# PPT-Smart-Chart-Generator

语义驱动的 PPT 智能图表生成与多模态配图系统。

## 当前进度

### 已完成

- 前端已经从 `Gradio` 完整切换为 `Vue 3 + Vite`，支持：
  - PPT 上传
  - 页码选择
  - 当前页实时预览
  - 图表预览
  - 配图预览
  - PPT 页码范围批量处理
  - 进度条、阶段状态、日志回显
  - 文本演示模式
  - 图表类型手动修正
  - 配图风格与配图模型选择
- 后端已经统一为 `FastAPI + Pipeline` 架构，支持：
  - PPT 内容解析
  - 文本模式直接生成图表
  - 本地规则 / 千问 API 双语义模式
  - 图表生成
  - 配图生成
  - 增强版 PPT 导出
  - 图表与配图写回 PPT
  - `/api/health`、`/api/process`、`/api/process-batch`、`/api/demo-chart`、`/api/slide-preview`
- 图表模块当前已支持多种类型：
  - `bar`
  - `line`
  - `pie`
  - `scatter`
  - `area`
  - `histogram`
  - `box`
  - `heatmap`
- 配图模块当前支持三种模式：
  - `local`：本地 PNG 配图预览
  - `wanx`：通义万相接入
  - `flux`：Flux 接入
- 已补齐基础测试、Docker 部署配置、技术文档初稿、前端使用说明和 Milestone 2 测试报告。

### 当前已知状态

- 千问语义分析主流程已接通，调用成功时会在日志中显示 `Semantic analysis completed with Qwen.`
- PPT 上传后，切换页码可以实时查看当前页的预览图。
- 图表和配图现在都可以作为 PNG 写回到增强版 PPT 中。
- `wanx` 和 `flux` 已接入真实调用分支；如果外部接口失败，会自动回退到本地配图预览，不会中断整条流程。

### 当前仍可继续优化

- `wanx` / `flux` 的线上返回效果还需要根据真实 key 和模型输出继续调优。
- 复杂 PPT 模板、复杂表格语义、写回版式位置还可以继续优化。
- 当前页预览是轻量渲染版，适合快速选页，不是 PowerPoint 原生像素级截图。


## 前五周阶段结果

- 第 1 周：完成基础工程搭建，前端切换到 Vue，后端切到 FastAPI。
- 第 2 周：完成 Pipeline 主链路、图表预览区、配图区、日志与进度展示。
- 第 3 周：补齐语义增强、图表推荐扩展、PPT 写回主路径。
- 第 4 周：完成千问接入、本地规则兜底、配图风格与模型参数联动。
- 第 5 周：完成 Pipeline 进度显示、错误重试、图表主题统一、Prompt 工程文档初稿和真实 PPT 稳定性验证。
- 第 6 周：完成用户反馈循环、批量多页处理、RAG 检索调优和前端工作台高级 UI 美化。
- 第 7 周：完成语义识别/CLIP/耗时评估脚本、图表插入问题修复、意图识别测试报告和 50 页批量烟测。
- 第 8 周：完成完整测试报告、前端使用说明与风格控制文档、Prompt 工程整理和生产构建验证。

## 项目结构

```text
.
├── app.py                         # FastAPI 启动入口
├── backend/                       # 后端整合目录
│   ├── app.py
│   ├── pipeline.py
│   ├── chart_generator.py
│   ├── ppt_parser.py
│   ├── image_clients.py
│   └── insert_to_pptx.py
├── main.py                        # 轻量调试入口
├── main_pipeline.py               # Pipeline 兼容导出入口
├── frontend/                      # Vue 3 前端
├── tests/                         # 自动化测试
├── docs/
│   ├── week1-deliverables.md
│   ├── technical-design-draft.md
│   ├── prompt-engineering-notes.md
│   ├── milestone2-test-report.md
│   ├── frontend-user-guide.md
│   └── week7-8-biweekly-report.md
└── requirements.txt
```

## 本地部署与启动

本地开发推荐使用“后端 FastAPI + 前端 Vite dev server”的方式启动：

- 后端地址：`http://127.0.0.1:8000`
- 前端地址：`http://127.0.0.1:5173`
- Vite 会把 `/api` 和 `/assets` 请求代理到本地后端。

### 0. 环境要求

- Python 3.12 推荐，项目 Docker 镜像也使用 Python 3.12。
- Node.js 20 推荐，前端 Docker 构建也使用 Node 20。
- macOS / Linux 可直接使用下面命令；Windows 用户请把虚拟环境激活命令替换为 `.venv\Scripts\activate`。

### 1. 准备后端环境

在项目根目录执行：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. 配置可选环境变量

不配置外部模型 Key 也可以本地启动，系统会使用本地规则语义分析和本地配图预览。
如果用户在工作台选择 `qwen`、`wanx` 或 `flux`，需要先在“个人设置”填写自己的 API Key；对应 Key 为空时，前端和后端都会提示并阻止请求。

如果需要配置默认模型名或服务端本地调试 Key，可在项目根目录创建 `.env`：

```env
ENABLE_QWEN_API=1
QWEN_API_KEY=your-qwen-api-key
QWEN_MODEL=qwen-plus

# 可选：通义万相配图
WANX_API_KEY=your-wanx-api-key
WANX_MODEL=wan2.6-t2i

# 可选：Flux 配图
FLUX_API_KEY=your-flux-api-key
FLUX_MODEL_ENDPOINT=flux-pro-1.1
```

如果只想离线演示或暂时没有 Key，可以写成：

```env
ENABLE_QWEN_API=0
```

后端会自动创建并使用这些本地目录：

- `data/uploads`
- `outputs`
- `outputs/previews`
- `logs`

### 3. 启动后端

保持虚拟环境已激活，在项目根目录执行：

```bash
python app.py
```

后端默认监听 `http://127.0.0.1:8000`。也可以使用等价的 Uvicorn 命令：

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

### 4. 启动前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

启动后访问 `http://127.0.0.1:5173`。前端开发服务器会把接口和生成资源代理到 `http://127.0.0.1:8000`。

### 5. 验证本地服务

```bash
curl http://127.0.0.1:8000/api/health
```

浏览器打开前端后，可以先使用文本演示模式输入：

```text
营收: 120
成本: 80
利润: 40
```

如果返回图表、配图预览和日志，说明本地部署已正常工作。

### 6. 停止服务

- 后端终端按 `Ctrl+C`。
- 前端终端按 `Ctrl+C`。
- 如果启用了虚拟环境，可以执行 `deactivate` 退出。

## 当前可用功能

### PPT 模式

- 上传 `.pptx`
- 自动生成第一页预览
- 调整页码时实时查看当前页
- 按页码范围批量生成图表、配图和合并版 PPT
- 选择语义分析模式
- 手动修正图表类型
- 选择配图风格和配图模型
- 一键生成图表、配图和增强版 PPT

### 文本演示模式

- 输入如 `营收: 120`
- 直接生成图表 PNG
- 同步返回配图、日志和阶段状态

### 健康检查

```bash
curl http://127.0.0.1:8000/api/health
```

可查看：

- 千问是否启用
- WANX 是否已配置
- FLUX 是否已配置
- 当前支持的语义模式、图表类型和配图风格

## 测试

当前仓库包含标准库可运行的基础测试：

```bash
python -m unittest tests.test_pipeline
```

安装 `pytest` 后，也可以继续沿用 `pytest` 工作流。

Milestone 2 评估与批量烟测：

```bash
python evaluator.py
./.venv/bin/python tools/run_50_slide_smoke.py
```

评估报告会输出到 `outputs/evaluation_report.csv`、`outputs/evaluation_summary.json` 和 `outputs/evaluation_summary.md`。

## Docker 部署

项目已经提供了前后端分离的 Docker 包装：

- `Dockerfile.backend`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `docker-compose.yml`

### 1. 准备环境变量

如需配置默认模型名或服务端本地调试 Key，可在根目录 `.env` 写入：

```env
QWEN_API_KEY=your-qwen-api-key
ENABLE_QWEN_API=1
QWEN_MODEL=qwen-plus
```

如果你暂时不想启用千问，可以设置；前端用户仍可在个人设置中填写自己的 Qwen Key 后发起 Qwen 请求：

```env
ENABLE_QWEN_API=0
```

### 2. 构建并启动

```bash
docker compose up -d --build
```

启动后：

- 前端地址：`http://服务器IP:8080`
- 后端地址：`http://服务器IP:8000`

### 3. 查看日志

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

### 4. 停止服务

```bash
docker compose down
```

### 5. 持久化目录

以下目录会挂载到宿主机，方便保留结果文件：

- `./outputs`
- `./logs`
- `./data/uploads`
