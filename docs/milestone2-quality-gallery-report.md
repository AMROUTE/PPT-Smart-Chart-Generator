# Milestone 2 图表与配图质量样例 Gallery

验证日期：2026 年 6 月 4 日

关联 WBS：`M2.5`、`M2.6`、`M2.7`、`M2.10`

## 1. 验证目标

本报告用于固化一组可复现的图表与配图质量样例，辅助人工验收图表可读性、异常数据处理、配图风格化和本地 fallback 质量。

## 2. 汇总

| 样例数 | PASS | REVIEW |
|---:|---:|---:|
| 10 | 10 | 0 |

## 3. Contact Sheets

- 图表样例总览：`docs/quality-gallery/chart-contact-sheet.png`
- 配图样例总览：`docs/quality-gallery/illustration-contact-sheet.png`

## 4. 样例明细

| 编号 | 类型 | 风格/图表 | 资产 | 分数 | 尺寸 | KB | 颜色数 | 期望特征 | 记录特征 | Warning | 状态 |
|---|---|---|---|---:|---|---:|---:|---|---|---|---|
| CHART-01 | chart | line / business | `docs/quality-gallery/chart-01-line.png` | 9.42 | 1200x720 | 22.6 | 240 | `value_labels` | `value_labels, axis_ticks, full_dataset_render` | - | PASS |
| CHART-02 | chart | bar / minimal | `docs/quality-gallery/chart-02-bar.png` | 9.42 | 1200x720 | 20.2 | 200 | `zero_baseline` | `value_labels, axis_ticks, full_dataset_render, zero_baseline` | - | PASS |
| CHART-03 | chart | pie / academic | `docs/quality-gallery/chart-03-pie.png` | 9.35 | 1200x720 | 25.2 | 506 | `pie_other_grouped` | `value_labels, axis_ticks, full_dataset_render, pie_other_grouped` | Pie chart grouped 3 small slices into Other to preserve total share. | PASS |
| CHART-04 | chart | bar / tech | `docs/quality-gallery/chart-04-bar.png` | 9.16 | 1200x720 | 30.3 | 631 | `readable_label_sampling` | `value_labels, axis_ticks, readable_label_sampling` | bar chart sampled 10 of 14 records to keep labels readable. | PASS |
| ILL-01 | illustration | business | `docs/quality-gallery/ill-01-business.png` | 7.4 | 1200x700 | 14.7 | 489 | `business_growth_milestones` | `local_scene_preview, 16:9_canvas, clean_negative_space, no_chart_shapes, layout_variant_spotlight, business_growth_milestones, human_subjects, human_subjects` | - | PASS |
| ILL-02 | illustration | tech | `docs/quality-gallery/ill-02-tech.png` | 6.95 | 1200x700 | 13.9 | 455 | `tech_device_cloud` | `local_scene_preview, 16:9_canvas, clean_negative_space, no_chart_shapes, layout_variant_full_scene, tech_device_cloud, human_subjects` | - | PASS |
| ILL-03 | illustration | education | `docs/quality-gallery/ill-03-education.png` | 7.5 | 1200x700 | 13.3 | 490 | `education_board_books` | `local_scene_preview, 16:9_canvas, clean_negative_space, no_chart_shapes, layout_variant_spotlight, education_board_books, human_subjects, human_subjects` | - | PASS |
| ILL-04 | illustration | medical | `docs/quality-gallery/ill-04-medical.png` | 6.95 | 1200x700 | 10.7 | 399 | `medical_care_symbol` | `local_scene_preview, 16:9_canvas, clean_negative_space, no_chart_shapes, layout_variant_duo_panel, human_subjects, medical_care_symbol` | - | PASS |
| ILL-05 | illustration | academic | `docs/quality-gallery/ill-05-academic.png` | 7.5 | 1200x700 | 10.1 | 325 | `academic_papers_library` | `local_scene_preview, 16:9_canvas, clean_negative_space, no_chart_shapes, layout_variant_duo_panel, human_subjects, academic_papers_library` | - | PASS |
| ILL-06 | illustration | sketch | `docs/quality-gallery/ill-06-sketch.png` | 6.95 | 1200x700 | 12.5 | 348 | `sketch_storyboard_lines` | `local_scene_preview, 16:9_canvas, clean_negative_space, no_chart_shapes, layout_variant_spotlight, sketch_storyboard_lines, human_subjects, human_subjects` | - | PASS |

## 5. 当前结论

- 图表样例覆盖趋势、正负值柱状图、饼图 Other 聚合和长类别抽样。
- 配图样例覆盖 business、tech、education、medical、academic、sketch 六类本地风格。
- 每个样例均输出 PNG，并记录可回读的质量字段或本地渲染特征。
- 每个样例都通过尺寸、文件大小和颜色丰富度 sanity check，降低空白图或单色图误入验收材料的风险。
- 该 gallery 是自动化样例证据，仍需结合人工视觉评分表完成最终主观审美验收。
