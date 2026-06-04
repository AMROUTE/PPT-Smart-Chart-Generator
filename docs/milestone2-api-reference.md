# Milestone 2 API 接口说明

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

适用版本：`backend.app:app`，Milestone 2 当前实现

基础地址：

```text
http://127.0.0.1:8000
```

## 1. 通用说明

### 1.1 请求格式

除查询接口外，主要业务接口使用 `multipart/form-data`，便于同时上传 `.pptx` 文件和提交配置字段。

### 1.2 文件类型

当前只支持 `.pptx`。

不支持：

- `.ppt`
- `.pdf`
- `.docx`
- 图片文件直接上传为 PPT

### 1.3 可选配置枚举

| 字段 | 可选值 | 默认值 | 说明 |
|---|---|---|---|
| `semantic_mode` | `local`、`qwen` | `local` | 语义分析模式；Qwen 不可用时回退本地规则 |
| `chart_type_override` | `auto`、空、`bar`、`line`、`pie`、`scatter`、`area`、`histogram`、`box`、`heatmap` | 空 | 手动覆盖图表类型；空或 auto 表示自动推荐 |
| `chart_theme` | `tech`、`business`、`minimal`、`academic` | `tech` | 图表主题 |
| `illustration_style` | `auto`、`business`、`tech`、`education`、`medical`、`academic`、`sketch` | `auto` | 配图风格 |
| `image_model` | `local`、`flux`、`wanx` | `local` | 配图模型；外部模型不可用时回退本地预览 |

### 1.4 自定义模型 Key 字段

以下字段可由前端设置页或接口调用临时传入：

- `custom_qwen_api_key`
- `custom_qwen_model`
- `custom_wanx_api_key`
- `custom_flux_api_key`

这些字段只用于当前请求，不应写入文档、日志或截图中。

## 2. 健康检查

```http
GET /api/health
```

用途：

- 检查后端是否可用。
- 检查模型配置状态。
- 检查 SQLite 数据库状态。
- 检查当前支持的模式和功能列表。

示例：

```bash
curl http://127.0.0.1:8000/api/health
```

关键返回字段：

| 字段 | 说明 |
|---|---|
| `status` | `ok` 表示后端可用 |
| `frontend` | 当前前端类型，预期为 `vue` |
| `pipeline_engine` | Pipeline 引擎 |
| `qwen_enabled` | Qwen 是否启用 |
| `wanx_enabled` | WANX key 是否存在 |
| `flux_enabled` | Flux key 是否存在 |
| `semantic_modes` | 支持的语义模式 |
| `image_models` | 支持的配图模型 |
| `database_stats` | SQLite 用户、上传和任务计数 |

## 3. Pipeline 结构

```http
GET /api/pipeline
```

用途：

- 返回当前 Pipeline Mermaid 图。
- 用于汇报或调试流程结构。

示例：

```bash
curl http://127.0.0.1:8000/api/pipeline
```

返回：

```json
{
  "mermaid": "graph TD\n..."
}
```

## 4. 登录

```http
POST /api/auth/login
```

请求类型：`multipart/form-data`

字段：

| 字段 | 必填 | 说明 |
|---|---|---|
| `username` | 是 | 用户名 |
| `password` | 是 | 密码 |

说明：

- 如果用户不存在，会自动创建用户。
- 如果用户存在但密码不匹配，返回 `400`。

示例：

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -F "username=demo" \
  -F "password=demo"
```

## 5. 单页 PPT 处理

```http
POST /api/process
```

用途：

- 上传 `.pptx`。
- 处理指定页。
- 生成图表、配图、增强版 PPT。
- 返回资源 URL、日志、阶段状态和质量元数据。

请求类型：`multipart/form-data`

字段：

| 字段 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `file` | 是 | - | `.pptx` 文件 |
| `slide_number` | 否 | `1` | 处理页码，从 1 开始 |
| `semantic_mode` | 否 | `local` | 语义模式 |
| `chart_type_override` | 否 | 空 | 图表类型覆盖 |
| `chart_theme` | 否 | `tech` | 图表主题 |
| `illustration_style` | 否 | `auto` | 配图风格 |
| `image_model` | 否 | `local` | 配图模型 |
| `custom_qwen_api_key` | 否 | 空 | 当前请求的 Qwen key |
| `custom_qwen_model` | 否 | 空 | 当前请求的 Qwen 模型 |
| `custom_wanx_api_key` | 否 | 空 | 当前请求的 WANX key |
| `custom_flux_api_key` | 否 | 空 | 当前请求的 Flux key |

示例：

```bash
curl -X POST http://127.0.0.1:8000/api/process \
  -F "file=@/path/to/demo.pptx" \
  -F "slide_number=1" \
  -F "semantic_mode=local" \
  -F "chart_type_override=auto" \
  -F "chart_theme=business" \
  -F "illustration_style=tech" \
  -F "image_model=local"
