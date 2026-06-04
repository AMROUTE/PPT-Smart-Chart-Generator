# Milestone 2 配图质量与重生成验证报告

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

验证日期：2026 年 6 月 4 日

关联 WBS：`M2.6`、`M2.7`

## 1. 验证目标

本轮验证用于推进 Milestone 2 中的配图质量优化和配图评分与重生成策略：

- 配图 Prompt 与图表 Prompt 保持解耦。
- 配图 Prompt 明确禁止图表、坐标轴、看板、数据面板、柱状元素、折线图和饼图元素。
- 配图 Prompt 增加 16:9 构图、清晰主体、文字留白、高分辨率和 presentation-safe 质量约束。
- 本地配图预览不再绘制容易被误认为图表的折线元素。
- Pipeline 输出初始评分、最终评分、评分阈值、是否重生成、重生成次数和重生成动作。
- Pipeline 输出评分组件，说明低分或通过的依据。
- 本地配图预览按行业风格绘制不同场景元素，并输出本地渲染特征。
- 本地配图和外部模型 Prompt 增加构图变体，降低批量多页配图同质化。
- 插图语义从通用 `business office collaboration` 升级为内容感知主题，能区分增长、区域市场、产品组合、营销投放、医疗、教育、算法等画面对象。
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
| `illustration_meta.quality_components` | 最终评分组件，如主题、风格、负向 prompt、画质规格是否命中 |
| `illustration_meta.initial_quality_components` | 初始评分组件 |
| `illustration_meta.prompt_quality_notes` | Prompt 质量约束摘要 |
| `illustration_meta.negative_prompt_terms` | 图表/看板/表格等负向约束词 |
| `illustration_meta.local_render_features` | 本地预览图渲染特征，如 `human_subjects`、`tech_device_cloud`、`medical_care_symbol` |
| `illustration_meta.composition_variant` | 当前配图构图变体，如 `duo_panel`、`full_scene`、`spotlight`、`diagonal_workshop` |
| `illustration_meta.requested_illustration_style` | 用户原始请求的配图风格，如 `auto` |
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
| 后端单元测试 | PASS，51 tests OK |
| 低分本地配图重生成测试 | PASS，`initial_clip_score < 6.5` 时触发 `local_refined_prompt` |
| Prompt 质量约束 | PASS，`Negative prompt: no charts`、16:9 构图和 presentation-safe 规格进入 prompt |
| 评分组件元数据 | PASS，`quality_components.negative_prompt=true` 等字段可回读 |
| 本地配图风格特征 | PASS，`business`、`tech`、`medical` 等风格可记录对应 `local_render_features` |
| 构图变体稳定性 | PASS，同一输入稳定复现，不同页码按 `duo_panel` / `full_scene` / `spotlight` / `diagonal_workshop` 轮换 |
| 内容感知主题 | PASS，区域份额、产品销量、广告投放等商务页不再统一生成办公室会议主题 |
| 插图多样性回归 | PASS，`docs/milestone2-illustration-diversity-report.md`，4/4 样例通过 |
| 质量样例 Gallery | PASS，`docs/quality-gallery/illustration-contact-sheet.png` 和 6 张配图样例 PNG 已生成，尺寸 / KB / 颜色数 sanity check 通过 |
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
quality_components.negative_prompt：true
local_render_features：business_growth_milestones
```

2026 年 6 月 4 日追加 demo 验证：

```text
输入文本：Q1-Q4 revenue trend
图表质量分：9.42 / 10
配图最终代理分数：7.25 / 10
quality_components：
- semantic_marker=true
- style_specific=true
- scene_spec=true
- negative_prompt=true
- quality_spec=true
```

## 5. 当前结论

`M2.6` 已补充更明确的行业风格配图 Prompt、本地预览视觉约束、WANX / Flux 客户端 mock 验证和外部模型 fallback 元数据。WANX / Flux 真实外部调用仍需在可用 API key 和网络环境下补验。

2026 年 6 月 4 日追加升级后，本地预览图不再只是通用抽象画面，而是按 `business`、`tech`、`education`、`medical`、`academic`、`sketch` 等风格绘制不同场景元素；同时按页码和内容稳定选择 `duo_panel`、`full_scene`、`spotlight`、`diagonal_workshop` 等构图变体。`business` 场景继续细分为 `business_growth_milestones`、`business_regional_network`、`business_product_showroom`、`business_marketing_studio` 等主题对象，避免批量页全部生成会议室插图。`local_render_features` 与 `composition_variant` 可作为没有外部 API key 时的可验收证据。

同日追加生成 `docs/milestone2-quality-gallery-report.md`，其中包含 6 张本地配图风格样例 PNG 和 contact sheet，可用于人工对比不同风格是否足够可区分。

2026 年 6 月 5 日追加 `docs/milestone2-illustration-diversity-report.md`，专门覆盖增长、区域、产品、营销四个相近商务页，防止插图再次退化为通用办公室会议场景。该报告生成 `docs/quality-gallery/illustration-diversity-contact-sheet.png`，并检查主题特征、构图变体、视觉主题和两两像素差。

`M2.7` 已具备自动评分、评分组件、低分重生成字段、本地渲染特征和单元测试证据，可进入后续人工样例对比与验收阶段。

## 6. 待补验证

- 使用可用 WANX / Flux API key 追加线上配图真实调用路径验证。
- 整理商务、教育、科技、医疗等风格的人工对比样例。
- 浏览器截图级检查前端配图质量字段展示效果。
