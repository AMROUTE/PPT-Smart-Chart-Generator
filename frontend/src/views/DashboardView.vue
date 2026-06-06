<script setup>
import { computed, ref, watch } from "vue";

import PipelineStatus from "../components/PipelineStatus.vue";
import SelectMenu from "../components/SelectMenu.vue";
import SlideOutlinePanel from "../components/SlideOutlinePanel.vue";
import UploadDropzone from "../components/UploadDropzone.vue";
import {
  chartTypeOptions,
  chartThemeOptions,
  illustrationStyleOptions,
  imageModelOptions,
  semanticModeOptions,
} from "../config/options";
import { useUserSettings } from "../composables/useUserSettings";
import { requestBatchLayout, requestBatchProcess, requestDemo, requestProcess, requestSlideOutline, requestSlidePreview } from "../services/api";

const { settings } = useUserSettings();

const file = ref(null);
const slideNumber = ref(1);
const loading = ref(false);
const errorMessage = ref("");
const response = ref(null);
const batchResult = ref(null);
const activeMode = ref("ppt");
const demoText = ref("营收: 120\n成本: 80\n利润: 40");
const demoLoading = ref(false);
const batchLoading = ref(false);
const batchLayoutLoading = ref(false);
const batchLayoutDownloadUrl = ref("");
const progressValue = ref(0);
const stageCards = ref([]);
const semanticMode = ref(settings.defaultSemanticMode);
const chartTypeOverride = ref("auto");
const chartTheme = ref("tech");
const illustrationStyle = ref(settings.defaultIllustrationStyle);
const imageModel = ref(settings.defaultImageModel);
const batchStart = ref(1);
const batchEnd = ref(1);
const slidePreviewUrl = ref("");
const slidePreviewLoading = ref(false);
const slidePreviewError = ref("");
const batchSlidePreviewCache = ref({});
const batchSlidePreviewLoading = ref(false);
const batchSlidePreviewError = ref("");
const slideCount = ref(0);
const uploadToken = ref("");
const slideOutline = ref([]);
const studioPanel = ref("overview");
const activeBatchIndex = ref(0);
const batchLayouts = ref({});

const studioTabs = [
  { key: "overview", label: "总览" },
  { key: "chart", label: "图表" },
  { key: "illustration", label: "配图" },
  { key: "pipeline", label: "流程" },
  { key: "outline", label: "逐页解析" },
];

const progressTemplate = [
  { stage: "parse_ppt", label: "解析内容" },
  { stage: "semantic_analysis", label: "语义分析" },
  { stage: "generate_chart", label: "生成图表" },
  { stage: "generate_illustration", label: "生成配图" },
  { stage: "save_pptx", label: "输出结果" },
];

let progressTimer = null;
let previewRequestId = 0;
let batchPreviewRequestId = 0;

const fileInfo = computed(() => {
  if (!file.value) {
    return null;
  }
  return {
    name: file.value.name,
    size: `${(file.value.size / 1024 / 1024).toFixed(2)} MB`,
    type: file.value.type || "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    lastModified: new Date(file.value.lastModified).toLocaleString("zh-CN"),
  };
});

const defaultBatchLayout = {
  chartX: 9,
  chartY: 12,
  chartScale: 42,
  illustrationX: 52,
  illustrationY: 16,
  illustrationScale: 39,
};

const batchSlides = computed(() => batchResult.value?.batch?.slides ?? []);
const hasBatchSlides = computed(() => batchSlides.value.length > 0);
const activeBatchSlide = computed(() => batchSlides.value[activeBatchIndex.value] ?? null);
const activeBatchPreviewUrl = computed(() => {
  const previewSlideNumber = activeBatchSlide.value?.slide_number;
  if (!previewSlideNumber) {
    return "";
  }
  return batchSlidePreviewCache.value[String(previewSlideNumber)]?.url ?? "";
});
const activeBatchPipeline = computed(() => activeBatchSlide.value?.pipeline ?? null);
const pipelineResult = computed(() => activeBatchPipeline.value ?? response.value?.pipeline ?? null);
const chartPreviewUrl = computed(() => pipelineResult.value?.chart_image_url ?? "");
const illustrationPreviewUrl = computed(() => pipelineResult.value?.illustration_image_url ?? "");
const downloadUrl = computed(() => pipelineResult.value?.final_pptx_url ?? "");
const recentLogs = computed(() => pipelineResult.value?.logs ?? []);
const intentInfo = computed(() => pipelineResult.value?.intent ?? null);
const chartSpec = computed(() => pipelineResult.value?.chart_spec ?? null);
const illustrationMeta = computed(() => pipelineResult.value?.illustration_meta ?? null);
const semanticModeLabel = computed(
  () => semanticModeOptions.find((item) => item.value === semanticMode.value)?.label ?? "本地规则",
);
const semanticModeText = computed(() => {
  const mode = intentInfo.value?.semantic_mode || semanticMode.value;
  return semanticModeOptions.find((item) => item.value === mode)?.label ?? "本地规则";
});
const clipScoreText = computed(() => {
  const score = illustrationMeta.value?.clip_score ?? intentInfo.value?.clip_score;
  return score == null ? "未评分" : `${score} / 10`;
});
const clipScoreValue = computed(() => {
  const score = illustrationMeta.value?.clip_score ?? intentInfo.value?.clip_score;
  return score == null ? "—" : String(score);
});
const chartQualityText = computed(() => {
  const score = chartSpec.value?.quality_score;
  return score == null ? "未评分" : `${score} / 10`;
});
const chartCoverageText = computed(() => {
  const coverage = chartSpec.value?.quality_checks?.numeric_coverage;
  const number = Number(coverage);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "—";
});
const illustrationQualityStatus = computed(() => {
  const meta = illustrationMeta.value;
  if (!meta) {
    return "待生成";
  }
  if (meta.regenerated) {
    return "已重生成";
  }
  if (meta.regenerate_hint) {
    return "待复核";
  }
  return "通过";
});
const illustrationQualityBadgeClass = computed(() => {
  const status = illustrationQualityStatus.value;
  if (status === "已重生成") {
    return "bg-amber-100 text-amber-700";
  }
  if (status === "待复核") {
    return "bg-red-100 text-red-700";
  }
  if (status === "通过") {
    return "bg-green-100 text-green-700";
  }
  return "bg-gray-100 text-gray-600";
});
const regenerateActionText = computed(() => {
  const action = illustrationMeta.value?.regenerate_action;
  const map = {
    local_refined_prompt: "本地 refined prompt",
    manual_review_recommended: "建议人工复核",
    none: "无需重生成",
  };
  return map[action] ?? action ?? "等待评分";
});
const scoreDeltaText = computed(() => {
  const meta = illustrationMeta.value;
  if (!meta || meta.initial_clip_score == null || meta.clip_score == null) {
    return "—";
  }
  const delta = Number(meta.clip_score) - Number(meta.initial_clip_score);
  if (!Number.isFinite(delta)) {
    return "—";
  }
  return delta > 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1);
});
const illustrationQualityCards = computed(() => {
  const meta = illustrationMeta.value || {};
  return [
    { label: "初始分", value: meta.initial_clip_score == null ? "—" : String(meta.initial_clip_score) },
    { label: "最终分", value: meta.clip_score == null ? "—" : String(meta.clip_score) },
    { label: "阈值", value: meta.score_threshold == null ? "6.5" : String(meta.score_threshold) },
    { label: "提升", value: scoreDeltaText.value },
  ];
});
const chartOverrideText = computed(
  () => chartTypeOptions.find((item) => item.value === chartTypeOverride.value)?.label ?? chartTypeOverride.value,
);
const chartThemeLabel = computed(
  () => chartThemeOptions.find((item) => item.value === chartTheme.value)?.label ?? chartTheme.value,
);
const canPreview = computed(() => Boolean(file.value || uploadToken.value));
const illustrationStyleLabel = computed(
  () => illustrationStyleOptions.find((item) => item.value === illustrationStyle.value)?.label ?? illustrationStyle.value,
);
const imageModelLabel = computed(
  () => imageModelOptions.find((item) => item.value === imageModel.value)?.label ?? imageModel.value,
);
const hasVisualOutput = computed(() => Boolean(chartPreviewUrl.value || illustrationPreviewUrl.value));
const hasPipelineOutput = computed(() => Boolean(stageCards.value.length || recentLogs.value.length));
const batchDownloadUrl = computed(() => batchResult.value?.batch?.final_pptx_url ?? "");
const sourcePptxPath = computed(() => batchResult.value?.file?.source_pptx_path ?? "");
const batchStatusText = computed(() => {
  const batch = batchResult.value?.batch;
  if (!batch) {
    return "尚未批量处理";
  }
  return `${batch.success_count}/${batch.total_slides} 页成功`;
});
const batchPageText = computed(() => {
  if (!hasBatchSlides.value) {
    return "0/0";
  }
  return `${activeBatchIndex.value + 1}/${batchSlides.value.length}`;
});
const activeBatchLayoutKey = computed(() => {
  const slide = activeBatchSlide.value;
  return String(slide?.pipeline?.request_id ?? slide?.slide_number ?? "default");
});
const activeBatchLayout = computed(() => batchLayouts.value[activeBatchLayoutKey.value] ?? defaultBatchLayout);
const chartLayerStyle = computed(() => ({
  left: `${activeBatchLayout.value.chartX}%`,
  top: `${activeBatchLayout.value.chartY}%`,
  width: `${activeBatchLayout.value.chartScale}%`,
}));
const illustrationLayerStyle = computed(() => ({
  left: `${activeBatchLayout.value.illustrationX}%`,
  top: `${activeBatchLayout.value.illustrationY}%`,
  width: `${activeBatchLayout.value.illustrationScale}%`,
}));
const batchLayoutText = computed(
  () =>
    `图表 ${activeBatchLayout.value.chartX}%/${activeBatchLayout.value.chartY}% · 配图 ${activeBatchLayout.value.illustrationX}%/${activeBatchLayout.value.illustrationY}%`,
);
const currentStudioLabel = computed(
  () => studioTabs.find((item) => item.key === studioPanel.value)?.label ?? "总览",
);
const currentPanelDescription = computed(() => {
  const map = {
    overview: "以当前结果为主视图，减少无关信息干扰。",
    chart: "放大查看图表结果，适合汇报前快速核对。",
    illustration: "放大查看配图结果，适合做风格判断和最终选择。",
    pipeline: "查看语义判断、阶段状态和运行日志。",
    outline: "查看每页 PPT 的提取结构，快速定位目标页。",
  };
  return map[studioPanel.value] ?? map.overview;
});
const summaryMetrics = computed(() => [
  { label: "模式", value: activeMode.value === "ppt" ? "PPT" : "文本演示" },
  { label: "页码", value: activeMode.value === "ppt" ? String(slideNumber.value) : "Demo" },
  { label: "配图质量", value: illustrationQualityStatus.value },
  { label: "进度", value: `${progressValue.value}%` },
]);

