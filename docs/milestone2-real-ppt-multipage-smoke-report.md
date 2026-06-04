# Milestone 2 真实 PPT 多页 Smoke 报告

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

验证日期：2026 年 6 月 3 日

补充验证日期：2026 年 6 月 4 日

关联 WBS：`M2.2`、`M2.3`、`M2.10`

样例登记：`docs/milestone2-real-ppt-sample-register.md`

## 1. 验证目标

本次验证在第 1 页 smoke 的基础上继续推进，目标是覆盖 Milestone 2 中“至少 30 页真实 PPT 页面完成解析和预览验证”的数量要求。每份真实 PPT 选择 3 个代表页：

- 第 1 页
- 中间页
- 最后一页

共 10 份 PPT、30 个真实页面。

## 2. 验证环境与命令

环境变量：

```bash
DATABASE_PATH=/private/tmp/milestone2-real-ppt-multipage.db
ENABLE_QWEN_API=0
```

说明：

- 使用临时 SQLite 数据库，避免污染项目默认 `data/app.db`。
- 使用 `semantic_mode=local` 和 `image_model=local`，确保验证结果不受外部 API 波动影响。
- 使用 `process_local_ppt_batch` 对每份 PPT 的代表页批量处理，并输出同一个增强版 PPT。

核心命令：

```bash
DATABASE_PATH=/private/tmp/milestone2-real-ppt-multipage.db ENABLE_QWEN_API=0 ./.venv/bin/python -c 'from backend.database import init_db; from backend.services import process_local_ppt_batch; init_db(); ...'
```

## 3. 验证结果

| 编号 | 文件名 | 总页数 | 处理页码 | 处理页数 | 状态 | 平均 CLIP 代理分数 | 批量增强版 PPT |
|---|---|---:|---|---:|---|---:|---|
| RPPT-01 | `0920-十一安全教育.pptx` | 11 | `1,6,11` | 3 | PASS | 6.40 | `outputs/0920-十一安全教育_batch_enhanced.pptx` |
| RPPT-02 | `18 手绘卡通风格医疗行业专用.pptx` | 32 | `1,16,32` | 3 | PASS | 6.40 | `outputs/18 手绘卡通风格医疗行业专用_batch_enhanced.pptx` |
| RPPT-03 | `19 创意放黑板粉笔风格教师教课教学设计.pptx` | 33 | `1,17,33` | 3 | PASS | 6.40 | `outputs/19 创意放黑板粉笔风格教师教课教学设计_batch_enhanced.pptx` |
| RPPT-04 | `2.4 GenAI&LLM Measure.pptx` | 11 | `1,6,11` | 3 | PASS | 6.40 | `outputs/2.4 GenAI&LLM Measure_batch_enhanced.pptx` |
| RPPT-05 | `2252709 杨烜赫 2253715 陈甫彬 Speech-Recognition-project-slide.pptx` | 24 | `1,12,24` | 3 | PASS | 6.40 | `outputs/2252709 杨烜赫 2253715 陈甫彬 Speech-Recognition-project-slide_batch_enhanced.pptx` |
| RPPT-06 | `24w3407组汇报ppt.pptx` | 9 | `1,5,9` | 3 | PASS | 6.40 | `outputs/24w3407组汇报ppt_batch_enhanced.pptx` |
| RPPT-07 | `AutoTestDesignAI.pptx` | 12 | `1,6,12` | 3 | PASS | 6.40 | `outputs/AutoTestDesignAI_batch_enhanced.pptx` |
| RPPT-08 | `HCI项目报道 (4).pptx` | 14 | `1,7,14` | 3 | PASS | 6.40 | `outputs/HCI项目报道 (4)_batch_enhanced.pptx` |
| RPPT-09 | `ML history.pptx` | 13 | `1,7,13` | 3 | PASS | 6.40 | `outputs/ML history_batch_enhanced.pptx` |
| RPPT-10 | `【13】黑白极简风工作总结汇报通用PPT模板.pptx` | 14 | `1,7,14` | 3 | PASS | 6.40 | `outputs/【13】黑白极简风工作总结汇报通用PPT模板_batch_enhanced.pptx` |

## 4. 指标汇总

| 指标 | 数值 |
|---|---:|
| 真实 PPT 样例数 | 10 |
| 真实页面验证数 | 30 |
| 成功处理页面数 | 30 |
| 失败页面数 | 0 |
| 多页 smoke 成功率 | 100% |
| 批量增强版 PPT 输出数 | 10 |
| 平均 CLIP 代理分数 | 6.40 |

## 5. 写回模式补充复测

为配合 `M2.3` 版式优化，已在 2026 年 6 月 4 日重新执行 10 份真实 PPT、30 个代表页的批量处理与结构化检查。

复测命令：

```bash
PYTHONPATH=/Users/mac/Documents/PPT-Smart-Chart-Generator DATABASE_PATH=/private/tmp/milestone2-real-ppt-multipage-v4.db ENABLE_QWEN_API=0 ./.venv/bin/python /private/tmp/milestone2_reverify.py
```

复测结果：

| 指标 | 数值 |
|---|---:|
| 真实 PPT 样例数 | 10 |
| 真实页面验证数 | 30 |
| 成功处理页面数 | 30 |
| 内联写回页面 | 23 |
| 附加结果页页面 | 7 |
| 附加结果页保留原始目标页 | 7/7 |
| 新增图表/配图图片数符合预期 | 30/30 |
| 新增图片均在页面边界内 | 30/30 |
| 新增图表和新增配图互不重叠 | 30/30 |

本轮复测确认：对结构化重叠风险较高的页面，系统会自动追加增强结果页，保留原始页面；对低风险页面，继续内联写回图表和配图。

## 6. 当前结论

- `M2.2` 已获得 30 个真实页面解析与处理通过证据。
- `M2.3` 已获得 10 份真实 PPT 的多页批量增强版输出证据。
- `M2.10` 已获得 10 份真实样例和 30 页真实页面的小批量 smoke 验证证据。

## 7. 待补验证

本次验证证明端到端链路可运行，但还不足以直接声明版式质量完全达标。下一步仍需补充：

- 人工打开增强版 PPT，检查图表和配图是否遮挡正文、标题、页脚或重要图片。
- 对含表格页做专项检查，确认写回位置是否符合“替换原表格区域”目标。
- 如需证明线上效果，追加 Qwen、WANX、Flux 真实调用路径验证。
