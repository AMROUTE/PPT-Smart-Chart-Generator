# Prompt 工程文档初稿

## 1. 目标

Prompt 工程用于支撑语义识别模块完成以下任务：

- 判断页面是否适合生成图表
- 识别图表表达意图
- 推荐合适图表类型
- 输出结构化字段供下游模块消费

## 2. 当前语义分析输出字段

- `chart_type`
- `reason`
- `summary`
- `visual_theme`
- `palette`
- `keywords`
- `audience`

## 3. 当前模式

### 本地规则模式

根据以下信息进行规则判断：

- 文本关键词，如“趋势”“增长”“占比”“份额”
- 表格标签模式，如年份、季度、月份
- 数值列数量与行数

### 千问模式

通过 `backend/qwen_client.py` 调用千问兼容接口，返回结构化语义分析结果；若调用失败，则回退到本地规则模式。

## 4. Few-shot / RAG 相关资源

- 案例库：`test_cases.py`
- 检索逻辑：`rag_retriever.py`
- 评测脚本：`evaluator.py`

## 5. 边缘案例处理

- 无显式数值：使用默认演示数据兜底
- 图表类型不稳定：允许前端手动覆盖
- 千问接口失败：自动回退本地规则
- 配图匹配分数低：Pipeline 先生成 refined prompt；本地配图预览会自动重生成，并在 `illustration_meta` 中记录初始分、最终分、阈值、重生成动作和原因

## 6. 配图 Prompt 约束

配图 Prompt 与图表 Prompt 解耦，只表达业务场景、行业环境或概念插画，不要求模型绘制任何数据图形。

统一负面约束：

```text
Avoid charts, axes, dashboards, data panels, tables, bar shapes, line plots, pie slices, or explicit statistical graphics.
```

当前支持的风格方向：

| 风格 | 场景方向 |
|---|---|
| `auto` | 清晰业务场景，包含人物、地点和活动 |
| `business` | 现代办公协作、会议讨论、执行汇报氛围 |
| `tech` | 软件团队工作区、设备、云服务和产品流程 |
| `education` | 课堂、教师、学生、书本和学习环境 |
| `medical` | 医疗咨询、临床护理、可信赖的健康场景 |
| `academic` | 研究讨论、论文、电脑、研讨或图书馆环境 |
| `sketch` | 手绘白板风格的解决问题场景 |

## 7. 配图评分与重生成

Pipeline 会输出：

- `illustration_meta.initial_clip_score`
- `illustration_meta.clip_score`
- `illustration_meta.score_threshold`
- `illustration_meta.regenerated`
- `illustration_meta.regenerate_attempts`
- `illustration_meta.regenerate_action`
- `illustration_meta.regenerate_reason`

当前阈值为 `6.5`。本地预览低于阈值时，系统使用更具体的行业场景 refined prompt 自动重生成；外部模型结果低于阈值时，保留人工复核依据，避免无控制地重复消耗 API 额度。
