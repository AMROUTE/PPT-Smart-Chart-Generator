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
  - `/api/health`、`/api/process`、`/api/demo-chart`、`/api/slide-preview`
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
- 已补齐基础测试、Docker 部署配置和技术文档初稿。

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
- 第 5 周：完成 Docker 化、增强版 PPT 导出、当前页实时预览、真实配图模型接入骨架。

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
│   └── prompt-engineering-notes.md
└── requirements.txt
```

## 启动方式

### 1. 后端

```bash
pip install -r requirements.txt
python app.py
```

默认启动在 `http://127.0.0.1:8000`。

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

默认开发地址为 `http://127.0.0.1:5173`，并会把 `/api` 和 `/assets` 请求代理到本地 Python 服务。

## 当前可用功能

### PPT 模式

- 上传 `.pptx`
- 自动生成第一页预览
- 调整页码时实时查看当前页
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

## Docker 部署

项目已经提供了前后端分离的 Docker 包装：

- `Dockerfile.backend`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `docker-compose.yml`

### 1. 准备环境变量

确保根目录 `.env` 至少包含：

```env
QWEN_API_KEY=your-qwen-api-key
ENABLE_QWEN_API=1
QWEN_MODEL=qwen-plus
```

如果你暂时不想启用千问，可以设置：

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
