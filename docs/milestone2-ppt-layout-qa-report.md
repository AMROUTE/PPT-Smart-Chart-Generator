# Milestone 2 PPT 写回版式 QA 报告

项目名称：语义驱动的 PPT 智能图表生成与多模态配图系统

验证日期：2026 年 6 月 3 日

补充验证日期：2026 年 6 月 4 日

关联 WBS：`M2.3`

输入报告：`docs/milestone2-real-ppt-multipage-smoke-report.md`

## 1. QA 目标

本次 QA 用于检查 10 份真实 PPT 的多页批量增强版输出是否具备基础版式可用性。由于当前环境缺少 `soffice` / `libreoffice` 和 `pdftoppm`，无法将 PPTX 渲染成页面图片做像素级视觉检查，因此本轮采用 `python-pptx` 做结构化版式检查。

检查范围：

- 10 份真实 PPT
- 每份 3 个代表页：第 1 页、中间页、最后一页
- 合计 30 个真实页面

## 2. 检查方法

对每个处理页执行以下结构化检查：

1. 比较原始 PPT 与增强版 PPT 的图片数量。
2. 确认每个处理页新增至少 2 张图片，即图表 PNG 和配图 PNG。
3. 检查新增图片是否在页面边界内。
4. 检查新增图表与新增配图之间是否互相重叠。
5. 进一步检查新增图片与原始文本框、原始图片的重叠风险。

## 3. 结构化检查结果

### 3.1 初始写回策略

| 检查项 | 结果 |
|---|---|
| 检查页面数 | 30 |
| 新增图表/配图图片数符合预期 | 30/30 PASS |
| 新增图片均在页面边界内 | 30/30 PASS |
| 新增图表和新增配图互不重叠 | 30/30 PASS |
| 新增图片与原始内容无重叠风险 | 1/30 LOW，29/30 REVIEW |

### 3.2 低重叠区域选择策略复测

已在 `backend/insert_to_pptx.py` 增加低重叠写回区域选择策略：

- 表格页仍优先使用表格区域作为图表区域。
- 无表格锚点时，从多个候选布局中选择与原始文本、图片、表格重叠分数最低的布局。
- 配图区域会避开图表区域，避免新增图表与新增配图互相覆盖。

复测命令：

```bash
./.venv/bin/python -m unittest tests.test_pipeline
DATABASE_PATH=/private/tmp/milestone2-real-ppt-multipage-v2.db ENABLE_QWEN_API=0 ./.venv/bin/python -c 'from backend.services import process_local_ppt_batch; ...'
```

复测结果：

| 检查项 | 结果 |
|---|---|
| 后端单元测试 | PASS，25 tests OK |
| 真实 PPT 多页 smoke | 10/10 份 PASS，30/30 页 completed |
| 新增图表/配图图片数符合预期 | 30/30 PASS |
| 新增图片均在页面边界内 | 30/30 PASS |
| 新增图表和新增配图互不重叠 | 30/30 PASS |
| 新增图片与原始内容无重叠风险 | 2/30 LOW，28/30 REVIEW |

### 3.3 网格候选搜索与布局诊断复测

在低重叠策略基础上继续增强：

- 将无表格页的候选布局从 4 组固定位置扩展为多尺寸、多位置网格搜索。
- 保留表格锚点优先策略。
- 在 Pipeline 输出的 `intent.layout` 中记录图表区域、配图区域、重叠分数、是否建议版式复核。
- 当 `layout_warning=true` 时，在 Pipeline 日志中追加 warning。

复测命令：

```bash
./.venv/bin/python -m unittest tests.test_pipeline
DATABASE_PATH=/private/tmp/milestone2-real-ppt-multipage-v3.db ENABLE_QWEN_API=0 ./.venv/bin/python -c 'from backend.services import process_local_ppt_batch; ...'
```

复测结果：

| 检查项 | 结果 |
|---|---|
| 后端单元测试 | PASS，25 tests OK |
| 真实 PPT 多页 smoke | 10/10 份 PASS，30/30 页 completed |
| 新增图表/配图图片数符合预期 | 30/30 PASS |
| 新增图片均在页面边界内 | 30/30 PASS |
| 新增图表和新增配图互不重叠 | 30/30 PASS |
| 新增图片与原始内容无重叠风险 | 2/30 LOW，28/30 REVIEW |
| 原始内容重叠命中数 | 113 |

真实样例单页检查确认 Pipeline 会返回布局诊断字段：

```text
intent.layout = {
  "chart_region": {...},
  "illustration_region": {...},
  "overlap_score": 0.0532,
  "layout_warning": false,
  "pair_overlap": 0
}
```

### 3.4 高风险页面附加结果页策略复测

在网格候选搜索与布局诊断基础上继续增强：

- 当 `intent.layout.layout_warning=true` 时，不再强行覆盖原始目标页。
- 系统会追加一页“增强结果页”，在新页面中放置图表、配图、标题、摘要和说明。
- 原始目标页保持不变，避免复杂模板、图片密集页、文本密集页被新增资产遮挡。
- 追加页面不再假设模板一定包含第 7 个空白版式；当模板版式数量不足时，自动选择最后一个可用版式并清空占位元素。

复测命令：

