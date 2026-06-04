# Milestone 2 图表生成稳定性验证报告

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

验证日期：2026 年 6 月 4 日

关联 WBS：`M2.5`、`M2.10`

## 1. 验证目标

本轮用于推进 `M2.5 图表生成稳定性优化`：

- 确认 8 类图表类型均能生成 PNG。
- 处理空数据、缺失值、非法数值、单数值列等异常场景。
- 图表生成器自身具备 placeholder fallback，不完全依赖 Pipeline 外层异常兜底。
- 输出图表质量元数据，支持从 `chart_spec` 判断数据覆盖率、可读性和渲染策略。
- 保持 50 页批量 smoke 和语义评估稳定。

## 2. 实现内容

涉及文件：

- `backend/chart_generator.py`
- `backend/database.py`
- `tests/test_pipeline.py`

图表生成器增强：

| 场景 | 处理方式 |
|---|---|
| 空数据 | 输出 placeholder PNG，`fallback=true` |
| 无数值列 | 输出 placeholder PNG，记录 warning |
| 缺失值 / 非法数值 | 转换为 `0.0`，不中断绘图 |
| `scatter` 数值列不足 | 自动加入 `_point_index` 合成列 |
| `heatmap` 单数值列 | 自动加入 baseline 列 |
| `pie` 负数或全 0 | 负数转 0；全 0 使用等比例 placeholder slices |
| 类别过多 | 对柱状、折线、面积、饼图等类别图进行可读性抽样，并记录 warning |
| 图表可读性 | 绘制轴刻度、数值标签、图例和截断标签 |
| 正负值柱状图 | 使用零基线绘制，避免负值从底部误画 |
| 饼图类别过多 | 保留主要切片，将剩余小切片聚合为 `Other`，避免直接丢失份额 |
| 文本演示解析 | 保留 `2020: 100`、`0-10分: 2` 等数字/区间标签；重复双指标自动配对为真实二维 scatter 数据 |
| 相关性散点图 | 使用真实 x/y 指标名，绘制趋势线，并记录 `scatter_real_xy` 或 `scatter_synthetic_index` |

新增质量字段：

| 字段 | 说明 |
|---|---|
| `chart_spec.quality_score` | 图表质量代理分数，满分 10 |
| `chart_spec.quality_checks.numeric_coverage` | 已渲染数值字段的有效数值覆盖率 |
| `chart_spec.quality_checks.value_range` | 已渲染数值范围 |
| `chart_spec.quality_checks.readability` | `full` 或 `sampled`，表示是否因可读性做了抽样 |
| `chart_spec.render_notes` | 渲染增强说明，如 `value_labels`、`axis_ticks` |
| `chart_spec.quality_status` | 图表质量门禁状态：`pass`、`attention`、`review`、`fallback` |
| `chart_spec.review_required` | 是否需要人工复核 |
| `chart_spec.review_reason` | 质量门禁说明 |

补充修复：

- 发现 50 页 smoke 在旧 SQLite schema 下写入任务记录会失败。
- 已将 `processing_jobs` 自动补列逻辑加入任务写入、列表和详情读取前，确保旧数据库也能兼容新增字段。

## 3. 验证命令

```bash
./.venv/bin/python -m unittest tests.test_pipeline
./.venv/bin/python tools/run_50_slide_smoke.py
./.venv/bin/python evaluator.py
cd frontend
npm run build
```

## 4. 验证结果

| 检查项 | 结果 |
|---|---|
| 后端单元测试 | PASS，54 tests OK |
| 8 类图表生成测试 | PASS，`bar`、`line`、`pie`、`scatter`、`area`、`histogram`、`box`、`heatmap` |
| 空数据 placeholder | PASS |
| 缺失值 / 非法值处理 | PASS |
| Scatter / Heatmap 数值列不足补足 | PASS |
| Pie 非正值安全处理 | PASS |
| 图表质量元数据 | PASS，`quality_score`、`quality_checks`、`render_notes` 可回读 |
| 图表质量门禁 | PASS，`quality_status`、`review_required`、`review_reason` 可回读 |
| 类别过多抽样 | PASS，14 条类别数据抽样为 10 条并记录 warning |
| 负值柱状图零基线 | PASS，正负值混合数据记录 `zero_baseline` |
| 饼图 Other 聚合 | PASS，8 类饼图聚合为 6 个渲染切片并记录 warning |
| 质量样例 Gallery | PASS，`docs/quality-gallery/chart-contact-sheet.png` 和 4 张图表样例 PNG 已生成，尺寸 / KB / 颜色数 sanity check 通过 |
| 图表多样性回归 | PASS，`docs/milestone2-chart-diversity-report.md`，5/5 样例通过 |
| 旧 SQLite schema 自动补列 | PASS |
| 50 页批量 smoke | PASS，50/50 completed，平均 CLIP 代理分数 6.7 |
| 语义评估 | PASS，60/60，准确率 100.00%，平均 CLIP 代理分数 7.02 |
| 前端生产构建 | PASS，39 modules transformed |

50 页 smoke 输出：

```json
{
  "requested_slides": 50,
  "processed_count": 50,
  "completed_count": 50,
  "final_pptx_exists": true,
  "average_clip_score": 6.7,
  "pass": true
}
```

## 5. 当前结论

`M2.5` 已具备更强的图表生成稳定性证据：8 类图表路径均可生成 PNG，常见异常数据不会中断流程，空数据也能输出可展示的 fallback 图。

2026 年 6 月 4 日追加升级后，图表输出不只证明“生成成功”，还可通过 `chart_spec` 证明图表质量：轴刻度和值标签已启用，类别过多时会做可读性抽样或 Other 聚合，正负值柱状图使用零基线，质量代理分数、数值覆盖率和质量门禁状态可进入前端与日志页展示。

同日追加生成 `docs/milestone2-quality-gallery-report.md`，其中包含 4 张图表质量样例 PNG 和 contact sheet，可作为人工审美复核入口。

2026 年 6 月 5 日追加 `docs/milestone2-chart-diversity-report.md`，覆盖趋势、构成、对比、相关和分布五类意图。该报告验证完整 Pipeline 可分别生成 line、pie、bar、scatter、histogram 五类图表，并补齐文本演示模式中的年份标签、区间标签和双指标相关性解析质量。

仍待补充：

- 更细的人工图表审美检查，如颜色对比、图例可读性和真实业务数据中的多系列拥挤情况。
- 针对真实业务数据集的多系列图表视觉验收。