```

关键返回字段：

| 字段 | 说明 |
|---|---|
| `file` | 上传文件元数据 |
| `pipeline.status` | `completed` 表示完成 |
| `pipeline.progress` | Pipeline 进度，完成时为 `100` |
| `pipeline.intent` | 图表推荐、语义意图、配图主题和版式诊断 |
| `pipeline.chart_spec` | 图表生成配置 |
| `pipeline.illustration_meta` | 配图评分、重生成和外部模型 fallback 元数据 |
| `pipeline.chart_image_url` | 图表预览资源 URL |
| `pipeline.illustration_image_url` | 配图预览资源 URL |
| `pipeline.final_pptx_url` | 增强版 PPT 下载 URL |
| `pipeline.logs` | 运行日志 |
| `pipeline.stage_history` | 阶段历史 |

## 6. 批量 PPT 处理

```http
POST /api/process-batch
```

用途：

- 对多个页码执行批量处理。
- 输出同一个增强版 PPT。

请求类型：`multipart/form-data`

字段：

| 字段 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `file` | 二选一 | - | 新上传 `.pptx` |
| `upload_token` | 二选一 | 空 | 已上传文件 token |
| `slide_numbers` | 否 | 空 | 指定页码，如 `1,3,5`；优先级高于范围 |
| `slide_start` | 否 | `1` | 页码范围起点 |
| `slide_end` | 否 | `0` | 页码范围终点；0 表示自动 |
| 其他配置字段 | 否 | 同 `/api/process` | 语义、图表、配图配置 |

示例：

```bash
curl -X POST http://127.0.0.1:8000/api/process-batch \
  -F "file=@/path/to/demo.pptx" \
  -F "slide_numbers=1,3,5" \
  -F "semantic_mode=local" \
  -F "image_model=local"
```

关键返回字段：

| 字段 | 说明 |
|---|---|
| `batch.total_slides` | 请求处理页数 |
| `batch.success_count` | 成功页数 |
| `batch.failure_count` | 失败页数 |
| `batch.slides` | 每页处理结果 |
| `batch.final_pptx_url` | 批量增强版 PPT 下载 URL |

## 7. 文本演示模式

```http
POST /api/demo-chart
```

用途：

- 无 PPT 输入时快速验证语义识别、图表推荐、配图生成、日志和 fallback。

请求类型：`multipart/form-data`

字段：

| 字段 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `source_text` | 是 | - | 演示文本 |
| 其他配置字段 | 否 | 同 `/api/process` | 语义、图表、配图配置 |

示例：

```bash
curl -X POST http://127.0.0.1:8000/api/demo-chart \
  -F "source_text=广告投入越高，销售额通常越高。" \
  -F "semantic_mode=local" \
  -F "chart_type_override=auto" \
  -F "image_model=local"
```

预期：

- `pipeline.intent.intent_category` 接近 `correlation`。
- `pipeline.intent.chart_type` 接近 `scatter`。
- `pipeline.chart_image_url` 和 `pipeline.illustration_image_url` 可访问。

## 8. 单页预览

```http
POST /api/slide-preview
```

用途：

- 上传或复用 PPT 文件，生成指定页的预览图。
- 前端上传后会优先调用该接口。

请求类型：`multipart/form-data`

字段：

| 字段 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `file` | 二选一 | - | `.pptx` 文件 |
| `upload_token` | 二选一 | 空 | 已上传文件 token |
| `slide_number` | 否 | `1` | 预览页码 |

示例：

```bash
curl -X POST http://127.0.0.1:8000/api/slide-preview \
  -F "file=@/path/to/demo.pptx" \
  -F "slide_number=1"