function appendPersonalSettings(formData) {
  formData.append("custom_qwen_api_key", settings.customQwenApiKey || "");
  formData.append("custom_qwen_model", settings.customQwenModel || "");
  formData.append("custom_wanx_api_key", settings.customWanxApiKey || "");
  formData.append("custom_flux_api_key", settings.customFluxApiKey || "");
}

async function submitForm() {
  errorMessage.value = "";
  response.value = null;
  startProgress();

  if (!file.value) {
    errorMessage.value = "请先上传 PPTX 文件。";
    stopProgress(true);
    return;
  }

  loading.value = true;
  const formData = new FormData();
  formData.append("file", file.value);
  formData.append("slide_number", String(slideNumber.value));
  formData.append("semantic_mode", semanticMode.value);
  formData.append("chart_type_override", chartTypeOverride.value);
  formData.append("chart_theme", chartTheme.value);
  formData.append("illustration_style", illustrationStyle.value);
  formData.append("image_model", imageModel.value);
  appendPersonalSettings(formData);

  try {
    const payload = await requestProcess(formData);
    response.value = payload;
    batchResult.value = null;
    batchSlidePreviewCache.value = {};
    batchSlidePreviewError.value = "";
    finalizeProgress(payload.pipeline);
    studioPanel.value = payload.pipeline?.illustration_image_url ? "illustration" : "chart";
  } catch (error) {
    errorMessage.value = error.message;
    stopProgress(true);
  } finally {
    loading.value = false;
  }
}

async function runDemo() {
  errorMessage.value = "";
  response.value = null;
  startProgress();
  demoLoading.value = true;

  const formData = new FormData();
  formData.append("source_text", demoText.value);
  formData.append("semantic_mode", semanticMode.value);
  formData.append("chart_type_override", chartTypeOverride.value);
  formData.append("chart_theme", chartTheme.value);
  formData.append("illustration_style", illustrationStyle.value);
  formData.append("image_model", imageModel.value);
  appendPersonalSettings(formData);

  try {
    const payload = await requestDemo(formData);
    response.value = payload;
    batchResult.value = null;
    batchSlidePreviewCache.value = {};
    batchSlidePreviewError.value = "";
    finalizeProgress(payload.pipeline);
    studioPanel.value = payload.pipeline?.illustration_image_url ? "illustration" : "chart";
  } catch (error) {
    errorMessage.value = error.message;
    stopProgress(true);
  } finally {
    demoLoading.value = false;
  }
}

function handleSelectedFile(selected) {
  file.value = selected ?? null;
  uploadToken.value = "";
  slidePreviewUrl.value = "";
  slidePreviewError.value = "";
  batchSlidePreviewCache.value = {};
  batchSlidePreviewError.value = "";
  slideOutline.value = [];
  slideCount.value = 0;
  slideNumber.value = 1;
  batchStart.value = 1;
  batchEnd.value = 1;
  response.value = null;
  batchResult.value = null;
  studioPanel.value = "overview";
  if (file.value) {
    fetchSlidePreview(true);
  }
}

async function fetchSlidePreview(forceUpload = false) {
  if (activeMode.value !== "ppt" || !canPreview.value) {
    return;
  }
  const currentRequestId = ++previewRequestId;
  slidePreviewLoading.value = true;
  slidePreviewError.value = "";
  const formData = new FormData();
  formData.append("slide_number", String(slideNumber.value));
  if (forceUpload || !uploadToken.value) {
    formData.append("file", file.value);
  } else {
    formData.append("upload_token", uploadToken.value);
  }

  try {
    const payload = await requestSlidePreview(formData);
    if (currentRequestId !== previewRequestId) {
      return;
    }
    uploadToken.value = payload.upload_token || uploadToken.value;
    slideCount.value = payload.slide_count || 0;
    if (payload.slide_count && batchEnd.value <= 1) {
      batchEnd.value = payload.slide_count;
    }
    slidePreviewUrl.value = payload.preview_image_url || "";
    if (!slideOutline.value.length || forceUpload) {
      await fetchSlideOutline();
    }
  } catch (error) {
    if (currentRequestId !== previewRequestId) {
      return;
    }
    slidePreviewError.value = error.message;
    slidePreviewUrl.value = "";
  } finally {
    if (currentRequestId === previewRequestId) {
      slidePreviewLoading.value = false;
    }
  }
}

async function fetchSlideOutline() {
  if (!uploadToken.value) {
    return;
  }
  try {
    const formData = new FormData();
    formData.append("upload_token", uploadToken.value);
    const payload = await requestSlideOutline(formData);
    slideOutline.value = payload.slides || [];
    slideCount.value = payload.slide_count || slideCount.value;
    if (payload.slide_count && batchEnd.value <= 1) {
      batchEnd.value = payload.slide_count;
    }
  } catch (error) {
    slidePreviewError.value = error.message;
  }
}

