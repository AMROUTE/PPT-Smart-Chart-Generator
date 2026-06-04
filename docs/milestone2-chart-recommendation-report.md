# Milestone 2 图表推荐质量提升报告

编制日期：2026 年 6 月 4 日

对应 WBS：`M2.4 图表推荐质量提升`

## 1. 目标

本轮围绕 `M2.4` 推进图表推荐质量：把实际 Pipeline 中的本地启发式推荐从“只给 chart_type”升级为“识别意图、推荐图表、给出判断依据和置信度”的可验收结果，并用 evaluator 小批量测试验证五类意图覆盖。

## 2. 本轮增强

### 2.1 本地推荐规则

`backend/pipeline.py` 新增 `_recommend_chart_intent`，覆盖五类语义意图：

| 意图 | 推荐图表 | 主要信号 |
|---|---|---|
| `comparison` | `bar` | 对比、高低、差异、分别为 |
| `trend` | `line` | 时间线索、趋势、增长、下降、首列时间序列 |
| `composition` | `pie` | 占比、构成、份额、来源、组成 |
| `distribution` | `bar` / `histogram` | 分布、区间、集中、大多数、频率 |
| `correlation` | `scatter` | 相关、关系、影响、越...越、双数值列 |

### 2.2 Pipeline 输出字段

`intent` 现在新增：

- `intent_category`
- `recommendation_confidence`
- `recommendation_signals`
- `chart_alternatives`
- `chart_recommendation`

原有 `chart_type` 和 `reason` 保持可用。手动指定图表类型时，`reason` 会记录原始推荐和人工覆盖关系。

### 2.3 前端解释展示

`frontend/src/components/PipelineStatus.vue` 已展示：

- 推荐图表
- 语义意图
- 推荐置信度
- 判断依据
- 命中的推荐信号

这让用户可以理解系统为什么选择某个图表类型，而不是只能看到最终结果。

## 3. 验证结果

### 3.1 后端单测

命令：

```bash
./.venv/bin/python -m unittest tests.test_pipeline
```

结果：

```text
Ran 39 tests in 0.738s
OK
```

新增覆盖：

- `comparison -> bar`
- `trend -> line`
- `composition -> pie`
- `distribution -> bar`
- `correlation -> scatter`
- Demo Pipeline 输出推荐意图、置信度和信号字段。

### 3.2 语义评测

命令：

```bash
./.venv/bin/python evaluator.py
```

结果：

| 指标 | 结果 | 目标 | 状态 |
|---|---:|---:|---|
| 样本数 | 60 | - | INFO |
| 意图准确率 | 100.00% | 88% | PASS |
| 平均 CLIP 代理分数 | 7.02 | 6.5 | PASS |
| 平均单样本耗时 | 0.01 ms | - | INFO |

输出文件：

- `outputs/evaluation_report.csv`
- `outputs/evaluation_summary.json`
- `outputs/evaluation_summary.md`

说明：本轮 evaluator 自动回退到 local 引擎，原因是 LLM parser 依赖导入失败：`cannot import name 'masked' from 'numpy.ma'`。本地兜底规则仍达到当前验收目标。

### 3.3 前端构建

命令：

```bash
cd frontend
npm run build
```

结果：

```text
39 modules transformed
built in 435ms
```

说明：推荐意图、置信度和命中信号展示已通过 Vite 生产构建验证。

## 4. 当前结论

`M2.4` 已具备五类意图覆盖、图表推荐解释和小批量评测证据。实际 Pipeline 输出与前端展示均可看到推荐依据，后续可继续补充 Qwen Prompt 实测和更多真实 PPT 页面人工评分。