```

关键返回字段：

- `upload_token`
- `slide_number`
- `slide_count`
- `preview_image_url`
- `file`

## 9. 逐页解析

```http
POST /api/parse-slides
```

用途：

- 返回整份 PPT 的逐页摘要。
- 用于前端逐页解析面板。
- 支持空页、图片页、表格页、文本页诊断。

请求类型：`multipart/form-data`

字段：

| 字段 | 必填 | 说明 |
|---|---|---|
| `file` | 二选一 | `.pptx` 文件 |
| `upload_token` | 二选一 | 已上传文件 token |

示例：

```bash
curl -X POST http://127.0.0.1:8000/api/parse-slides \
  -F "upload_token=uploaded-file-token.pptx"
```

每页关键字段：

| 字段 | 说明 |
|---|---|
| `slide_number` | 页码 |
| `text_content` | 截断后的文本内容 |
| `table_count` | 表格数 |
| `shape_count` | 元素数 |
| `picture_count` | 图片数 |
| `placeholder_count` | 占位符数 |
| `is_empty` | 是否为空页 |
| `diagnostics` | 页面诊断详情 |

## 10. 历史任务列表

```http
GET /api/jobs?limit=30
```

用途：

- 返回最近处理任务。
- 前端日志页左侧列表使用该接口。

示例：

```bash
curl "http://127.0.0.1:8000/api/jobs?limit=10"
```

关键返回字段：

- `jobs[].request_id`
- `jobs[].source_type`
- `jobs[].slide_number`
- `jobs[].status`
- `jobs[].chart_type`
- `jobs[].chart_theme`
- `jobs[].progress`
- `jobs[].updated_at`

## 11. 历史任务详情

```http
GET /api/jobs/{request_id}
```

用途：

- 查看单个历史任务详情。
- 回看日志、阶段历史、配图质量、版式诊断和资源 URL。

示例：

```bash
curl http://127.0.0.1:8000/api/jobs/demo-b085855bc6
```

关键返回字段：

| 字段 | 说明 |
|---|---|
| `job.intent` | 语义意图、推荐解释、版式诊断 |
| `job.chart_spec` | 图表配置 |
| `job.illustration_meta` | 配图评分和 fallback 元数据 |
| `job.layout` | PPT 写回版式诊断 |
| `job.logs` | Pipeline 运行日志 |
| `job.stage_history` | 阶段历史 |
| `job.chart_image_url` | 图表资源 URL |
| `job.illustration_image_url` | 配图资源 URL |
| `job.final_pptx_url` | 增强版 PPT URL |

## 12. 静态资源

后端挂载：

| 路径 | 说明 |
|---|---|
| `/assets/outputs/...` | 图表、配图、预览图和增强版 PPT 输出 |
| `/assets/uploads/...` | 上传文件资源 |

前端开发服务器和 Nginx 部署需要代理：

- `/api` 到后端
- `/assets` 到后端

## 13. 错误返回

常见错误：

| 状态码 | 场景 |
|---:|---|
| `400` | 文件类型错误、缺少上传文件、页码越界、表单字段非法 |
| `404` | 历史任务不存在 |
| `500` | Pipeline、预览、解析或批处理运行异常 |

错误格式：

```json
{
  "detail": "Please upload a .pptx file."
}
```

## 14. Milestone 2 验收关联

| WBS | API 证据 |
|---|---|
| `M2.2` | `/api/slide-preview`、`/api/parse-slides` |
| `M2.3` | `/api/process`、`/api/process-batch`、`/assets/outputs/...pptx` |
| `M2.4` | `/api/demo-chart`、`/api/process` 中的 `intent` |
| `M2.6`、`M2.7` | `illustration_meta`、`image_model`、外部模型 fallback 字段 |
| `M2.8` | 前端工作台调用 `/api/*` |
| `M2.9` | `/api/jobs`、`/api/jobs/{request_id}` |
| `M2.11` | `/api/health`、`/assets` 静态资源代理 |
| `M2.12` | 本接口说明、演示脚本、测试报告 |
