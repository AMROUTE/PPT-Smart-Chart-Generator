# Milestone 2 基线验证记录

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

验证日期：2026 年 6 月 3 日

关联清单：`docs/milestone2-wbs-checklist.md`

## 1. 验证目标

本次验证用于支撑 Milestone 2 WBS 的起点确认，优先覆盖以下工作包：

- `M2.1`：问题收敛与验收标准确认
- `M2.3`：PPT 写回与版式优化
- `M2.4`：图表推荐质量提升
- `M2.5`：图表生成稳定性优化
- `M2.8`：前端工作台优化
- `M2.10`：测试样例与评测体系
- `M2.11`：部署与环境验证

## 2. 验证环境

| 项目 | 当前值 |
|---|---|
| Python | `Python 3.9.6` |
| Node.js | `v25.9.0` |
| 后端入口 | `backend.app:app` |
| 前端构建工具 | `Vite 5.4.21` |
| 数据库 | SQLite，路径 `data/app.db` |

说明：README 推荐 Python 3.12 和 Node.js 20；本次验证使用当前本地已有环境完成。该环境能通过基线测试，但最终交付前仍建议补一轮推荐版本环境验证。

## 3. 验证结果汇总

| 验证项 | 命令 | 结果 | 关联 WBS |
|---|---|---|---|
| 后端单元测试 | `./.venv/bin/python -m unittest tests.test_pipeline` | PASS，23 tests OK | `M2.5`、`M2.10` |
| 语义识别/配图匹配评估 | `./.venv/bin/python evaluator.py` | PASS，60/60，准确率 100.00%，平均 CLIP 代理分数 7.02 | `M2.4`、`M2.7`、`M2.10` |
| 50 页批量烟测 | `./.venv/bin/python tools/run_50_slide_smoke.py` | PASS，50/50 页完成，输出增强版 PPT | `M2.2`、`M2.3`、`M2.10` |
| 前端生产构建 | `npm run build`，目录 `frontend/` | PASS，39 modules transformed，构建成功 | `M2.8`、`M2.10` |
| 后端健康检查 | `curl http://127.0.0.1:8000/api/health` | PASS，`status=ok`，SQLite、模型配置和功能列表可读 | `M2.9`、`M2.11` |

## 4. 关键输出

### 4.1 后端单元测试

结果：

```text
Ran 23 tests in 0.400s
OK
```

备注：运行时出现 `urllib3` 的 LibreSSL 警告，但不影响测试通过。

### 4.2 语义评估

结果：

```text
总样本数：60
预测正确：60
准确率：100.00%（目标 >= 88%）
平均 CLIP 匹配分数：7.02（目标 >= 6.5）
平均单样本耗时：0.01 ms
PASS
```

输出文件：

- `outputs/evaluation_report.csv`
- `outputs/evaluation_summary.json`
- `outputs/evaluation_summary.md`

备注：本次评估使用 `local` 引擎。脚本提示 LLM parser 不可用并自动回退：

```text
LLM parser unavailable, using local evaluator: cannot import name 'masked' from 'numpy.ma' (unknown location)
```

该回退符合 Milestone 2 的 graceful fallback 方向，但 `M2.4` 若要证明千问路径质量，仍需在完整外部模型环境下追加验证。

### 4.3 50 页批量烟测

结果：

```json
{
  "source_ppt": "outputs/week7_50_slide_smoke_source.pptx",
  "final_pptx_path": "outputs/week7_50_slide_smoke_source_batch_enhanced.pptx",
  "requested_slides": 50,
  "processed_count": 50,
  "completed_count": 50,
  "final_pptx_exists": true,
  "average_clip_score": 6.7,
  "elapsed_seconds": 3.03,
  "pass": true
}
```

输出文件：

- `outputs/week7_50_slide_smoke_source.pptx`
- `outputs/week7_50_slide_smoke_source_batch_enhanced.pptx`
- `outputs/week7_50_slide_smoke_summary.json`

### 4.4 前端构建

结果：

```text
vite v5.4.21 building for production...
✓ 39 modules transformed.
✓ built in 436ms
```

### 4.5 健康检查

结果摘要：

```json
{
  "status": "ok",
  "frontend": "vue",
  "pipeline_engine": "langgraph",
  "qwen_enabled": true,
  "wanx_enabled": true,
  "flux_enabled": true,
  "database_enabled": true,
  "database_engine": "sqlite",
  "database_path": "data/app.db",
  "database_exists": true
}
```

当前数据库统计：

- users：3
- uploads：17
- jobs：120

## 5. 当前结论

- `M2.1` 已具备完成证据：WBS 验收清单已建立，验收标准、状态枚举、证据字段和验证命令已固化。
- `M2.4`、`M2.5`、`M2.8`、`M2.10`、`M2.11` 已获得基线通过证据，但仍需根据 WBS 要求补充真实 PPT 样例、Docker Compose 验证和外部模型路径验证。
- `M2.2` 和 `M2.3` 已有 50 页烟测证据，但复杂真实 PPT、图片型表格、SmartArt 和版式人工验收仍需继续推进。

## 6. 下一步建议

1. 按 `M2.2` 和 `M2.3` 收集或指定 10 份真实 PPT 样例，建立真实样例清单。
2. 对 `outputs/week7_50_slide_smoke_source_batch_enhanced.pptx` 做人工版式检查，记录是否存在遮挡、错位或内容重叠。
3. 按 `M2.11` 再跑一轮 Docker Compose 验证，补齐容器化部署证据。
4. 若有可用 API key，按 `M2.4`、`M2.6` 追加 Qwen、WANX、Flux 真实调用路径验证。
