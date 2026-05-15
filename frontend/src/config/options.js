export const semanticModeOptions = [
  { value: "local", label: "本地规则", hint: "速度更快，适合日常调试" },
  { value: "qwen", label: "千问 API", hint: "语义理解更强，依赖外部模型" },
];

export const chartTypeOptions = [
  { value: "auto", label: "自动推荐", hint: "根据语义自动判断图表类型" },
  { value: "bar", label: "柱状图", hint: "适合对比不同类别" },
  { value: "line", label: "折线图", hint: "适合趋势变化" },
  { value: "pie", label: "饼图", hint: "适合占比展示" },
  { value: "scatter", label: "散点图", hint: "适合相关性观察" },
  { value: "area", label: "面积图", hint: "适合累计趋势" },
  { value: "histogram", label: "直方图", hint: "适合分布展示" },
  { value: "box", label: "箱线图", hint: "适合离散度分析" },
  { value: "heatmap", label: "热力图", hint: "适合密度与矩阵关系" },
];

export const illustrationStyleOptions = [
  { value: "auto", label: "自动", hint: "根据内容自动匹配视觉方向" },
  { value: "business", label: "商务风", hint: "偏正式、汇报与增长场景" },
  { value: "tech", label: "科技风", hint: "偏未来感、产品与数据场景" },
  { value: "education", label: "教育风", hint: "偏讲解式、清晰层次" },
  { value: "medical", label: "医疗风", hint: "偏干净、可信和柔和" },
  { value: "academic", label: "学术风", hint: "偏理性、信息表达优先" },
  { value: "sketch", label: "手绘风", hint: "偏轻松、草图式表达" },
];

export const imageModelOptions = [
  { value: "local", label: "本地预览", hint: "仅做本地预览，不调用外部接口" },
  { value: "flux", label: "Flux", hint: "更偏高质感图像生成" },
  { value: "wanx", label: "通义万相", hint: "阿里系图像生成模型" },
];
