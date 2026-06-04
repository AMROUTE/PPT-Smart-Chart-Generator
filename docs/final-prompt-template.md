# 最终 Prompt 模板整理

## 1. 语义识别 Prompt 目标

语义识别 Prompt 用于将 PPT 文本或用户输入转换为结构化 JSON，供后续图表生成和配图生成使用。最终模板需要同时满足：

- 能识别 comparison、trend、composition、distribution、correlation 五类意图；
- 能输出稳定 JSON；
- 能给出推荐图表类型；
- 能处理模糊文本、无明确数字、多意图混合和口语化表达；
- 能结合 RAG/Few-shot 示例提升鲁棒性。

## 2. 最终输出格式

```json
{
  "intent": "comparison | trend | composition | distribution | correlation",
  "chart_type": "bar_chart | line_chart | pie_chart | scatter_chart",
  "title": "简洁中文标题",
  "x": [],
  "y": [],
  "reason": "一句中文说明判断依据"
}
```

## 3. 意图与图表映射

| 意图 | 场景 | 推荐图表 |
|---|---|---|
| comparison | 对比不同对象、地区、产品、方案 | bar_chart |
| trend | 时间序列、阶段变化、增长下降 | line_chart |
| composition | 占比、构成、份额、组成结构 | pie_chart |
| distribution | 区间、集中程度、分布状态 | bar_chart |
| correlation | 两个变量之间的正负相关或影响关系 | scatter_chart |

## 4. 边缘情况规则

1. 无明确数字：根据语义生成相对值用于演示，并在 reason 中说明。
2. 多意图混合：选择页面表达的核心目的；若存在时间序列和持续变化，优先 trend。
3. 模糊表达：如“越来越好”“明显提升”，按最接近语义分类。
4. 口语化表达：先转换为标准业务语义，再分类。
5. 输出约束：只能输出 JSON，不能输出 Markdown 或额外解释。

## 5. 配图 Prompt 约束

配图 Prompt 与图表 Prompt 解耦。配图只生成业务场景、行业场景或概念插画，不生成图表、坐标轴、数据看板、柱状图、折线图、饼图等元素。

通用约束：

```text
Avoid charts, axes, dashboards, data panels, tables, bar shapes, line plots, pie slices, or explicit statistical graphics.
```

风格可选项：

- auto
- business
- tech
- education
- medical
- academic
- sketch

低分重生成策略：

- 初始配图 Prompt 先根据语义输出的 `visual_theme`、`summary`、`keywords`、`audience` 和用户选择的 `illustration_style` 生成。
- 如果本地代理评分低于 `6.5`，Pipeline 会生成 `illustration_prompt_retry`。
- `illustration_prompt_retry` 会把 `auto` 风格收敛到更具体的 `business` 场景，或保留用户指定风格，并补充“具体人物场景”和“明确行业上下文”。
- 本地配图预览会自动使用 refined prompt 重生成；外部模型结果保留人工复核提示，避免无限重试消耗 API。

评分与重生成输出字段：

```json
{
  "clip_score": 6.7,
  "initial_clip_score": 6.4,
  "score_threshold": 6.5,
  "regenerated": true,
  "regenerate_attempts": 1,
  "regenerate_action": "local_refined_prompt",
  "regenerate_reason": "Initial score 6.4 is below threshold 6.5."
}
```

## 6. 验证方式

使用以下命令验证语义识别模板和本地兜底规则：

```bash
python evaluator.py
python -m unittest tests.test_pipeline
```

当前验证结果：

- 样本数：60
- 意图准确率：100.00%
- 平均 CLIP 代理分数：7.02
- 输出文件：`outputs/evaluation_report.csv`
- 后端单测：43 tests OK