```bash
./.venv/bin/python -m unittest tests.test_pipeline
PYTHONPATH=/Users/mac/Documents/PPT-Smart-Chart-Generator DATABASE_PATH=/private/tmp/milestone2-real-ppt-multipage-v4.db ENABLE_QWEN_API=0 ./.venv/bin/python /private/tmp/milestone2_reverify.py
```

复测结果：

| 检查项 | 结果 |
|---|---|
| 后端单元测试 | PASS，26 tests OK |
| 真实 PPT 多页 smoke | 10/10 份 PASS，30/30 页 completed |
| 内联写回页面 | 23/30 |
| 附加结果页页面 | 7/30 |
| 附加结果页保留原始目标页 | 7/7 PASS |
| 新增图表/配图图片数符合预期 | 30/30 PASS |
| 新增图片均在页面边界内 | 30/30 PASS |
| 新增图表和新增配图互不重叠 | 30/30 PASS |
| 模板版式索引兼容性 | RPPT-06 PASS，无 `slide layout index out of range` fallback |

本轮结构化 QA 结果说明，高风险页面已经从“可能遮挡原始内容”转为“保留原页并追加结果页”。因此 M2.3 的自动写回策略已具备更稳妥的验收证据，但仍需补充人工打开 PPT 或渲染截图级检查。

### 3.5 真实 PPT 版式预复核

为避免只依赖全文件图片总数造成误判，已补充 `tools/run_m2_layout_prefill.py`，按“处理页新增资产 + 附加结果页图片”的口径复核 10 份真实 PPT 批量增强版输出。

复测命令：

```bash
./.venv/bin/python tools/run_m2_layout_prefill.py
```

复测结果：

| 检查项 | 结果 |
|---|---|
| 真实 PPT 样例 | 10/10 份 PASS |
| 批量增强版 PPT 可打开 | 10/10 PASS |
| 代表处理页新增资产达到预期 | 10/10 PASS |
| 附加结果页图片边界 | PASS |
| 附加结果页图片间重叠 | PASS |
| 输出报告 | `docs/milestone2-layout-prefill-report.md` |

说明：该预复核能证明结构化写回结果满足基础资产与边界要求，但仍不能替代人工打开 PPT 或渲染截图级视觉验收。

## 4. 主要发现

### 4.1 已通过项

- 所有 30 个真实页面均成功写入新增图片。
- 每个处理页相较原始页面都新增 2 张图片。
- 新增图表和新增配图均在页面边界内，没有越界。
- 新增图表和新增配图之间没有互相覆盖。
- 每份 PPT 都生成了批量增强版 PPT 文件。

### 4.2 待改进项

结构化重叠检查显示，网格候选搜索上线后，仍有 28/30 个页面的新增图片与原始文本框或原始图片存在重叠风险。补充上线“附加结果页”策略后，这类高风险页面不再强行写入原页，而是追加独立结果页，保留原始目标页内容。

典型风险包括：

- 内联写回页仍需要人工确认是否达到“美观”标准。
- 附加结果页需要人工确认标题、摘要、图表和配图的整体呈现是否符合汇报要求。
- 当前结构化 QA 只能证明边界、图片数量、图片间不重叠和原页保留，无法替代渲染截图级视觉检查。

## 5. 当前结论

`M2.3` 当前状态应保持为 `进行中`，暂不标记为 `已完成`。

已有证据证明：

- 图表和配图可以稳定写入目标页。
- 多页批量输出可以写回同一个增强版 PPT。
- 新增图表和新增配图之间不存在内部重叠。
- 新增低重叠布局选择策略和网格候选搜索后，真实样例多页 smoke 仍保持 30/30 通过。
- Pipeline 已能输出 `intent.layout` 诊断字段，用于标记需要人工复核的页面。
- 高风险页面可以自动转为附加结果页，原始目标页保持不变。
- 真实样例中 7 个附加结果页均通过结构化检查。
- 10 份真实 PPT 的批量增强版输出通过版式预复核，处理页新增资产和附加页边界检查均达到预期。

仍缺少的验收证据：

- 图表和配图在人工视觉检查中不明显遮挡原始核心内容。
- 对含表格页可以优先替换原表格区域，并在人工检查中确认版式合理。
- 对复杂模板页面可以选择低风险写回区域，或使用附加结果页且视觉呈现合理。
- 至少一轮人工或渲染图像级版式检查通过。

## 6. 后续修复建议

建议把 `M2.3` 的后续实现拆成两步：

1. 继续增强写回区域选择策略。
   - 对图片密集或文本密集页面，优先使用当前“附加结果页”模式，避免破坏原始页面。
   - 对低风险页面继续使用内联写回，并保留 `layout_warning` 诊断字段。
   - 后续可补充更细的冲突对象列表，帮助人工快速定位风险。

2. 继续完善自动版式 QA 输出。
   - 当前已在 Pipeline 返回中记录新增图表和配图的 bounding box。
   - 当前已记录重叠分数和 `layout_warning`。
   - 后续可进一步记录具体冲突对象列表，便于前端或报告展示。

## 7. 渲染工具缺口

当前本地环境缺少：

- `soffice` / `libreoffice`
- `pdftoppm`

因此无法完成 PPTX -> PDF -> PNG 的视觉渲染检查。后续如果安装 LibreOffice 和 Poppler，可补充像素级页面截图检查。
