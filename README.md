# PPT-Smart-Chart-Generator

语义驱动的 PPT 智能图表生成与多模态配图系统。

## Week 1 完成情况

- 前端从 Gradio 方案切换为 Vue 3 + Vite 工程，覆盖上传文件、页码选择、基本信息展示、结果预览区。
- 后端调整为 API 服务骨架，保留后续接入 LangGraph、图表生成、配图生成的扩展点。
- `main_pipeline.py` 完成第一周需要的 LangGraph Pipeline 设计骨架，并提供无依赖 fallback，方便本地先验证结构。
- `tests/` 补齐测试框架基础用例，覆盖 Pipeline 结构与后端辅助函数。

## 项目结构

```text
.
├── app.py                  # 兼容启动入口
├── backend/                # 后端整合目录
├── main_pipeline.py        # Pipeline 兼容导出入口
├── frontend/               # Vue 3 前端
├── tests/                  # 第一周测试框架
├── docs/week1-deliverables.md
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

默认开发地址为 `http://127.0.0.1:5173`，并会把 `/api` 请求代理到本地 Python 服务。

## 测试

当前仓库包含标准库可运行的基础测试：

```bash
python -m unittest discover -s tests
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
