# Milestone 2 真实 PPT 端到端 Smoke 报告

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

验证日期：2026 年 6 月 3 日

关联 WBS：`M2.2`、`M2.3`、`M2.10`

样例登记：`docs/milestone2-real-ppt-sample-register.md`

## 1. 验证目标

本次 smoke 验证用于确认 10 份真实 PPT 样例至少可以完成第 1 页端到端处理：

1. PPT 文件可读取。
2. 第 1 页可解析。
3. 本地语义模式可生成图表。
4. 本地配图模式可生成配图。
5. 系统可输出增强版 PPT。

本次验证不替代人工版式验收；遮挡、错位、重叠等视觉问题仍需后续人工检查。

## 2. 验证环境与命令

环境变量：

```bash
DATABASE_PATH=/private/tmp/milestone2-real-ppt-smoke.db
ENABLE_QWEN_API=0
```

说明：

- 本次使用临时 SQLite 数据库，避免污染项目默认 `data/app.db`。
- 本次使用 `semantic_mode=local` 和 `image_model=local`，避免外部 API 波动影响真实样例基线。
- 首轮运行因临时数据库未初始化失败，错误为 `OperationalError: no such table: processing_jobs`；调用 `init_db()` 后重跑通过。该问题属于验证脚本环境初始化问题，不是 PPT 解析链路失败。

核心命令：

```bash
DATABASE_PATH=/private/tmp/milestone2-real-ppt-smoke.db ENABLE_QWEN_API=0 ./.venv/bin/python -c 'from backend.database import init_db; from backend.services import process_local_ppt; init_db(); ...'
```

## 3. 验证结果

| 编号 | 文件名 | 状态 | 图表输出 | 配图输出 | 增强版 PPT | CLIP 代理分数 |
|---|---|---|---|---|---|---:|
| RPPT-01 | `0920-十一安全教育.pptx` | PASS | `outputs/ppt-e9b790dd49_chart_slide_1.png` | `outputs/ppt-e9b790dd49_illustration_slide_1.png` | `outputs/0920-十一安全教育_enhanced.pptx` | 6.4 |
| RPPT-02 | `18 手绘卡通风格医疗行业专用.pptx` | PASS | `outputs/ppt-ec1d97d25e_chart_slide_1.png` | `outputs/ppt-ec1d97d25e_illustration_slide_1.png` | `outputs/18 手绘卡通风格医疗行业专用_enhanced.pptx` | 6.4 |
| RPPT-03 | `19 创意放黑板粉笔风格教师教课教学设计.pptx` | PASS | `outputs/ppt-e4b1b027b0_chart_slide_1.png` | `outputs/ppt-e4b1b027b0_illustration_slide_1.png` | `outputs/19 创意放黑板粉笔风格教师教课教学设计_enhanced.pptx` | 6.4 |
| RPPT-04 | `2.4 GenAI&LLM Measure.pptx` | PASS | `outputs/ppt-a760d69fd2_chart_slide_1.png` | `outputs/ppt-a760d69fd2_illustration_slide_1.png` | `outputs/2.4 GenAI&LLM Measure_enhanced.pptx` | 6.4 |
| RPPT-05 | `2252709 杨烜赫 2253715 陈甫彬 Speech-Recognition-project-slide.pptx` | PASS | `outputs/ppt-532c2e13b6_chart_slide_1.png` | `outputs/ppt-532c2e13b6_illustration_slide_1.png` | `outputs/2252709 杨烜赫 2253715 陈甫彬 Speech-Recognition-project-slide_enhanced.pptx` | 6.4 |
| RPPT-06 | `24w3407组汇报ppt.pptx` | PASS | `outputs/ppt-c8c5eea59f_chart_slide_1.png` | `outputs/ppt-c8c5eea59f_illustration_slide_1.png` | `outputs/24w3407组汇报ppt_enhanced.pptx` | 6.4 |
| RPPT-07 | `AutoTestDesignAI.pptx` | PASS | `outputs/ppt-7911ade4da_chart_slide_1.png` | `outputs/ppt-7911ade4da_illustration_slide_1.png` | `outputs/AutoTestDesignAI_enhanced.pptx` | 6.4 |
| RPPT-08 | `HCI项目报道 (4).pptx` | PASS | `outputs/ppt-4457a5e756_chart_slide_1.png` | `outputs/ppt-4457a5e756_illustration_slide_1.png` | `outputs/HCI项目报道 (4)_enhanced.pptx` | 6.4 |
| RPPT-09 | `ML history.pptx` | PASS | `outputs/ppt-e5b4a847a1_chart_slide_1.png` | `outputs/ppt-e5b4a847a1_illustration_slide_1.png` | `outputs/ML history_enhanced.pptx` | 6.4 |
| RPPT-10 | `【13】黑白极简风工作总结汇报通用PPT模板.pptx` | PASS | `outputs/ppt-282b17490c_chart_slide_1.png` | `outputs/ppt-282b17490c_illustration_slide_1.png` | `outputs/【13】黑白极简风工作总结汇报通用PPT模板_enhanced.pptx` | 6.4 |

## 4. 指标汇总

| 指标 | 数值 |
|---|---:|
| 样例文件数 | 10 |
| 处理页码 | 第 1 页 |
| 成功数 | 10 |
| 失败数 | 0 |
| 端到端 smoke 成功率 | 100% |
| 平均 CLIP 代理分数 | 6.4 |

## 5. 当前结论

- `M2.2` 获得真实 PPT 第 1 页解析链路通过证据，但复杂页、表格页、图片型表格和 SmartArt 仍需继续验证。
- `M2.3` 获得真实 PPT 增强版输出证据，但版式质量还需人工检查。
- `M2.10` 获得 10 份真实 PPT 样例端到端 smoke 证据，可作为小批量评测体系的起点。

## 6. 待补验证

- 对每份 PPT 选择 2 至 3 个代表页继续处理，覆盖含表格页、图片密集页、目录页和正文页。
- 对生成的 10 份增强版 PPT 做人工版式检查，记录遮挡、错位、重叠和可编辑性。
- 若需要证明线上模型能力，追加 Qwen / WANX / Flux 路径验证。
