# 前端使用说明与风格控制文档

## 1. 启动方式

后端：

```bash
python app.py
```

前端：

```bash
cd frontend
npm install
npm run dev
```

默认前端地址为 `http://127.0.0.1:5173`，后端地址为 `http://127.0.0.1:8000`。

## 2. PPT 模式操作流程

1. 登录系统或使用默认账号进入工作台；
2. 上传 `.pptx` 文件；
3. 选择当前处理页码，系统会生成当前页预览；
4. 选择语义分析模式、图表类型修正、图表主题、配图风格和配图模型；
5. 点击生成按钮，等待 Pipeline 完成；
6. 查看图表预览、图表质量、配图预览、配图质量状态、CLIP 匹配分数、日志和增强版 PPT 下载入口；
7. 如需批量处理，切换到批量页码范围并执行批量生成；
8. 批量完成后，在“批量逐页查看”区域通过页码按钮、上一页、下一页查看每一页的图表、配图、质量字段和 Pipeline 日志；
9. 在“位置微调”区域使用滑杆调整当前页图表和配图的 X / Y 位置与缩放，主画布会实时显示 16:9 预览；
10. 点击“导出微调版 PPT”，系统会把当前批量结果和每页微调参数写回为新的 PPTX，并提供“下载微调版”入口。

批量位置微调会保留自动增强版 PPT，同时额外生成一份手动布局版 PPT，便于对重点页做人工落点确认。

## 3. 文本演示模式

文本演示模式适合快速验证语义识别和图表生成。示例输入：

```text
营收: 120
成本: 80
利润: 40
```

系统会直接生成图表 PNG、配图 PNG、日志和阶段状态。

## 4. 图表主题

当前支持四类图表主题：

| 主题 | 用途 |
|---|---|
| Tech | 深色科技风，适合技术汇报和系统演示 |
| Business | 商务汇报风，适合经营分析和阶段总结 |
| Minimal | 简洁中性风，适合轻量展示 |
| Academic | 学术报告风，适合课程和研究汇报 |

## 5. 配图风格

当前支持七类配图风格：

| 风格 | 用途 |
|---|---|
| Auto | 根据内容自动选择 |
| Business | 商务办公、增长、经营场景 |
| Tech | 技术、产品、数据系统场景 |
| Education | 教学、培训、学习场景 |
| Medical | 医疗、健康、可信场景 |
| Academic | 理性、研究、信息表达场景 |
| Sketch | 轻量手绘表达 |

## 6. 配图模型

| 模型 | 说明 |
|---|---|
| Local Preview | 不调用外部 API，使用本地可控预览图 |
| Flux | 调用 Flux 分支生成高质量配图 |
| Wanx | 调用通义万相分支生成配图 |

当外部模型不可用时，系统会自动回退到 Local Preview，避免中断完整流程。

## 7. 图表质量

工作台会在 Pipeline 摘要、Pipeline 详情页和日志详情页展示图表质量字段：

| 字段 | 含义 |
|---|---|
| 图表质量 | `chart_spec.quality_score`，满分 10 |
| 覆盖率 | `chart_spec.quality_checks.numeric_coverage`，有效数值覆盖率 |
| 数据点 | 实际渲染的数据点数量 |
| 系列数 | 实际渲染的数值系列数量 |
| 可读性 | `full` 或 `sampled`，表示是否因类别过多做了抽样 |
| 质量门禁 | `pass`、`attention`、`review` 或 `fallback` |
| 复核原因 | `review_reason`，说明为什么通过、需留意或需要复核 |

当图表出现长类别、正负值柱状图、饼图类别过多等场景时，Pipeline 详情会通过 warnings 或 render notes 提供质量依据。

## 8. 配图质量与重生成状态

工作台会在总览、配图详情页和 Pipeline 日志页展示配图质量状态：

| 状态 | 含义 |
|---|---|
| 待生成 | 尚无配图评分结果 |
| 通过 | 最终配图代理分数达到阈值 |
| 已重生成 | 初始分低于阈值，系统已使用 refined prompt 重生成 |
| 待复核 | 最终分仍低于阈值，需要人工检查或重新生成 |

前端展示字段包括：

- 初始分：`initial_clip_score`
- 最终分：`clip_score`
- 阈值：`score_threshold`
- 分数提升
- 重生成动作：如 `local_refined_prompt`
- 重生成次数
- 重生成原因
- 评分组件：`quality_components`
- 本地渲染特征：`local_render_features`
- 构图变体：`composition_variant`

`local_render_features` 用于说明本地预览图是否包含清晰主体、留白、无图表元素、行业风格元素、主题对象和构图变体，例如 `business_growth_milestones`、`business_regional_network`、`business_product_showroom`、`business_marketing_studio`、`tech_device_cloud`、`medical_care_symbol`、`layout_variant_spotlight`。批量生成时，系统会按页码和内容稳定选择 `duo_panel`、`full_scene`、`spotlight`、`diagonal_workshop` 等构图，并按页面语义生成不同视觉主题，降低相邻页配图同质化。

## 9. 质量样例 Gallery

当前质量样例报告位于：

```text
docs/milestone2-quality-gallery-report.md
docs/milestone2-chart-diversity-report.md
docs/milestone2-illustration-diversity-report.md
```

样例图片位于：

```text
docs/quality-gallery/
```

其中 `chart-contact-sheet.png` 汇总图表质量样例，`chart-diversity-contact-sheet.png` 汇总趋势、构成、对比、相关、分布五类图表多样性样例，`illustration-contact-sheet.png` 汇总配图风格样例，`illustration-diversity-contact-sheet.png` 汇总增长、区域、产品、营销四类商务页的去同质化样例，可用于人工验收时快速浏览质量升级效果。

## 10. 日志与历史记录

日志页展示最近处理任务，包括页码、语义模式、图表类型、配图风格、模型、状态和输出路径。该页面用于检查运行状态、回溯错误和准备演示说明。

选择左侧历史任务后，右侧详情区会读取任务详情接口并展示：

- 图表质量、覆盖率和可读性；
- 配图评分、低分重生成状态和重生成原因；
- 配图评分组件和本地渲染特征；
- PPT 写回版式诊断，包括写回模式、重叠分数、原页是否保留；
- Pipeline 阶段记录；
- Pipeline 运行日志。

当前工作台的 Pipeline 日志页展示本次生成详情；日志页用于回看历史任务详情。

## 11. 逐页解析面板

上传 PPT 后，工作台的逐页解析面板会展示每页的解析摘要，帮助选择需要增强的目标页。

页面类型包括：

| 类型 | 含义 |
|---|---|
| 空页 | 未提取到文本、表格或图片，通常不建议处理 |
| 表格页 | 页面含表格或文本推断表格，适合生成图表 |
| 图片页 | 页面以图片内容为主，适合人工复核是否需要增强 |
| 文本页 | 页面主要包含文本块，系统会尝试从文本中识别数据 |
| 待复核 | 页面元素不足或结构特殊，需要人工判断 |

面板还会显示图片数、占位符数、文本块数、表格数和元素数。如果出现“文本推断表格”标签，说明系统从文本内容中识别到了可用于图表生成的数据。
