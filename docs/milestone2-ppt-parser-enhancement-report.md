# Milestone 2 PPT 解析增强报告

编制日期：2026 年 6 月 4 日

对应 WBS：`M2.2 PPT 解析增强`

## 1. 目标

围绕 Word 版 WBS 中 `M2.2` 的要求，本轮增强聚焦 PPT 页面解析的边界场景可观测性，包括空页、图片页、占位符、多文本块页面和文本型数据识别。目标是在不改变现有主流程输入输出的前提下，让后端、前端日志页和后续评测可以追踪更明确的页面元素信息。

## 2. 本轮增强

### 2.1 页面诊断字段

`backend/ppt_parser.py` 的 `ParsedSlideContent` 增加 `diagnostics` 字段，主要包含：

- `shape_count`：页面形状总数。
- `text_shape_count`：带文本框能力的形状数。
- `non_empty_text_shape_count`：实际包含文本的形状数。
- `table_count`：解析后的表格数量，包括文本推断表格。
- `picture_count`：图片形状数量。
- `placeholder_count`：占位符数量。
- `empty_shape_count`：无文本、无表格、非图片的空形状数量。
- `has_inferred_table`：是否由文本块推断出表格。
- `is_empty`：是否为空内容页。
- `text_order`：按页面坐标排序后的文本形状索引。

### 2.2 形状描述增强

`describe_shape` 在保留原字段的基础上增加：

- `has_picture`
- `is_placeholder`
- `placeholder_type`
- `text_preview`

这些字段用于后续判断图片占位、空页、复杂版式和人工复核范围。

### 2.3 文本读取顺序优化

过去 `text_content` 主要按 shape 插入顺序拼接。本轮改为按页面坐标 `(top, left, index)` 排序，更接近真实阅读顺序，适合处理多栏文本和模板中乱序插入的文本框。

### 2.4 Outline 输出增强

`parse_presentation_outline` 的每页摘要增加：

- `picture_count`
- `placeholder_count`
- `is_empty`
- `diagnostics`

因此 `/api/parse-slides` 和前端上传后的页列表可以直接获得页面诊断信息。

### 2.5 前端页列表诊断展示

`frontend/src/components/SlideOutlinePanel.vue` 已接入 outline 诊断字段。上传 PPT 后，逐页解析面板会显示：

- 页面类型：空页、表格页、图片页、文本页或待复核。
- 诊断标签：图片数量、占位符数量、文本块数量、文本推断表格。
- 指标摘要：表格、图片、文本块和元素数量。

用户在选择处理页之前即可快速避开空页，定位表格页或图片页。

## 3. 验证结果

### 3.1 后端单测

命令：

```bash
./.venv/bin/python -m unittest tests.test_pipeline
```

结果：

```text
Ran 38 tests in 0.870s
OK
```

新增覆盖：

- 空白 PPT 页会被标记为 `is_empty=true`。
- 图片页会统计 `picture_count=1`，且不会被误判为空页。
- 多文本块页面会按空间坐标输出 `text_content`。
- Presentation outline 会携带 `diagnostics`、`picture_count` 和 `is_empty`。
- 直接调用 service 的冷启动数据库路径会自动初始化基础表并记录任务。

### 3.2 50 页端到端烟测

命令：

```bash
DATABASE_PATH=/private/tmp/m2-parser-smoke.db ./.venv/bin/python tools/run_50_slide_smoke.py
```

结果：

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

说明：本次烟测使用临时 SQLite 路径，验证解析增强和数据库冷启动修复不会中断批量 PPT 主流程。

### 3.3 前端构建

命令：

```bash
cd frontend
npm run build
```

结果：

```text
39 modules transformed
built in 407ms
```

说明：逐页解析诊断展示已通过 Vite 生产构建验证。

## 4. 验收对应关系

| WBS 要求 | 当前证据 |
|---|---|
| 增强复杂表格解析 | 既有合并单元格解析单测仍通过；`cell_matrix` 和 `merge_hints` 保持可用。 |
| 改进文本型数据识别 | 文本块空间排序后再进入 `infer_table_from_text_blocks`，减少多栏乱序导致的推断偏差。 |
| 处理空页 | 新增 `is_empty`、`empty_shape_count` 及空页单测。 |
| 处理图片占位 | 新增 `has_picture`、`picture_count`、`is_placeholder`、`placeholder_type`。 |
| 处理复杂多栏文本 | 新增按页面坐标排序的 `text_order` 和空间阅读顺序单测。 |
| 页面元素信息可被前端使用 | 逐页解析面板已显示页面类型、诊断标签和指标摘要。 |

## 5. 后续待验证

- 对包含 SmartArt、组合形状和母版占位符的 PPT 做补充测试。