async function fetchBatchSlidePreview(slide) {
  if (activeMode.value !== "ppt" || !slide?.slide_number || !canPreview.value) {
    return;
  }

  const key = String(slide.slide_number);
  if (batchSlidePreviewCache.value[key]?.url) {
    return;
  }

  const currentRequestId = ++batchPreviewRequestId;
  batchSlidePreviewLoading.value = true;
  batchSlidePreviewError.value = "";

  const formData = new FormData();
  formData.append("slide_number", key);
  if (uploadToken.value) {
    formData.append("upload_token", uploadToken.value);
  } else if (file.value) {
    formData.append("file", file.value);
  }

  try {
    const payload = await requestSlidePreview(formData);
    if (currentRequestId !== batchPreviewRequestId) {
      return;
    }
    uploadToken.value = payload.upload_token || uploadToken.value;
    slideCount.value = payload.slide_count || slideCount.value;
    batchSlidePreviewCache.value = {
      ...batchSlidePreviewCache.value,
      [key]: {
        url: payload.preview_image_url || "",
        slideCount: payload.slide_count || 0,
      },
    };
  } catch (error) {
    if (currentRequestId !== batchPreviewRequestId) {
      return;
    }
    batchSlidePreviewError.value = error.message;
  } finally {
    if (currentRequestId === batchPreviewRequestId) {
      batchSlidePreviewLoading.value = false;
    }
  }
}

function startProgress() {
  stopProgress(false);
  progressValue.value = 6;
  stageCards.value = progressTemplate.map((item, index) => ({
    ...item,
    status: index === 0 ? "running" : "pending",
  }));
  progressTimer = window.setInterval(() => {
    if (progressValue.value < 90) {
      progressValue.value += 6;
      const activeIndex = Math.min(Math.floor(progressValue.value / 20), progressTemplate.length - 1);
      stageCards.value = progressTemplate.map((item, index) => ({
        ...item,
        status: index < activeIndex ? "completed" : index === activeIndex ? "running" : "pending",
      }));
    }
  }, 320);
}

function finalizeProgress(pipeline) {
  stopProgress(false);
  progressValue.value = pipeline?.progress ?? 100;
  stageCards.value =
    pipeline?.stage_history?.map((item) => ({
      stage: item.stage,
      label: item.stage,
      status: item.status,
      details: item.details,
    })) ?? progressTemplate.map((item) => ({ ...item, status: "completed" }));
}

function ensureBatchLayout(slide) {
  if (!slide) {
    return;
  }
  const key = String(slide.pipeline?.request_id ?? slide.slide_number ?? "default");
  if (!batchLayouts.value[key]) {
    batchLayouts.value = {
      ...batchLayouts.value,
      [key]: { ...defaultBatchLayout },
    };
  }
}

function stopProgress(reset) {
  if (progressTimer) {
    window.clearInterval(progressTimer);
    progressTimer = null;
  }
  if (reset) {
    progressValue.value = 0;
    stageCards.value = [];
  }
}

function rerunCurrentMode() {
  if (loading.value || demoLoading.value || batchLoading.value || batchLayoutLoading.value) {
    return;
  }
  if (activeMode.value === "ppt") {
    submitForm();
  } else {
    runDemo();
  }
}

async function submitBatch() {
  errorMessage.value = "";
  response.value = null;
  batchResult.value = null;
  batchSlidePreviewCache.value = {};
  batchSlidePreviewError.value = "";
  startProgress();

  if (activeMode.value !== "ppt" || (!file.value && !uploadToken.value)) {
    errorMessage.value = "请先上传 PPTX 文件。";
    stopProgress(true);
    return;
  }

  const start = Number(batchStart.value || 1);
  const end = Number(batchEnd.value || slideCount.value || start);
  if (start < 1 || end < start) {
    errorMessage.value = "请填写有效的批量页码范围。";
    stopProgress(true);
    return;
  }

  batchLoading.value = true;
  const formData = new FormData();
  if (uploadToken.value) {
    formData.append("upload_token", uploadToken.value);
  } else {
    formData.append("file", file.value);
  }
  formData.append("slide_start", String(start));
  formData.append("slide_end", String(end));
  formData.append("semantic_mode", semanticMode.value);
  formData.append("chart_type_override", chartTypeOverride.value);
  formData.append("chart_theme", chartTheme.value);
  formData.append("illustration_style", illustrationStyle.value);
  formData.append("image_model", imageModel.value);
  appendPersonalSettings(formData);

  try {
    const payload = await requestBatchProcess(formData);
    batchResult.value = payload;
    activeBatchIndex.value = 0;
    batchLayouts.value = {};
    batchLayoutDownloadUrl.value = "";
    const firstSuccessfulIndex = (payload.batch?.slides || []).findIndex((item) => item.pipeline);
    if (firstSuccessfulIndex >= 0) {
      selectBatchSlide(firstSuccessfulIndex, false);
    } else {
      stopProgress(false);
      progressValue.value = 100;
    }
    studioPanel.value = "overview";
  } catch (error) {
    errorMessage.value = error.message;
    stopProgress(true);
  } finally {
    batchLoading.value = false;
  }
}

async function exportBatchManualLayout() {
  errorMessage.value = "";
  if (!sourcePptxPath.value || !batchSlides.value.length) {
    errorMessage.value = "请先完成一次批量生成。";
    return;
  }
  const slides = batchSlides.value
    .filter((item) => item.pipeline)
    .map((item) => {
      const key = String(item.pipeline?.request_id ?? item.slide_number ?? "default");
      return {
        slide_number: item.slide_number,
        chart_path: item.pipeline.chart_image || "",
        illustration_path: item.pipeline.illustration_image || "",
        title: `第 ${item.slide_number} 页手动布局结果`,
        subtitle: item.pipeline.intent?.reason || "手动微调后的批量生成结果。",
        intent: item.pipeline.intent || {},
        shapes: item.pipeline.shapes || [],
        layout_override: batchLayouts.value[key] ?? defaultBatchLayout,
      };
    });
  if (!slides.length) {
    errorMessage.value = "当前批量结果没有可写回的成功页。";
    return;
  }
  batchLayoutLoading.value = true;
  try {
    const payload = await requestBatchLayout({
      source_pptx_path: sourcePptxPath.value,
      batch_request_id: batchResult.value?.batch?.request_id || "",
      slides,
    });
    batchLayoutDownloadUrl.value = payload.final_pptx_url || "";
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    batchLayoutLoading.value = false;
  }
}

function selectBatchSlide(index, switchPanel = true) {
  if (index < 0 || index >= batchSlides.value.length) {
    return;
  }
  activeBatchIndex.value = index;
  const slide = batchSlides.value[index];
  ensureBatchLayout(slide);
  fetchBatchSlidePreview(slide);
  if (slide?.pipeline) {
    response.value = { pipeline: slide.pipeline };
    finalizeProgress(slide.pipeline);
  } else {
    response.value = null;
    stopProgress(false);
    progressValue.value = 100;
    stageCards.value = [];
  }
  if (slide?.slide_number) {
    slideNumber.value = slide.slide_number;
  }
  if (switchPanel) {
    studioPanel.value = "overview";
  }
}

function moveBatchSlide(delta) {
  selectBatchSlide(activeBatchIndex.value + delta);
}

function updateActiveBatchLayout(field, value) {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return;
  }
  const key = activeBatchLayoutKey.value;
  batchLayouts.value = {
    ...batchLayouts.value,
    [key]: {
      ...defaultBatchLayout,
      ...(batchLayouts.value[key] ?? {}),
      [field]: numericValue,
    },
  };
}

function resetActiveBatchLayout() {
  const key = activeBatchLayoutKey.value;
  batchLayouts.value = {
    ...batchLayouts.value,
    [key]: { ...defaultBatchLayout },
  };
}

function selectOutlineSlide(targetSlide) {
  slideNumber.value = targetSlide;
  studioPanel.value = "outline";
}

watch(slideNumber, () => {
  if (activeMode.value === "ppt" && canPreview.value) {
    fetchSlidePreview(false);
  }
});

watch(
  () => settings.defaultSemanticMode,
  (value) => {
    if (semanticMode.value === "local" || semanticMode.value === "qwen") {
      semanticMode.value = value;
    }
  },
);

watch(
  () => settings.defaultImageModel,
  (value) => {
    imageModel.value = value;
  },
);

watch(
  () => settings.defaultIllustrationStyle,
  (value) => {
    illustrationStyle.value = value;
  },
);
</script>

