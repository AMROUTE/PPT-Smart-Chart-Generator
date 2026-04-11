# 第一周交付说明

## 对应工作表任务

阿曼卓勒·阿迪力江（组长）第一周任务：

1. 创建 GitHub 仓库与项目结构
2. 最终版 `requirements.txt`
3. 设计完整 LangGraph Pipeline
4. 搭建测试框架

## 本次完成内容

### 1. 项目结构整理

- 增加 `frontend/` 目录，承载 Vue 3 前端代码。
- 将 `app.py` 调整为 API 服务骨架，方便前后端分离。
- 保留 `main_pipeline.py` 作为流程编排核心。

### 2. requirements 完整化

- 去掉 Gradio 作为主前端依赖。
- 增加 `fastapi`、`uvicorn` 用于 API 服务。
- 保留 `langgraph`、`pytest` 等后续需要的依赖。

### 3. LangGraph Pipeline 设计

当前流程节点如下：

```mermaid
graph TD
    start([Start]) --> parse_ppt
    parse_ppt --> semantic_analysis
    semantic_analysis --> generate_chart
    generate_chart --> generate_illustration
    generate_illustration --> save_pptx
    save_pptx --> end([End])
```

### 4. 测试框架

- 新增 `unittest` 基础测试，保证在未安装第三方库时也能先跑结构验证。
- 覆盖 Pipeline 节点定义、Mermaid 导出、文件校验与本地处理流程。

## 说明

- “创建 GitHub 仓库” 这一项当前默认视为仓库已存在并已初始化 Git。
- Vue 前端目前完成的是第一周所需基础界面，后续可继续按周计划补进度条、预览区和风格控制。
