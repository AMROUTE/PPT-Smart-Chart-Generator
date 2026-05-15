# 技术文档初稿

## 1. 系统概览

项目采用 `Vue 3 + Vite` 前端与 `FastAPI` 后端，核心流程由 `Pipeline` 统一编排，覆盖以下阶段：

1. `parse_ppt`
2. `semantic_analysis`
3. `generate_chart`
4. `generate_illustration`
5. `save_pptx`

## 2. 前端设计

- 文件：`frontend/src/App.vue`
- 功能：上传 PPT、文本演示、进度展示、图表预览、配图预览、日志展示、图表类型修正、配图风格与模型选择
- 本地开发代理：`/api` 与 `/assets`

## 3. 后端设计

- 应用入口：`backend/app.py`
- 服务层：`backend/services.py`
- 状态结构：`backend/schemas.py`
- 流程编排：`backend/pipeline.py`
- PPT 解析：`backend/ppt_parser.py`
- 图表生成：`backend/chart_generator.py`
- PPT 写回：`backend/insert_to_pptx.py`
- 千问接入：`backend/qwen_client.py`

## 4. 核心接口

- `GET /api/health`
- `GET /api/pipeline`
- `POST /api/process`
- `POST /api/demo-chart`

## 5. 当前已实现能力

- PPT 上传与页码处理
- 文本到图表演示
- 本地规则 / 千问 API 双模式
- 图表类型手动覆盖
- 配图风格与配图模型选择
- 图表预览、配图预览、日志与阶段状态展示
- 增强版 PPT 输出
- Docker 化部署

## 6. 当前限制

- 配图模型当前以本地预览流程为主，`Flux` / `通义万相` 作为接口级可切换选项保留
- 配图评分当前为本地启发式分数，用于演示闭环和人工重生成提示
- 复杂 PPT 模板与大规模评测仍需继续完善
