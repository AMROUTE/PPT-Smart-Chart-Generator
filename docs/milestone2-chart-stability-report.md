# Milestone 2 图表生成稳定性验证报告

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

验证日期：2026 年 6 月 4 日

关联 WBS：`M2.5`、`M2.10`

## 1. 验证目标

本轮用于推进 `M2.5 图表生成稳定性优化`：

- 确认 8 类图表类型均能生成 PNG。
- 处理空数据、缺失值、非法数值、单数值列等异常场景。
- 图表生成器自身具备 placeholder fallback，不完全依赖 Pipeline 外层异常兜底。
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
| 后端单元测试 | PASS，34 tests OK |
| 8 类图表生成测试 | PASS，`bar`、`line`、`pie`、`scatter`、`area`、`histogram`、`box`、`heatmap` |
| 空数据 placeholder | PASS |
| 缺失值 / 非法值处理 | PASS |
| Scatter / Heatmap 数值列不足补足 | PASS |
| Pie 非正值安全处理 | PASS |
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

仍待补充：

- 更细的人工图表审美检查，如标签拥挤、颜色对比、图例可读性。
- 针对真实业务数据集的多系列图表视觉验收。
