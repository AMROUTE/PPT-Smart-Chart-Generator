# Milestone 2 真实 PPT 样例登记表

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

登记日期：2026 年 6 月 3 日

关联 WBS：`M2.2`、`M2.3`、`M2.10`

## 1. 登记目标

本登记表用于支撑 Milestone 2 对“真实 PPT 样例”的验收要求：

- 至少 10 份真实 PPT 样例完成测试。
- 至少 30 页真实 PPT 页面完成解析和预览验证。
- 后续围绕这些样例补充 PPT 解析、图表/配图写回、端到端成功率和人工版式检查证据。

## 2. 样例选择原则

- 排除 `~$` 开头的 Office 临时锁文件。
- 排除系统自动生成的 `enhanced.pptx`，优先使用原始 PPT。
- 覆盖不同主题和版式：安全教育、医疗、教学、AI/LLM、语音识别、项目汇报、HCI、机器学习、工作总结模板。
- 初步使用 `python-pptx` 验证文件可打开，并统计页数、表格、图片、形状和文本框数量。

## 3. 样例清单

| 编号 | 文件名 | 类型/场景 | 页数 | 表格数 | 图片数 | 形状数 | 文本形状数 | 路径 | 当前状态 |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| RPPT-01 | `0920-十一安全教育.pptx` | 安全教育 / 图片较多 | 11 | 0 | 24 | 65 | 25 | `/Users/mac/Downloads/0920-十一安全教育.pptx` | 3 页多页 smoke 通过，待人工版式验收 |
| RPPT-02 | `18 手绘卡通风格医疗行业专用.pptx` | 医疗行业 / 模板页多 | 32 | 0 | 0 | 280 | 137 | `/Users/mac/Downloads/18 手绘卡通风格医疗行业专用/18 手绘卡通风格医疗行业专用.pptx` | 3 页多页 smoke 通过，待人工版式验收 |
| RPPT-03 | `19 创意放黑板粉笔风格教师教课教学设计.pptx` | 教学设计 / 复杂模板 | 33 | 0 | 8 | 584 | 248 | `/Users/mac/Downloads/19 创意放黑板粉笔风格教师教课教学设计/19 创意放黑板粉笔风格教师教课教学设计.pptx` | 3 页多页 smoke 通过，待人工版式验收 |
| RPPT-04 | `2.4 GenAI&LLM Measure.pptx` | GenAI / LLM 技术课件 | 11 | 0 | 19 | 93 | 44 | `/Users/mac/Downloads/2.4 GenAI&LLM Measure.pptx` | 3 页多页 smoke 通过，待人工版式验收 |
| RPPT-05 | `2252709 杨烜赫 2253715 陈甫彬 Speech-Recognition-project-slide.pptx` | 语音识别项目汇报 | 24 | 0 | 15 | 200 | 32 | `/Users/mac/Downloads/2252709 杨烜赫 2253715 陈甫彬 Speech-Recognition-project-slide.pptx` | 3 页多页 smoke 通过，待人工版式验收 |
| RPPT-06 | `24w3407组汇报ppt.pptx` | 小组汇报 / 含表格 | 9 | 1 | 12 | 81 | 42 | `/Users/mac/Downloads/24w3407组汇报ppt.pptx` | 3 页多页 smoke 通过，待人工版式验收 |
| RPPT-07 | `AutoTestDesignAI.pptx` | AI 测试设计 / 图文混排 | 12 | 0 | 27 | 175 | 126 | `/Users/mac/Downloads/AutoTestDesignAI.pptx` | 3 页多页 smoke 通过，待人工版式验收 |
| RPPT-08 | `HCI项目报道 (4).pptx` | HCI 项目报道 / 含表格 | 14 | 1 | 12 | 125 | 58 | `/Users/mac/Downloads/HCI项目报道 (4).pptx` | 3 页多页 smoke 通过，待人工版式验收 |
| RPPT-09 | `ML history.pptx` | 机器学习历史 / 技术内容 | 13 | 0 | 15 | 119 | 46 | `/Users/mac/Downloads/ML history.pptx` | 3 页多页 smoke 通过，待人工版式验收 |
| RPPT-10 | `【13】黑白极简风工作总结汇报通用PPT模板.pptx` | 工作总结模板 / 含表格 | 14 | 3 | 14 | 121 | 54 | `/Users/mac/Downloads/【13】黑白极简风工作总结汇报通用PPT模板.pptx` | 3 页多页 smoke 通过，待人工版式验收 |

## 4. 样例规模

| 指标 | 数值 |
|---|---:|
| 样例文件数 | 10 |
| 总页数 | 173 |
| 总表格数 | 5 |
| 总图片数 | 146 |
| 总形状数 | 1843 |
| 总文本形状数 | 812 |

## 5. 初步验证命令

```bash
./.venv/bin/python -c 'from pptx import Presentation; from pathlib import Path; paths = [...]; ...'
```

初步验证结论：以上 10 份 PPT 均可被 `python-pptx` 打开并读取基础结构信息。

## 6. 后续验收记录字段

后续执行真实样例测试时，每份 PPT 应补充以下字段：

- 选取页码范围
- 解析是否成功
- 图表生成是否成功
- 配图生成是否成功
- 增强版 PPT 是否生成
- 是否存在遮挡、错位、重叠
- 人工版式评分
- 失败原因或修复记录

## 7. 当前结论

本登记表已经满足 Milestone 2 对真实 PPT 样例数量和页数规模的最低要求，并已完成 10 份样例、30 个真实页面的多页端到端 smoke。下一步需要围绕这些样例执行人工版式验收，才能将 `M2.2`、`M2.3`、`M2.10` 从 `待验证` 推进到 `已完成`。