<template>
  <main class="w-full">
    <div class="mx-auto w-full max-w-[1480px] p-4 sm:p-6 xl:p-8">
      <section class="rounded-[28px] border border-white/50 bg-white/70 p-5 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl sm:p-8">
        <div class="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div class="max-w-4xl">
            <p class="text-[11px] font-medium uppercase tracking-[0.24em] text-gray-400">SmartChart Studio</p>
            <h1 class="mt-3 text-4xl font-semibold tracking-tight text-gray-900 sm:text-5xl xl:text-6xl">生成工作台</h1>
            <p class="mt-4 max-w-3xl text-base leading-7 text-gray-500">
              上传您的演示文稿，AI 将自动进行语义解析，并在主工作区为您实时生成专业的图表与配图。
            </p>
          </div>

          <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div
              v-for="item in summaryMetrics"
              :key="item.label"
              class="rounded-2xl border border-transparent bg-white/80 px-4 py-3 transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg hover:border-gray-200"
            >
              <p class="text-xs uppercase tracking-[0.18em] text-gray-400">{{ item.label }}</p>
              <p class="mt-2 text-sm font-semibold text-gray-900">{{ item.value }}</p>
            </div>
          </div>
        </div>
      </section>

      <div class="mt-8 grid gap-8 xl:grid-cols-[380px_minmax(0,1fr)]">
        <aside class="space-y-6 xl:sticky xl:top-8 xl:h-fit">
          <section class="relative z-10 overflow-visible rounded-[28px] border border-white/50 bg-white/70 p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl">
            <div class="flex items-center justify-between gap-4">
              <div>
                <p class="text-sm font-medium text-gray-500">Studio Controls</p>
                <h2 class="mt-2 text-3xl font-semibold tracking-tight text-gray-900">上传与生成</h2>
              </div>

              <div class="inline-flex rounded-full bg-gray-100 p-1">
                <button
                  type="button"
                  class="rounded-full px-4 py-2 text-sm font-medium transition-all duration-200 ease-in-out active:scale-[0.98]"
                  :class="activeMode === 'ppt' ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-900'"
                  @click="activeMode = 'ppt'"
                >
                  PPT
                </button>
                <button
                  type="button"
                  class="rounded-full px-4 py-2 text-sm font-medium transition-all duration-200 ease-in-out active:scale-[0.98]"
                  :class="activeMode === 'demo' ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-900'"
                  @click="activeMode = 'demo'"
                >
                  文本
                </button>
              </div>
            </div>

            <div class="mt-6 space-y-5">
              <UploadDropzone v-if="activeMode === 'ppt'" :file="file" class="h-56" @select="handleSelectedFile" />

              <div v-else class="rounded-3xl border border-gray-100 bg-gray-50/80 p-4">
                <label class="block space-y-2">
                  <span class="text-sm font-medium text-gray-500">业务文本</span>
                  <textarea
                    v-model="demoText"
                    rows="7"
                    placeholder="例如：营收 120"
                    class="w-full rounded-2xl border border-transparent bg-white px-4 py-3 text-sm text-gray-900 outline-none transition-all duration-200 ease-in-out placeholder:text-gray-400 focus:border-gray-300 focus:ring-1 focus:ring-gray-300 focus:shadow-sm"
                  ></textarea>
                </label>
              </div>

              <label v-if="activeMode === 'ppt'" class="block space-y-2">
                <span class="text-sm font-medium text-gray-500">处理页码<span v-if="slideCount">（共 {{ slideCount }} 页）</span></span>
                <input
                  v-model.number="slideNumber"
                  type="number"
                  min="1"
                  :max="slideCount || undefined"
                  class="w-full rounded-2xl border border-transparent bg-gray-100 px-4 py-3 text-sm text-gray-900 outline-none transition-all duration-200 ease-in-out placeholder:text-gray-400 focus:border-gray-300 focus:bg-white focus:ring-1 focus:ring-gray-300 focus:shadow-sm"
                />
              </label>

              <div class="grid gap-3">
                <button
                  type="button"
                  class="rounded-full bg-gray-900 px-5 py-3 text-sm font-medium text-white transition-all duration-200 ease-in-out hover:bg-gray-800 active:scale-[0.98]"
                  :disabled="loading || demoLoading || batchLoading"
                  @click="activeMode === 'ppt' ? submitForm() : runDemo()"
                >
                  {{
                    loading || demoLoading || batchLoading
                      ? "处理中..."
                      : activeMode === "ppt"
                        ? "一键生成图表与配图"
                        : "文本导出图表 PNG"
                  }}
                </button>
                <button
                  type="button"
                  class="rounded-full border border-gray-200 bg-white px-5 py-3 text-sm font-medium text-gray-700 transition-transform duration-150 ease-in-out hover:bg-gray-50 active:scale-[0.98]"
                  :disabled="loading || demoLoading || batchLoading"
                  @click="rerunCurrentMode"
                >
                  重新生成当前结果
                </button>
              </div>

              <div v-if="activeMode === 'ppt'" class="rounded-2xl border border-gray-100 bg-white/80 p-4">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <p class="text-sm font-semibold tracking-tight text-gray-900">批量处理</p>
                    <p class="mt-1 text-sm text-gray-500">第 {{ batchStart || 1 }} - {{ batchEnd || slideCount || batchStart || 1 }} 页</p>
                  </div>
                  <span class="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">{{ batchStatusText }}</span>
                </div>
                <div class="mt-4 grid grid-cols-2 gap-3">
                  <label class="block space-y-2">
                    <span class="text-sm font-medium text-gray-500">起始页</span>
                    <input
                      v-model.number="batchStart"
                      type="number"
                      min="1"
                      :max="slideCount || undefined"
                      class="w-full rounded-2xl border border-transparent bg-gray-100 px-4 py-3 text-sm text-gray-900 outline-none transition-all duration-200 ease-in-out focus:border-gray-300 focus:bg-white focus:ring-1 focus:ring-gray-300"
                    />
                  </label>
                  <label class="block space-y-2">
                    <span class="text-sm font-medium text-gray-500">结束页</span>
                    <input
                      v-model.number="batchEnd"
                      type="number"
                      min="1"
                      :max="slideCount || undefined"
                      class="w-full rounded-2xl border border-transparent bg-gray-100 px-4 py-3 text-sm text-gray-900 outline-none transition-all duration-200 ease-in-out focus:border-gray-300 focus:bg-white focus:ring-1 focus:ring-gray-300"
                    />
                  </label>
                </div>
                <button
                  type="button"
                  class="mt-4 w-full rounded-full border border-gray-200 bg-gray-950 px-5 py-3 text-sm font-medium text-white transition-transform duration-150 ease-in-out hover:bg-gray-800 active:scale-[0.98]"
                  :disabled="loading || demoLoading || batchLoading || (!file && !uploadToken)"
                  @click="submitBatch"
                >
                  {{ batchLoading ? "批量处理中..." : "批量生成合并 PPT" }}
                </button>
                <a
                  v-if="batchDownloadUrl"
                  :href="batchDownloadUrl"
                  target="_blank"
                  rel="noreferrer"
                  class="mt-3 flex items-center justify-between rounded-2xl border border-gray-100 bg-gray-50 px-4 py-3 text-sm font-medium text-gray-700 transition-all duration-200 hover:bg-white"
                >
                  <span>下载批量增强版 PPT</span>
                  <span class="text-xs text-gray-400">PPTX</span>
                </a>
              </div>

              <details class="group relative z-20 overflow-visible rounded-2xl border border-gray-100 bg-white/80 p-4">
                <summary class="flex cursor-pointer items-center justify-between gap-4">
                  <div>
                    <p class="text-sm font-semibold tracking-tight text-gray-900">高级参数</p>
                    <p class="mt-1 text-sm text-gray-500">自定义您的模型调度与语义分析配置。</p>
                  </div>
                  <span class="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-gray-500 transition-transform duration-300 ease-out group-open:rotate-180">
                    <svg class="h-4 w-4" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                      <path d="M5 7.5 10 12.5l5-5" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" />
                    </svg>
                  </span>
                </summary>

                <div class="grid grid-rows-[0fr] transition-all duration-300 ease-out group-open:grid-rows-[1fr]">
                  <div class="overflow-hidden">
                    <div class="mt-5 grid gap-4">
                      <label class="block space-y-2">
                        <span class="text-sm font-medium text-gray-500">语义分析模式</span>
                        <SelectMenu v-model="semanticMode" :options="semanticModeOptions" />
                      </label>

                      <label class="block space-y-2">
                        <span class="text-sm font-medium text-gray-500">图表类型修正</span>
                        <SelectMenu v-model="chartTypeOverride" :options="chartTypeOptions" />
                      </label>

                      <label class="block space-y-2">
                        <span class="text-sm font-medium text-gray-500">图表主题</span>
                        <SelectMenu v-model="chartTheme" :options="chartThemeOptions" />
                      </label>

                      <label class="block space-y-2">
                        <span class="text-sm font-medium text-gray-500">配图风格</span>
                        <SelectMenu v-model="illustrationStyle" :options="illustrationStyleOptions" />
                      </label>

                      <label class="block space-y-2">
                        <span class="text-sm font-medium text-gray-500">配图模型</span>
                        <SelectMenu v-model="imageModel" :options="imageModelOptions" />
                      </label>
                    </div>
                  </div>
                </div>
              </details>

              <div class="rounded-2xl border border-gray-100 bg-white/80 p-4">
                <div class="mb-3 flex items-center justify-between gap-3 text-sm">
                  <span class="font-medium text-gray-500">处理进度 · {{ semanticModeLabel }}</span>
                  <strong class="font-semibold text-gray-900">{{ progressValue }}%</strong>
                </div>
                <div class="h-2 overflow-hidden rounded-full bg-gray-100">
                  <div class="h-full rounded-full bg-gray-900 transition-all duration-300" :style="{ width: `${progressValue}%` }"></div>
                </div>
              </div>

              <p v-if="errorMessage" class="text-sm text-red-500">{{ errorMessage }}</p>
            </div>
          </section>

          <section class="rounded-[28px] border border-transparent bg-white/70 p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg hover:border-gray-200">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-sm font-medium text-gray-500">Current Page</p>
                <h3 class="mt-2 text-2xl font-semibold tracking-tight text-gray-900">即时预览</h3>
              </div>
              <span v-if="slidePreviewLoading" class="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">加载中</span>
            </div>

            <div v-if="slidePreviewUrl" class="mt-5 flex min-h-56 items-center justify-center overflow-hidden rounded-3xl border border-gray-100 bg-gray-50 p-4">
              <img :src="slidePreviewUrl" alt="slide preview" class="max-h-64 w-full rounded-2xl object-contain" />
            </div>
            <div v-else-if="slidePreviewError" class="mt-5 rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-500">
              {{ slidePreviewError }}
            </div>
            <div
              v-else
              class="mt-5 flex min-h-56 items-center justify-center rounded-3xl border border-dashed border-gray-200 bg-gray-50 text-center text-sm text-gray-500"
            >
              等待预览加载...
            </div>
          </section>
        </aside>

        <section class="min-w-0 space-y-6">
          <section class="rounded-[32px] border border-white/50 bg-white/75 p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl">
            <div class="flex flex-col gap-5 border-b border-gray-100 pb-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p class="text-sm font-medium text-gray-500">Workspace / {{ currentStudioLabel }}</p>
                <h2 class="mt-2 text-3xl font-semibold tracking-tight text-gray-900">结果主画布</h2>
                <p class="mt-2 text-sm leading-6 text-gray-500">{{ currentPanelDescription }}</p>
              </div>

              <div class="flex flex-wrap gap-2">
                <button
                  v-for="item in studioTabs"
                  :key="item.key"
                  type="button"
                  class="rounded-full px-4 py-2 text-sm font-medium transition-all duration-200 ease-in-out active:scale-[0.98]"
                  :class="
                    studioPanel === item.key
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-900'
                  "
                  @click="studioPanel = item.key"
                >
                  {{ item.label }}
                </button>
              </div>
            </div>

            <div v-if="hasBatchSlides" class="mt-6 rounded-[28px] border border-gray-100 bg-gray-50/80 p-5">
              <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Batch Review</p>
                  <h3 class="mt-2 text-2xl font-semibold tracking-tight text-gray-900">批量逐页查看</h3>
                  <p class="mt-2 text-sm leading-6 text-gray-500">
                    当前第 {{ activeBatchSlide?.slide_number ?? "—" }} 页 · {{ batchPageText }} · {{ activeBatchSlide?.status ?? "waiting" }}
                  </p>
                </div>

                <div class="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    class="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-transform duration-150 ease-in-out hover:bg-gray-50 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
                    :disabled="activeBatchIndex <= 0"
                    @click="moveBatchSlide(-1)"
                  >
                    上一页
                  </button>
                  <button
                    type="button"
                    class="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-transform duration-150 ease-in-out hover:bg-gray-50 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
                    :disabled="activeBatchIndex >= batchSlides.length - 1"
                    @click="moveBatchSlide(1)"
                  >
                    下一页
                  </button>
                  <button
                    type="button"
                    class="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-transform duration-150 ease-in-out hover:bg-gray-50 active:scale-[0.98]"
                    @click="resetActiveBatchLayout"
                  >
                    重置位置
                  </button>
                  <button
                    type="button"
                    class="rounded-full bg-gray-900 px-4 py-2 text-sm font-medium text-white transition-transform duration-150 ease-in-out hover:bg-gray-800 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="batchLayoutLoading || !sourcePptxPath"
                    @click="exportBatchManualLayout"
                  >
                    {{ batchLayoutLoading ? "写回中..." : "导出微调版 PPT" }}
                  </button>
                  <a
                    v-if="batchLayoutDownloadUrl"
                    :href="batchLayoutDownloadUrl"
                    target="_blank"
                    rel="noreferrer"
                    class="rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-700 transition-transform duration-150 ease-in-out hover:bg-emerald-100 active:scale-[0.98]"
                  >
                    下载微调版
                  </a>
                </div>
              </div>

              <div class="mt-5 flex gap-2 overflow-x-auto pb-1">
                <button
                  v-for="(item, index) in batchSlides"
                  :key="`${item.slide_number}-${index}`"
                  type="button"
                  class="min-w-20 rounded-2xl border px-4 py-3 text-left text-sm transition-all duration-200 ease-out active:scale-[0.98]"
                  :class="
                    activeBatchIndex === index
                      ? 'border-gray-900 bg-gray-900 text-white shadow-md'
                      : item.status === 'failed'
                        ? 'border-red-100 bg-red-50 text-red-600'
                        : 'border-gray-100 bg-white text-gray-600 hover:border-gray-200 hover:text-gray-900'
                  "
                  @click="selectBatchSlide(index)"
                >
                  <span class="block text-xs opacity-60">Slide</span>
                  <strong class="mt-1 block text-base">第 {{ item.slide_number }} 页</strong>
                </button>
              </div>

              <div class="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]">
                <div class="overflow-hidden rounded-[24px] border border-gray-100 bg-white p-4">
                  <div class="relative aspect-video overflow-hidden rounded-[20px] border border-gray-100 bg-white">
                    <img
                      v-if="activeBatchPreviewUrl"
                      :src="activeBatchPreviewUrl"
                      alt="original slide preview"
                      class="absolute inset-0 h-full w-full object-cover"
                    />
                    <div
                      v-else
                      class="absolute inset-0 flex items-center justify-center bg-[linear-gradient(135deg,#f8fafc_0%,#eef2f7_100%)] text-sm text-gray-500"
                    >
                      {{ batchSlidePreviewLoading ? "原稿预览加载中..." : batchSlidePreviewError || "等待原稿预览..." }}
                    </div>
                    <div class="absolute inset-0 bg-white/10"></div>
                    <img
                      v-if="chartPreviewUrl"
                      :src="chartPreviewUrl"
                      alt="batch chart placement"
                      class="absolute rounded-xl border border-white/80 bg-white object-contain p-2 shadow-lg ring-1 ring-gray-900/5 transition-all duration-200"
                      :style="chartLayerStyle"
                    />
                    <img
                      v-if="illustrationPreviewUrl"
                      :src="illustrationPreviewUrl"
                      alt="batch illustration placement"
                      class="absolute rounded-xl border border-white/80 bg-white object-contain p-2 shadow-lg ring-1 ring-gray-900/5 transition-all duration-200"
                      :style="illustrationLayerStyle"
                    />
                    <div
                      v-if="!activeBatchPreviewUrl && !chartPreviewUrl && !illustrationPreviewUrl"
                      class="absolute inset-0 flex items-center justify-center text-sm text-gray-500"
                    >
                      当前页未生成可预览资源
                    </div>
                  </div>
                  <p class="mt-3 text-sm text-gray-500">{{ batchLayoutText }}</p>
                </div>

                <div class="rounded-[24px] border border-gray-100 bg-white p-4">
                  <div class="flex items-center justify-between gap-3">
                    <div>
                      <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Placement</p>
                      <h4 class="mt-2 text-lg font-semibold tracking-tight text-gray-900">位置微调</h4>
                    </div>
                    <span class="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">可写回</span>
                  </div>

                  <div class="mt-4 space-y-4">
                    <label class="block space-y-2">
                      <span class="flex justify-between text-sm font-medium text-gray-500">
                        <span>图表 X</span>
                        <span>{{ activeBatchLayout.chartX }}%</span>
                      </span>
                      <input class="w-full accent-gray-900" type="range" min="0" max="70" :value="activeBatchLayout.chartX" @input="updateActiveBatchLayout('chartX', $event.target.value)" />
                    </label>
                    <label class="block space-y-2">
                      <span class="flex justify-between text-sm font-medium text-gray-500">
                        <span>图表 Y</span>
                        <span>{{ activeBatchLayout.chartY }}%</span>
                      </span>
                      <input class="w-full accent-gray-900" type="range" min="0" max="60" :value="activeBatchLayout.chartY" @input="updateActiveBatchLayout('chartY', $event.target.value)" />
                    </label>
                    <label class="block space-y-2">
                      <span class="flex justify-between text-sm font-medium text-gray-500">
                        <span>图表缩放</span>
                        <span>{{ activeBatchLayout.chartScale }}%</span>
                      </span>
                      <input class="w-full accent-gray-900" type="range" min="24" max="70" :value="activeBatchLayout.chartScale" @input="updateActiveBatchLayout('chartScale', $event.target.value)" />
                    </label>
                    <label class="block space-y-2">
                      <span class="flex justify-between text-sm font-medium text-gray-500">
                        <span>配图 X</span>
                        <span>{{ activeBatchLayout.illustrationX }}%</span>
                      </span>
                      <input class="w-full accent-gray-900" type="range" min="0" max="72" :value="activeBatchLayout.illustrationX" @input="updateActiveBatchLayout('illustrationX', $event.target.value)" />
                    </label>
                    <label class="block space-y-2">
                      <span class="flex justify-between text-sm font-medium text-gray-500">
                        <span>配图 Y</span>
                        <span>{{ activeBatchLayout.illustrationY }}%</span>
                      </span>
                      <input class="w-full accent-gray-900" type="range" min="0" max="62" :value="activeBatchLayout.illustrationY" @input="updateActiveBatchLayout('illustrationY', $event.target.value)" />
                    </label>
                    <label class="block space-y-2">
                      <span class="flex justify-between text-sm font-medium text-gray-500">
                        <span>配图缩放</span>
                        <span>{{ activeBatchLayout.illustrationScale }}%</span>
                      </span>
                      <input class="w-full accent-gray-900" type="range" min="24" max="70" :value="activeBatchLayout.illustrationScale" @input="updateActiveBatchLayout('illustrationScale', $event.target.value)" />
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <div class="mt-6">
              <div
                v-if="studioPanel === 'overview'"
                class="grid min-h-[44rem] gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.9fr)]"
              >
                <div class="grid gap-6">
                  <button
                    type="button"
                    class="flex min-h-[22rem] flex-col rounded-[28px] border border-transparent bg-gray-50/70 p-6 text-left transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg hover:border-gray-200"
                    @click="studioPanel = 'chart'"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <div>
                        <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Primary Visual</p>
                        <h3 class="mt-2 text-2xl font-semibold tracking-tight text-gray-900">图表结果</h3>
                      </div>
                      <span class="rounded-full bg-white px-3 py-1 text-xs font-medium text-gray-600">进入详情</span>
                    </div>

                    <div v-if="chartPreviewUrl" class="mt-6 flex flex-1 items-center justify-center overflow-hidden rounded-[24px] border border-gray-100 bg-white p-6">
                      <img :src="chartPreviewUrl" alt="chart preview" class="max-h-[25rem] w-full object-contain" />
                    </div>
                    <div
                      v-else
                      class="mt-6 flex flex-1 flex-col items-center justify-center rounded-[24px] border border-dashed border-gray-200 bg-white text-sm text-gray-500"
                    >
                      <svg class="mb-4 h-12 w-12 opacity-20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <path d="M4 19.5h16M7.5 16V9m4 7V5.5m4 10.5v-4" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" />
                      </svg>
                      等待生成图表...
                    </div>
                  </button>

                  <button
                    type="button"
                    class="flex min-h-[18rem] flex-col rounded-[28px] border border-transparent bg-gray-50/70 p-6 text-left transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg hover:border-gray-200"
                    @click="studioPanel = 'pipeline'"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <div>
                        <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Decision Trace</p>
                        <h3 class="mt-2 text-2xl font-semibold tracking-tight text-gray-900">Pipeline 摘要</h3>
                      </div>
                      <span class="rounded-full bg-white px-3 py-1 text-xs font-medium text-gray-600">查看流程</span>
                    </div>

                    <div class="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                      <div class="rounded-2xl border border-white/60 bg-white p-4">
                        <p class="text-xs uppercase tracking-[0.18em] text-gray-400">推荐图表</p>
                        <p class="mt-2 text-sm font-semibold text-gray-900">{{ intentInfo?.chart_type || "待生成" }}</p>
                      </div>
                      <div class="rounded-2xl border border-white/60 bg-white p-4">
                        <p class="text-xs uppercase tracking-[0.18em] text-gray-400">语义来源</p>
                        <p class="mt-2 text-sm font-semibold text-gray-900">{{ intentInfo?.source || "heuristic" }}</p>
                      </div>
                      <div class="rounded-2xl border border-white/60 bg-white p-4">
                        <p class="text-xs uppercase tracking-[0.18em] text-gray-400">配图风格</p>
                        <p class="mt-2 text-sm font-semibold text-gray-900">{{ illustrationStyleLabel }}</p>
                      </div>
                      <div class="rounded-2xl border border-white/60 bg-white p-4">
                        <p class="text-xs uppercase tracking-[0.18em] text-gray-400">图表质量</p>
                        <p class="mt-2 text-sm font-semibold text-gray-900">{{ chartQualityText }}</p>
                      </div>
                      <div class="rounded-2xl border border-white/60 bg-white p-4">
                        <p class="text-xs uppercase tracking-[0.18em] text-gray-400">覆盖率</p>
                        <p class="mt-2 text-sm font-semibold text-gray-900">{{ chartCoverageText }}</p>
                      </div>
                      <div class="rounded-2xl border border-white/60 bg-white p-4">
                        <p class="text-xs uppercase tracking-[0.18em] text-gray-400">CLIP</p>
                        <p class="mt-2 text-sm font-semibold text-gray-900">{{ clipScoreText }}</p>
                      </div>
                    </div>
                  </button>
                </div>

                <div class="grid gap-6">
                  <button
                    type="button"
                    class="flex min-h-[22rem] flex-col rounded-[28px] border border-transparent bg-gray-900 p-6 text-left text-white transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg hover:border-white/15"
                    @click="studioPanel = 'illustration'"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <div>
                        <p class="text-xs uppercase tracking-[0.18em] text-white/50">Illustration</p>
                        <h3 class="mt-2 text-2xl font-semibold tracking-tight text-white">配图结果</h3>
                      </div>
                      <div class="flex flex-wrap justify-end gap-2">
                        <span class="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-white/80">进入详情</span>
                        <span class="rounded-full px-3 py-1 text-xs font-medium" :class="illustrationQualityBadgeClass">
                          {{ illustrationQualityStatus }}
                        </span>
                      </div>
                    </div>

                    <div v-if="illustrationPreviewUrl" class="mt-6 flex flex-1 items-center justify-center overflow-hidden rounded-[24px] border border-white/10 bg-white/5 p-6">
                      <img :src="illustrationPreviewUrl" alt="illustration preview" class="max-h-[25rem] w-full object-contain" />
                    </div>
                    <div
                      v-else
                      class="mt-6 flex flex-1 flex-col items-center justify-center rounded-[24px] border border-dashed border-white/10 bg-white/5 text-sm text-white/60"
                    >
                      <svg class="mb-4 h-12 w-12 opacity-20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <path d="M5 19.25h14a1.25 1.25 0 0 0 1.25-1.25V6A1.25 1.25 0 0 0 19 4.75H5A1.25 1.25 0 0 0 3.75 6v12A1.25 1.25 0 0 0 5 19.25Z" stroke="currentColor" stroke-width="1.5" />
                        <path d="m7.5 15.5 3-3 2.25 2.25 3.75-4.25" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" />
                        <circle cx="8.25" cy="8.5" r="1.25" fill="currentColor" />
                      </svg>
                      等待生成配图...
                    </div>

                    <div v-if="illustrationMeta" class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                      <div
                        v-for="item in illustrationQualityCards"
                        :key="item.label"
                        class="rounded-2xl border border-white/10 bg-white/5 px-4 py-3"
                      >
                        <p class="text-[11px] uppercase tracking-[0.16em] text-white/40">{{ item.label }}</p>
                        <p class="mt-2 text-sm font-semibold text-white">{{ item.value }}</p>
                      </div>
                    </div>
                  </button>

                  <button
                    type="button"
                    class="flex min-h-[18rem] flex-col rounded-[28px] border border-transparent bg-gray-50/70 p-6 text-left transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg hover:border-gray-200"
                    @click="studioPanel = 'outline'"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <div>
                        <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Outline</p>
                        <h3 class="mt-2 text-2xl font-semibold tracking-tight text-gray-900">逐页 PPT 解析</h3>
                      </div>
                      <span class="rounded-full bg-white px-3 py-1 text-xs font-medium text-gray-600">查看详情</span>
                    </div>

                    <div class="mt-5 space-y-3">
                      <div
                        v-for="item in slideOutline.slice(0, 3)"
                        :key="item.slide_number"
                        class="rounded-2xl border border-white/60 bg-white px-4 py-4"
                      >
                        <div class="flex items-start justify-between gap-3">
                          <p class="text-sm font-semibold tracking-tight text-gray-900">第 {{ item.slide_number }} 页</p>
                          <span class="text-xs text-gray-400">{{ item.table_count }} 表格 · {{ item.shape_count }} 元素</span>
                        </div>
                        <p class="mt-2 line-clamp-2 text-sm leading-6 text-gray-500">{{ item.text_content || "暂无文本摘要" }}</p>
                      </div>
                      <div
                        v-if="!slideOutline.length"
                        class="flex min-h-32 items-center justify-center rounded-2xl border border-dashed border-gray-200 bg-white text-sm text-gray-500"
                      >
                        等待解析结果...
                      </div>
                    </div>
                  </button>
                </div>
              </div>

              <div v-else-if="studioPanel === 'chart'" class="min-h-[44rem]">
                <div class="flex h-full flex-col rounded-[28px] border border-transparent bg-gray-50/70 p-6 transition-all duration-300 ease-out hover:shadow-lg hover:border-gray-200">
                  <div class="flex items-center justify-between gap-3">
                    <div>
                      <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Detail View</p>
                      <h3 class="mt-2 text-2xl font-semibold tracking-tight text-gray-900">图表详情页</h3>
                    </div>
                    <button
                      type="button"
                      class="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-transform duration-150 ease-in-out hover:bg-gray-50 active:scale-[0.98]"
                      @click="studioPanel = 'overview'"
                    >
                      返回总览
                    </button>
                  </div>

                  <div v-if="chartPreviewUrl" class="mt-6 flex flex-1 items-center justify-center overflow-hidden rounded-[28px] border border-gray-100 bg-white p-8">
                    <img :src="chartPreviewUrl" alt="chart preview" class="max-h-[38rem] w-full object-contain" />
                  </div>
                  <div
                    v-else
                    class="mt-6 flex min-h-[34rem] flex-col items-center justify-center rounded-[28px] border border-dashed border-gray-200 bg-white text-sm text-gray-500"
                  >
                    <svg class="mb-4 h-14 w-14 opacity-20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <path d="M4 19.5h16M7.5 16V9m4 7V5.5m4 10.5v-4" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" />
                    </svg>
                    等待生成图表...
                  </div>
                </div>
              </div>

              <div v-else-if="studioPanel === 'illustration'" class="min-h-[44rem]">
                <div class="flex h-full flex-col rounded-[28px] border border-transparent bg-gray-950 p-6 text-white transition-all duration-300 ease-out hover:shadow-lg hover:border-white/15">
                  <div class="flex items-center justify-between gap-3">
                    <div>
                      <p class="text-xs uppercase tracking-[0.18em] text-white/40">Detail View</p>
                      <h3 class="mt-2 text-2xl font-semibold tracking-tight text-white">配图详情页</h3>
                    </div>
                    <button
                      type="button"
                      class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white transition-transform duration-150 ease-in-out hover:bg-white/10 active:scale-[0.98]"
                      @click="studioPanel = 'overview'"
                    >
                      返回总览
                    </button>
                  </div>

                  <div v-if="illustrationPreviewUrl" class="mt-6 flex flex-1 items-center justify-center overflow-hidden rounded-[28px] border border-white/10 bg-white/5 p-8">
                    <img :src="illustrationPreviewUrl" alt="illustration preview" class="max-h-[38rem] w-full object-contain" />
                  </div>
                  <div
                    v-else
                    class="mt-6 flex min-h-[34rem] flex-col items-center justify-center rounded-[28px] border border-dashed border-white/10 bg-white/5 text-sm text-white/60"
                  >
                    <svg class="mb-4 h-14 w-14 opacity-20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <path d="M5 19.25h14a1.25 1.25 0 0 0 1.25-1.25V6A1.25 1.25 0 0 0 19 4.75H5A1.25 1.25 0 0 0 3.75 6v12A1.25 1.25 0 0 0 5 19.25Z" stroke="currentColor" stroke-width="1.5" />
                      <path d="m7.5 15.5 3-3 2.25 2.25 3.75-4.25" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" />
                      <circle cx="8.25" cy="8.5" r="1.25" fill="currentColor" />
                    </svg>
                    等待生成配图...
                  </div>

                  <div v-if="illustrationMeta" class="mt-6 rounded-[24px] border border-white/10 bg-white/5 p-5">
                    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <p class="text-xs uppercase tracking-[0.18em] text-white/40">Quality Gate</p>
                        <h4 class="mt-2 text-lg font-semibold tracking-tight text-white">配图质量与重生成</h4>
                      </div>
                      <span class="w-fit rounded-full px-3 py-1 text-xs font-medium" :class="illustrationQualityBadgeClass">
                        {{ illustrationQualityStatus }}
                      </span>
                    </div>

                    <div class="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
                      <div
                        v-for="item in illustrationQualityCards"
                        :key="item.label"
                        class="rounded-2xl border border-white/10 bg-black/20 px-4 py-3"
                      >
                        <p class="text-[11px] uppercase tracking-[0.16em] text-white/40">{{ item.label }}</p>
                        <p class="mt-2 text-sm font-semibold text-white">{{ item.value }}</p>
                      </div>
                    </div>

                    <div class="mt-5 grid gap-3 lg:grid-cols-2">
                      <div class="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                        <p class="text-[11px] uppercase tracking-[0.16em] text-white/40">重生成动作</p>
                        <p class="mt-2 text-sm font-semibold text-white">{{ regenerateActionText }}</p>
                      </div>
                      <div class="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                        <p class="text-[11px] uppercase tracking-[0.16em] text-white/40">重生成次数</p>
                        <p class="mt-2 text-sm font-semibold text-white">{{ illustrationMeta.regenerate_attempts ?? 0 }}</p>
                      </div>
                    </div>

                    <p v-if="illustrationMeta.regenerate_reason" class="mt-4 text-sm leading-6 text-white/65">
                      {{ illustrationMeta.regenerate_reason }}
                    </p>
                  </div>
                </div>
              </div>

              <div v-else-if="studioPanel === 'pipeline'" class="min-h-[44rem]">
                <div class="studio-scrollbar max-h-[52rem] overflow-auto">
                  <PipelineStatus
                    :intent-info="intentInfo"
                    :illustration-meta="illustrationMeta"
                    :chart-spec="chartSpec"
                    :stage-cards="stageCards"
                    :recent-logs="recentLogs"
                    :semantic-mode-text="semanticModeText"
                    :chart-override-text="chartOverrideText"
                    :clip-score-text="clipScoreText"
                  />
                </div>
              </div>

              <div v-else-if="studioPanel === 'outline'" class="min-h-[44rem]">
                <div class="studio-scrollbar max-h-[52rem] overflow-auto">
                  <SlideOutlinePanel :slides="slideOutline" :active-slide="slideNumber" @select-slide="selectOutlineSlide" />
                </div>
              </div>
            </div>
          </section>

          <section class="grid gap-6 xl:grid-cols-[minmax(0,1.05fr)_minmax(280px,0.95fr)_minmax(280px,0.95fr)]">
            <div class="rounded-[28px] border border-transparent bg-white/70 p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg hover:border-gray-200">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-medium text-gray-500">Upload Context</p>
                  <h3 class="mt-2 text-2xl font-semibold tracking-tight text-gray-900">文件基本信息</h3>
                </div>
                <span class="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">
                  {{ activeMode === "ppt" ? "PPT" : "TEXT" }}
                </span>
              </div>

              <div v-if="fileInfo" class="mt-6 grid gap-4 md:grid-cols-2">
                <div class="rounded-2xl border border-gray-100 bg-white/90 p-4 md:col-span-2">
                  <p class="text-xs uppercase tracking-[0.18em] text-gray-400">File</p>
                  <p class="mt-2 text-sm font-semibold text-gray-900">{{ fileInfo.name }}</p>
                </div>
                <div class="rounded-2xl border border-gray-100 bg-white/90 p-4">
                  <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Size</p>
                  <p class="mt-2 text-sm font-semibold text-gray-900">{{ fileInfo.size }}</p>
                </div>
                <div class="rounded-2xl border border-gray-100 bg-white/90 p-4">
                  <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Page</p>
                  <p class="mt-2 text-sm font-semibold text-gray-900">{{ slideNumber }}</p>
                </div>
                <div class="rounded-2xl border border-gray-100 bg-white/90 p-4 md:col-span-2">
                  <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Updated</p>
                  <p class="mt-2 text-sm text-gray-500">{{ fileInfo.lastModified }}</p>
                </div>
              </div>

              <div
                v-else
                class="mt-6 flex min-h-52 flex-col items-center justify-center rounded-[24px] border border-dashed border-gray-200 bg-gray-50 text-center"
              >
                <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-gray-400 shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
                  <svg class="h-7 w-7" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M7 3.75h7.75L20.25 9v11.25A1.75 1.75 0 0 1 18.5 22h-11A1.75 1.75 0 0 1 5.75 20.25V5.5A1.75 1.75 0 0 1 7.5 3.75Z" stroke="currentColor" stroke-linejoin="round" stroke-width="1.5" />
                    <path d="M14.75 3.75V9h5.5" stroke="currentColor" stroke-linejoin="round" stroke-width="1.5" />
                  </svg>
                </div>
                <p class="mt-4 text-sm font-medium text-gray-900">等待上传文件</p>
                <p class="mt-2 max-w-xs text-sm leading-6 text-gray-500">上传后，这里显示文件属性和当前处理页信息。</p>
              </div>
            </div>

            <div class="rounded-[28px] border border-transparent bg-white/70 p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg hover:border-gray-200">
              <p class="text-sm font-medium text-gray-500">Current Config</p>
              <h3 class="mt-2 text-2xl font-semibold tracking-tight text-gray-900">调用配置</h3>

              <div class="mt-6 space-y-3">
                <div class="flex items-center justify-between gap-3 rounded-2xl border border-gray-100 bg-white/90 px-4 py-3 text-sm">
                  <span class="text-gray-500">默认语义模式</span>
                  <strong class="font-semibold text-gray-900">{{ semanticModeText }}</strong>
                </div>
                <div class="flex items-center justify-between gap-3 rounded-2xl border border-gray-100 bg-white/90 px-4 py-3 text-sm">
                  <span class="text-gray-500">图表修正</span>
                  <strong class="font-semibold text-gray-900">{{ chartOverrideText }}</strong>
                </div>
                <div class="flex items-center justify-between gap-3 rounded-2xl border border-gray-100 bg-white/90 px-4 py-3 text-sm">
                  <span class="text-gray-500">配图风格</span>
                  <strong class="font-semibold text-gray-900">{{ illustrationStyleLabel }}</strong>
                </div>
                <div class="flex items-center justify-between gap-3 rounded-2xl border border-gray-100 bg-white/90 px-4 py-3 text-sm">
                  <span class="text-gray-500">配图模型</span>
                  <strong class="font-semibold text-gray-900">{{ imageModelLabel }}</strong>
                </div>
              </div>
            </div>

            <div class="rounded-[28px] border border-transparent bg-white/70 p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg hover:border-gray-200">
              <p class="text-sm font-medium text-gray-500">Quick Access</p>
              <h3 class="mt-2 text-2xl font-semibold tracking-tight text-gray-900">结果入口</h3>

              <div class="mt-6 grid gap-3">
                <button
                  type="button"
                  class="flex items-center justify-between rounded-2xl border border-gray-100 bg-white/90 px-4 py-4 text-left transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-md active:scale-[0.98]"
                  @click="studioPanel = 'chart'"
                >
                  <span>
                    <strong class="block text-sm font-semibold text-gray-900">图表详情页</strong>
                    <span class="mt-1 block text-sm text-gray-500">{{ hasVisualOutput ? "进入大图视图" : "等待生成" }}</span>
                  </span>
                  <span class="text-xs font-medium text-gray-400">Chart</span>
                </button>

                <button
                  type="button"
                  class="flex items-center justify-between rounded-2xl border border-gray-100 bg-white/90 px-4 py-4 text-left transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-md active:scale-[0.98]"
                  @click="studioPanel = 'illustration'"
                >
                  <span>
                    <strong class="block text-sm font-semibold text-gray-900">配图详情页</strong>
                    <span class="mt-1 block text-sm text-gray-500">{{ hasVisualOutput ? "进入放大预览" : "等待生成" }}</span>
                  </span>
                  <span class="text-xs font-medium text-gray-400">Visual</span>
                </button>

                <button
                  type="button"
                  class="flex items-center justify-between rounded-2xl border border-gray-100 bg-white/90 px-4 py-4 text-left transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-md active:scale-[0.98]"
                  @click="studioPanel = 'pipeline'"
                >
                  <span>
                    <strong class="block text-sm font-semibold text-gray-900">流程详情页</strong>
                    <span class="mt-1 block text-sm text-gray-500">{{ hasPipelineOutput ? "查看日志与阶段状态" : "等待运行" }}</span>
                  </span>
                  <span class="text-xs font-medium text-gray-400">Trace</span>
                </button>
              </div>

              <a
                v-if="downloadUrl"
                :href="downloadUrl"
                class="mt-6 inline-flex rounded-full border border-gray-200 bg-white px-4 py-3 text-sm font-medium text-gray-700 transition-transform duration-150 ease-in-out hover:bg-gray-50 active:scale-[0.98]"
              >
                下载增强版 PPT
              </a>
              <div v-else class="mt-6 rounded-2xl border border-dashed border-gray-200 bg-gray-50 px-4 py-4 text-sm text-gray-500">
                等待生成结果...
              </div>
            </div>
          </section>
        </section>
      </div>
    </div>
  </main>
</template>
