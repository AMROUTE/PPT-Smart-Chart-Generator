export const semanticModeOptions = [
  { value: "local", label: "Local Rules", hint: "Faster local heuristic analysis" },
  { value: "qwen", label: "Qwen API", hint: "Stronger semantic understanding" },
];

export const chartTypeOptions = [
  { value: "auto", label: "Auto", hint: "Automatically choose a chart type" },
  { value: "bar", label: "Bar", hint: "Best for comparing categories" },
  { value: "line", label: "Line", hint: "Best for trend changes" },
  { value: "pie", label: "Pie", hint: "Best for composition and share" },
  { value: "scatter", label: "Scatter", hint: "Best for correlation" },
  { value: "area", label: "Area", hint: "Best for cumulative trends" },
  { value: "histogram", label: "Histogram", hint: "Best for distribution" },
  { value: "box", label: "Box", hint: "Best for spread analysis" },
  { value: "heatmap", label: "Heatmap", hint: "Best for matrix intensity" },
];

export const chartThemeOptions = [
  { value: "tech", label: "Tech", hint: "Dark blue high-contrast dashboard style" },
  { value: "business", label: "Business", hint: "Clean executive presentation style" },
  { value: "minimal", label: "Minimal", hint: "Simple neutral visual style" },
  { value: "academic", label: "Academic", hint: "Soft research presentation style" },
];

export const illustrationStyleOptions = [
  { value: "auto", label: "Auto", hint: "Automatically match the content" },
  { value: "business", label: "Business", hint: "Formal reporting and growth scenarios" },
  { value: "tech", label: "Tech", hint: "Future-oriented product and data scenarios" },
  { value: "education", label: "Education", hint: "Clear instructional scenarios" },
  { value: "medical", label: "Medical", hint: "Clean and trustworthy scenes" },
  { value: "academic", label: "Academic", hint: "Rational and information-focused scenes" },
  { value: "sketch", label: "Sketch", hint: "Lightweight hand-drawn expression" },
];

export const imageModelOptions = [
  { value: "local", label: "Local Preview", hint: "Do not call external image APIs" },
  { value: "flux", label: "Flux", hint: "Higher-quality image generation" },
  { value: "wanx", label: "Wanx", hint: "Alibaba Tongyi image generation" },
];
