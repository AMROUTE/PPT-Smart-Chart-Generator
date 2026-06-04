# Milestone 2 配图质量与重生成验证报告

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

验证日期：2026 年 6 月 4 日

关联 WBS：`M2.6`、`M2.7`

## 1. 验证目标

本轮验证用于推进 Milestone 2 中的配图质量优化和配图评分与重生成策略：

- 配图 Prompt 与图表 Prompt 保持解耦。
- 配图 Prompt 明确禁止图表、坐标轴、看板、数据面板、柱状元素、折线图和饼图元素。
- 本地配图预览不再绘制容易被误认为图表的折线元素。
- Pipeline 输出初始评分、最终评分、评分阈值、是否重生成、重生成次数和重生成动作。
- 当本地配图代理分数低于阈值时，自动使用 refined prompt 重生成一版本地预览。
- WANX / Flux 外部配图入口可配置；失败时记录原因并回退到本地预览。

## 2. 实现内容

涉及文件：

- `backend/pipeline.py`
- `backend/image_clients.py`
- `tests/test_pipeline.py`
- `docs/prompt-engineering-notes.md`
- `docs/final-prompt-template.md`

新增或增强的字段：

| 字段 | 说明 |
|---|---|
| `illustration_meta.clip_score` | 最终 CLIP 代理分数 |
| `illustration_meta.initial_clip_score` | 初始 CLIP 代理分数 |
| `illustration_meta.score_threshold` | 低分重生成阈值，当前为 `6.5` |
| `illustration_meta.regenerated` | 是否已自动重生成 |
| `illustration_meta.regenerate_attempts` | 重生成次数 |
| `illustration_meta.regenerate_action` | 重生成动作，如 `local_refined_prompt` |
| `illustration_meta.regenerate_reason` | 触发重生成的原因 |
| `illustration_meta.requested_image_model` | 用户请求的配图模型 |
| `illustration_meta.external_provider_requested` | 是否请求外部配图模型 |
| `illustration_meta.external_provider` | 请求的外部模型供应方，如 `wanx` 或 `flux` |
| `illustration_meta.resolved_image_source` | 最终实际配图来源 |
| `illustration_meta.fallback_to_local` | 外部模型失败时是否回退到本地预览 |
| `illustration_prompt_retry` | 低分时生成的 refined prompt |

外部客户端验证范围：

- WANX 缺 key 时抛出明确配置错误。
- FLUX 缺 key 时抛出明确配置错误。
- WANX 能解析返回图片 URL 并下载到目标 PNG。
- FLUX 支持直接返回图片 URL 和 polling URL 两种结果形态。
- FLUX 响应缺少图片 URL 时会抛出明确错误。

## 3. 验证命令

```bash
./.venv/bin/python -m unittest tests.test_pipeline
./.venv/bin/python evaluator.py
```

## 4. 验证结果

| 检查项 | 结果 |
|---|---|
| 后端单元测试 | PASS，43 tests OK |
| 低分本地配图重生成测试 | PASS，`initial_clip_score < 6.5` 时触发 `local_refined_prompt` |
| WANX / Flux 客户端单测 | PASS，缺 key、WANX 下载、FLUX 直返和轮询路径均覆盖 |
| 外部模型 fallback 元数据 | PASS，`requested_image_model`、`resolved_image_source`、`fallback_to_local` 可回读 |
| 语义识别评估 | PASS，60/60 |
| 图表推荐准确率 | 100.00% |
| 平均 CLIP 代理分数 | 7.02 |
| 评估报告 | `outputs/evaluation_report.csv`、`outputs/evaluation_summary.md` |

低分重生成样例：

```text
输入文本：Alpha / Beta
初始代理分数：6.4
重生成动作：local_refined_prompt
最终代理分数：6.7
regenerate_hint：false
```

## 5. 当前结论

`M2.6` 已补充更明确的行业风格配图 Prompt、本地预览视觉约束、WANX / Flux 客户端 mock 验证和外部模型 fallback 元数据。WANX / Flux 真实外部调用仍需在可用 API key 和网络环境下补验。

`M2.7` 已具备自动评分、低分重生成字段和单元测试证据，可进入后续人工样例对比与验收阶段。

## 6. 待补验证

- 使用可用 WANX / Flux API key 追加线上配图真实调用路径验证。
- 整理商务、教育、科技、医疗等风格的人工对比样例。
- 浏览器截图级检查前端配图质量字段展示效果。
