<script setup>
<<<<<<< HEAD
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
=======
import { computed, ref, watch } from "vue";
>>>>>>> main

const file = ref(null);
const slideNumber = ref(1);
const loading = ref(false);
const demoLoading = ref(false);
const errorMessage = ref("");
const response = ref(null);
const activeMode = ref("ppt");
const semanticMode = ref("local");
const demoText = ref("营收: 120\n成本: 80\n利润: 40");

const themeMode = ref("light");
const activePreview = ref("compare");
const selectedModel = ref("flux");
const selectedStyle = ref("tech");
const controlNetEnabled = ref(true);
const controlNetStrength = ref(0.72);
const selectedCandidateIndex = ref(0);
const generationRound = ref(0);
const progressValue = ref(0);
const stageCards = ref([]);
<<<<<<< HEAD
const progressTimer = ref(null);
const pageReady = ref(false);
const fileInput = ref(null);

const pageOptions = [
  { value: "home", label: "首页" },
  { value: "workspace", label: "生成工作台" },
  { value: "report", label: "质量报告" },
  { value: "docs", label: "使用说明" },
];

const validPages = pageOptions.map((item) => item.value);

function getPageFromHash() {
  if (typeof window === "undefined") return "home";
  const page = window.location.hash.replace(/^#\/?/, "");
  return validPages.includes(page) ? page : "home";
}

const currentPage = ref(getPageFromHash());
const heroHeadlineRef = ref(null);
const heroHeadlineVisible = ref(false);
const spotlightSelector = [
  ".hero-panel",
  ".entry-card",
  ".overview-strip article",
  ".page-toolbar",
  ".report-card",
  ".doc-card",
  ".rail",
  ".stage",
  ".rail-block",
  ".summary-item",
  ".candidate-row",
  ".compare-panel",
  ".file-card",
  ".intent-card",
  ".gauge-card",
  ".stage-item",
].join(",");

let metricObserver = null;
let heroObserver = null;

const modelOptions = [
  { value: "flux", label: "Flux" },
  { value: "wanxiang", label: "通义万相" },
];

const styleOptions = [
  { value: "tech", label: "科技数据" },
  { value: "business", label: "商务增长" },
  { value: "minimal", label: "极简信息图" },
  { value: "education", label: "教育卡片" },
  { value: "medical", label: "医疗关怀" },
  { value: "neo", label: "赛博蓝紫" },
];

const styleGuideCards = [
  {
    value: "tech",
    label: "科技数据",
    glyph: "◧",
    accent: ["#1a73e8", "#10b981"],
    copy: "适合数据看板、图表和信息密度较高的页面。",
  },
  {
    value: "business",
    label: "商务增长",
    glyph: "↗",
    accent: ["#f59e0b", "#ef4444"],
    copy: "适合汇报、销售和增长叙事，强调商业感。",
  },
  {
    value: "minimal",
    label: "极简信息图",
    glyph: "□",
    accent: ["#64748b", "#38bdf8"],
    copy: "适合说明型内容，强调留白、秩序和阅读性。",
  },
  {
    value: "education",
    label: "教育卡片",
    glyph: "✎",
    accent: ["#6366f1", "#0ea5e9"],
    copy: "适合知识讲解、流程说明和教学类内容。",
  },
  {
    value: "medical",
    label: "医疗关怀",
    glyph: "✚",
    accent: ["#10b981", "#14b8a6"],
    copy: "适合健康、服务和关怀表达，视觉更温和。",
  },
  {
    value: "neo",
    label: "赛博蓝紫",
    glyph: "◆",
    accent: ["#8b5cf6", "#22c55e"],
    copy: "适合科技感和未来感视觉，强调动态氛围。",
  },
];

const heroHeadlineWords = [
  "把",
  "PPT",
  "图表生成、",
  "配图生成",
  "和",
  "CLIP",
  "质量判断",
  "拆成",
  "清晰流程。",
];

const heroHeadlineText = heroHeadlineWords.join("");
=======
const semanticMode = ref("local");
const chartTypeOverride = ref("auto");
const illustrationStyle = ref("auto");
const imageModel = ref("local");
const slidePreviewUrl = ref("");
const slidePreviewLoading = ref(false);
const slidePreviewError = ref("");
const slideCount = ref(0);
const uploadToken = ref("");
>>>>>>> main

const progressTemplate = [
  { stage: "parse_ppt", label: "解析内容" },
  { stage: "semantic_analysis", label: "语义分析" },
  { stage: "generate_chart", label: "生成图表" },
  { stage: "generate_illustration", label: "生成配图" },
  { stage: "save_pptx", label: "输出结果" },
];

<<<<<<< HEAD
const previewTabs = [
  { value: "chart", label: "图表" },
  { value: "illustration", label: "配图" },
  { value: "compare", label: "对比" },
];

const candidateTemplates = [
  {
    id: "primary",
    title: "主推荐配图",
    subtitle: "最贴近当前语义结果",
    tag: "推荐",
    tones: ["#06b6d4", "#2563eb"],
  },
  {
    id: "secondary",
    title: "对比配图 A",
    subtitle: "更偏商务插画",
    tag: "备选",
    tones: ["#f59e0b", "#ef4444"],
  },
  {
    id: "tertiary",
    title: "对比配图 B",
    subtitle: "更偏极简信息图",
    tag: "候选",
    tones: ["#8b5cf6", "#22c55e"],
  },
];
=======
let progressTimer = null;
let previewRequestId = 0;
>>>>>>> main

const fileInfo = computed(() => {
  if (!file.value) return null;
  return {
    name: file.value.name,
    size: `${(file.value.size / 1024 / 1024).toFixed(2)} MB`,
    type: file.value.type || "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    lastModified: new Date(file.value.lastModified).toLocaleString("zh-CN"),
  };
});

const pipelineResult = computed(() => response.value?.pipeline ?? null);
const chartPreviewUrl = computed(() => pipelineResult.value?.chart_image_url ?? "");
const illustrationPreviewUrl = computed(() => pipelineResult.value?.illustration_image_url ?? "");
const downloadUrl = computed(() => pipelineResult.value?.final_pptx_url ?? "");
const recentLogs = computed(() => pipelineResult.value?.logs ?? []);
const intentInfo = computed(() => pipelineResult.value?.intent ?? null);
const semanticModeLabel = computed(() => (semanticMode.value === "qwen" ? "千问 API" : "本地规则"));
const modelLabel = computed(() => (selectedModel.value === "flux" ? "Flux" : "通义万相"));
const styleLabel = computed(() => styleOptions.find((item) => item.value === selectedStyle.value)?.label ?? "未知风格");
const workflowStatus = computed(() => {
  if (loading.value || demoLoading.value) return "处理中";
  if (response.value) return "已完成";
  return "就绪";
});
const primaryActionLabel = computed(() => (activeMode.value === "ppt" ? "生成 PPT 配图" : "生成演示图表"));
const selectedCandidateScore = computed(() => selectedCandidate.value?.score ?? 0);
const selectedCandidateHint = computed(() => selectedCandidate.value?.hint ?? "当前无候选项");
const previewModeLabel = computed(() => previewTabs.find((item) => item.value === activePreview.value)?.label ?? "对比");
const canGenerate = computed(() => !loading.value && !demoLoading.value);
const selectedPageLabel = computed(() => pageOptions.find((item) => item.value === currentPage.value)?.label ?? "首页");

onMounted(() => {
  window.requestAnimationFrame(() => {
    pageReady.value = true;
  });
  void refreshVisualObservers();
  window.addEventListener("hashchange", syncPageFromHash);
  window.addEventListener("pointermove", updateSpotlight);
});

onBeforeUnmount(() => {
  window.removeEventListener("hashchange", syncPageFromHash);
  window.removeEventListener("pointermove", updateSpotlight);
  metricObserver?.disconnect();
  heroObserver?.disconnect();
});

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function deriveClipScore() {
  const styleBase = {
    tech: 0.17,
    business: 0.15,
    minimal: 0.13,
    education: 0.12,
    medical: 0.11,
    neo: 0.18,
  }[selectedStyle.value] ?? 0.12;
  const modelBase = selectedModel.value === "flux" ? 0.05 : 0.04;
  const controlBase = controlNetEnabled.value ? controlNetStrength.value * 0.1 : 0.02;
  const roundPenalty = (generationRound.value % 4) * 0.01;
  return clamp(0.58 + styleBase + modelBase + controlBase - roundPenalty, 0.58, 0.95);
}

const candidatePool = computed(() => {
  const base = [
    {
      id: "primary",
      title: "主推荐配图",
      subtitle: "语义和风格命中度最高",
      hint: "适合当前主题",
    },
    {
      id: "secondary",
      title: "对比配图 A",
      subtitle: "更强调品牌感与商业感",
      hint: "适合汇报型 PPT",
    },
    {
      id: "tertiary",
      title: "对比配图 B",
      subtitle: "更偏图示化和说明性",
      hint: "适合知识讲解页",
    },
  ];

  const styleBoost = {
    tech: 0.08,
    business: 0.07,
    minimal: 0.05,
    education: 0.04,
    medical: 0.03,
    neo: 0.09,
  }[selectedStyle.value] ?? 0.04;

  const modelBoost = selectedModel.value === "flux" ? 0.04 : 0.03;
  const controlBoost = controlNetEnabled.value ? controlNetStrength.value * 0.06 : 0.01;
  const roundBoost = (generationRound.value % 5) * 0.006;

  return base
    .map((item, index) => ({
      ...item,
      rank: index + 1,
      score: clamp(
        0.68 + styleBoost + modelBoost + controlBoost + roundBoost - index * 0.05,
        0.58,
        0.96,
      ),
      tones: candidateTemplates[index].tones,
      tag: candidateTemplates[index].tag,
    }))
    .sort((a, b) => b.score - a.score);
});

const selectedCandidate = computed(() => candidatePool.value[selectedCandidateIndex.value] ?? candidatePool.value[0] ?? null);
const clipScore = computed(() => {
  const backendScore = Number(pipelineResult.value?.clip_score);
  if (Number.isFinite(backendScore) && backendScore > 0) {
    return clamp(backendScore, 0, 1);
  }
  return candidatePool.value[0]?.score ?? deriveClipScore();
});
const clipScoreText = computed(() => clipScore.value.toFixed(2));
const clipScorePercent = computed(() => Math.round(clipScore.value * 100));
const clipGaugeStyle = computed(() => ({ "--score": String(clipScorePercent.value) }));
const clipStatus = computed(() => {
  if (clipScore.value >= 0.85) return "高度匹配";
  if (clipScore.value >= 0.75) return "匹配良好";
  return "需要微调";
});
const themeClass = computed(() => (themeMode.value === "dark" ? "theme-dark" : "theme-light"));

function handleFileChange(event) {
  const [selected] = event.target.files || [];
  file.value = selected ?? null;
}

function openFilePicker() {
  fileInput.value?.click();
}

function syncPageFromHash() {
  currentPage.value = getPageFromHash();
  void refreshVisualObservers();
}

function navigateTo(page) {
  if (!validPages.includes(page)) return;
  currentPage.value = page;
  if (typeof window !== "undefined") {
    const nextHash = `#/${page}`;
    if (window.location.hash !== nextHash) {
      window.location.hash = nextHash;
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
    void refreshVisualObservers();
  }
}

function updateSpotlight(event) {
  const card = event.target.closest?.(spotlightSelector);
  if (!card) return;
  const rect = card.getBoundingClientRect();
  card.style.setProperty("--spotlight-x", `${event.clientX - rect.left}px`);
  card.style.setProperty("--spotlight-y", `${event.clientY - rect.top}px`);
}

function setupMetricObserver() {
  metricObserver?.disconnect();
  if (typeof window === "undefined" || !("IntersectionObserver" in window)) return;
  metricObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          metricObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.28 },
  );
  document.querySelectorAll("[data-animate-metric]").forEach((item) => metricObserver.observe(item));
}

function setupHeroObserver() {
  heroObserver?.disconnect();
  heroHeadlineVisible.value = false;
  if (currentPage.value !== "home") return;
  if (typeof window === "undefined" || !("IntersectionObserver" in window) || !heroHeadlineRef.value) {
    heroHeadlineVisible.value = true;
    return;
  }
  heroObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          heroHeadlineVisible.value = true;
          heroObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 },
  );
  heroObserver.observe(heroHeadlineRef.value);
}

async function refreshVisualObservers() {
  await nextTick();
  window.requestAnimationFrame(() => {
    setupMetricObserver();
    setupHeroObserver();
  });
}

function startProgress() {
  stopProgress(false);
  progressValue.value = 6;
  stageCards.value = progressTemplate.map((item, index) => ({
    ...item,
    status: index === 0 ? "running" : "pending",
  }));
  progressTimer.value = window.setInterval(() => {
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

function stopProgress(reset) {
  if (progressTimer.value) {
    window.clearInterval(progressTimer.value);
    progressTimer.value = null;
  }
  if (reset) {
    progressValue.value = 0;
    stageCards.value = [];
  }
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
  void refreshVisualObservers();
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
  formData.append("illustration_style", illustrationStyle.value);
  formData.append("image_model", imageModel.value);

  try {
    const res = await fetch("/api/process", {
      method: "POST",
      body: formData,
    });
    const payload = await res.json();
    if (!res.ok) {
      throw new Error(payload.detail || "处理失败，请稍后再试。");
    }
    response.value = payload;
    generationRound.value += 1;
    finalizeProgress(payload.pipeline);
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
  formData.append("illustration_style", illustrationStyle.value);
  formData.append("image_model", imageModel.value);

  try {
    const res = await fetch("/api/demo-chart", {
      method: "POST",
      body: formData,
    });
    const payload = await res.json();
    if (!res.ok) {
      throw new Error(payload.detail || "演示图表生成失败。");
    }
    response.value = payload;
    generationRound.value += 1;
    finalizeProgress(payload.pipeline);
  } catch (error) {
    errorMessage.value = error.message;
    stopProgress(true);
  } finally {
    demoLoading.value = false;
  }
}

<<<<<<< HEAD
async function regenerateIllustration() {
  selectedCandidateIndex.value = 0;
  if (activeMode.value === "ppt") {
    await submitForm();
    return;
=======
function handleFileChange(event) {
  const [selected] = event.target.files || [];
  file.value = selected ?? null;
  uploadToken.value = "";
  slidePreviewUrl.value = "";
  slidePreviewError.value = "";
  slideCount.value = 0;
  slideNumber.value = 1;
  if (file.value) {
    fetchSlidePreview(true);
  }
}

async function fetchSlidePreview(forceUpload = false) {
  if (activeMode.value !== "ppt") {
    return;
  }
  if (!file.value && !uploadToken.value) {
    slidePreviewUrl.value = "";
    slidePreviewError.value = "";
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
    const res = await fetch("/api/slide-preview", {
      method: "POST",
      body: formData,
    });
    const payload = await res.json();
    if (!res.ok) {
      throw new Error(payload.detail || "页预览生成失败。");
    }
    if (currentRequestId !== previewRequestId) {
      return;
    }
    uploadToken.value = payload.upload_token || uploadToken.value;
    slideCount.value = payload.slide_count || 0;
    slidePreviewUrl.value = payload.preview_image_url || "";
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

function stopProgress(reset) {
  if (progressTimer) {
    window.clearInterval(progressTimer);
    progressTimer = null;
  }
  if (reset) {
    progressValue.value = 0;
    stageCards.value = [];
>>>>>>> main
  }
  await runDemo();
}

<<<<<<< HEAD
function selectCandidate(index) {
  selectedCandidateIndex.value = index;
}

function toggleTheme() {
  themeMode.value = themeMode.value === "dark" ? "light" : "dark";
}

function onStyleChange(value) {
  selectedStyle.value = value;
  selectedCandidateIndex.value = 0;
}
=======
function rerunCurrentMode() {
  if (loading.value || demoLoading.value) {
    return;
  }
  if (activeMode.value === "ppt") {
    submitForm();
  } else {
    runDemo();
  }
}

const pipelineResult = computed(() => response.value?.pipeline ?? null);
const chartPreviewUrl = computed(() => pipelineResult.value?.chart_image_url ?? "");
const illustrationPreviewUrl = computed(() => pipelineResult.value?.illustration_image_url ?? "");
const downloadUrl = computed(() => pipelineResult.value?.final_pptx_url ?? "");
const recentLogs = computed(() => pipelineResult.value?.logs ?? []);
const intentInfo = computed(() => pipelineResult.value?.intent ?? null);
const illustrationMeta = computed(() => pipelineResult.value?.illustration_meta ?? null);
const semanticModeLabel = computed(() => (semanticMode.value === "qwen" ? "千问 API" : "本地规则"));
const semanticModeText = computed(() => {
  const mode = intentInfo.value?.semantic_mode || semanticMode.value;
  return mode === "qwen" ? "千问 API" : "本地规则";
});
const clipScoreText = computed(() => {
  const score = illustrationMeta.value?.clip_score ?? intentInfo.value?.clip_score;
  return score == null ? "未评分" : `${score} / 10`;
});
const chartOverrideText = computed(() => {
  const value = chartTypeOverride.value;
  return value === "auto" ? "自动推荐" : value;
});

watch(slideNumber, () => {
  if (activeMode.value === "ppt" && (file.value || uploadToken.value)) {
    fetchSlidePreview(false);
  }
});
>>>>>>> main
</script>

<template>
  <main :class="['app-shell', themeClass, { 'is-ready': pageReady }]">
    <header class="appbar">
      <button type="button" class="brand brand-button" @click="navigateTo('home')">
        <div class="brand-mark">SC</div>
        <div>
          <h1>SmartChart Studio</h1>
          <p>Multi-modal illustration workspace</p>
        </div>
      </button>

      <nav class="appnav" aria-label="主导航">
        <button
          v-for="item in pageOptions"
          :key="item.value"
          type="button"
          class="nav-btn"
          :class="{ active: currentPage === item.value }"
          @click="navigateTo(item.value)"
        >
          {{ item.label }}
        </button>
      </nav>

      <div class="appbar-actions">
        <button type="button" class="ghost-btn" @click="toggleTheme">
          {{ themeMode === "dark" ? "浅色" : "深色" }}
        </button>
        <button
          v-if="currentPage === 'workspace'"
          type="button"
          class="secondary-btn"
          @click="navigateTo('report')"
        >
          查看结果报告
        </button>
        <button v-else type="button" class="primary-btn" @click="navigateTo('workspace')">
          开始生成
        </button>
      </div>
    </header>

    <Transition name="page-fade" mode="out-in">
      <section v-if="currentPage === 'home'" key="home" class="page home-page">
          <section class="hero-panel">
            <div class="hero-copy">
              <span class="eyebrow">SmartChart Multi-modal Pipeline</span>
              <h2 ref="heroHeadlineRef" class="hero-headline" :aria-label="heroHeadlineText">
                <span
                  v-for="(word, index) in heroHeadlineWords"
                  :key="`${word}-${index}`"
                  class="blur-word"
                  :class="{ visible: heroHeadlineVisible }"
                  :style="{ '--word-delay': `${index * 100}ms` }"
                  aria-hidden="true"
                >
                  {{ word }}
                </span>
              </h2>
              <p>
                首页只保留入口，生成工作台专注上传与预览，质量报告单独承接候选配图、语义匹配度和流程日志。
              </p>
            <div class="hero-actions">
              <button type="button" class="primary-btn" @click="navigateTo('workspace')">进入生成工作台</button>
              <button type="button" class="secondary-btn" @click="navigateTo('report')">查看质量报告</button>
            </div>
          </div>
          <div class="hero-card">
            <span class="section-kicker">当前状态</span>
            <strong>{{ workflowStatus }}</strong>
            <p>{{ modelLabel }} · {{ styleLabel }} · CLIP {{ clipScoreText }}</p>
            <div class="hero-meter">
              <span data-animate-metric class="metric-bar" :style="{ width: `${clipScorePercent}%` }"></span>
            </div>
          </div>
        </section>

        <section class="entry-grid">
          <button type="button" class="entry-card primary-entry" @click="navigateTo('workspace')">
            <span>01</span>
            <h3>生成工作台</h3>
            <p>上传 PPT、选择页码、切换模型和风格，保持核心操作区更干净。</p>
          </button>
          <button type="button" class="entry-card" @click="navigateTo('report')">
            <span>02</span>
            <h3>质量报告</h3>
            <p>查看 CLIP 分数、候选配图、流程轨迹和后端日志，不挤占生成页面。</p>
          </button>
          <button type="button" class="entry-card" @click="navigateTo('docs')">
            <span>03</span>
            <h3>使用说明</h3>
            <p>沉淀前端操作说明、风格控制说明和最终展示口径。</p>
          </button>
        </section>

        <section class="overview-strip">
          <article>
            <span>目标质量</span>
            <strong>CLIP ≥ 0.78</strong>
            <p>用于最终配图质量测试报告。</p>
          </article>
          <article>
            <span>模型能力</span>
            <strong>Flux / 通义万相</strong>
            <p>支持双模型切换与重新生成。</p>
          </article>
          <article>
            <span>风格控制</span>
            <strong>ControlNet</strong>
            <p>用强度滑杆控制配图风格约束。</p>
          </article>
        </section>
      </section>

      <section v-else-if="currentPage === 'workspace'" key="workspace" class="page workspace-page">
        <div class="page-toolbar">
          <button type="button" class="back-btn" @click="navigateTo('home')">返回首页</button>
          <div>
            <span class="section-kicker">{{ selectedPageLabel }}</span>
            <h2>生成工作台</h2>
            <p>这里只保留上传、参数和预览；候选图、日志和报告放到二级页面里。</p>
          </div>
          <div class="toolbar-actions">
            <button type="button" class="secondary-btn" @click="navigateTo('report')">查看结果报告</button>
          </div>
        </div>

        <section class="workspace compact-workspace">
      <aside class="rail">
        <div class="rail-block">
          <div class="section-head">
            <div>
              <h2>输入</h2>
              <p>切换来源、模型和生成方式。</p>
            </div>
            <span class="section-kicker">{{ activeMode === "ppt" ? "PPT" : "TEXT" }}</span>
          </div>

<<<<<<< HEAD
          <div class="mode-switch">
            <button type="button" :class="{ active: activeMode === 'ppt' }" @click="activeMode = 'ppt'">
              PPT 模式
            </button>
            <button type="button" :class="{ active: activeMode === 'demo' }" @click="activeMode = 'demo'">
              文本演示
            </button>
          </div>

=======
        <label class="field">
          <span>图表类型修正</span>
          <select v-model="chartTypeOverride">
            <option value="auto">自动推荐</option>
            <option value="bar">柱状图</option>
            <option value="line">折线图</option>
            <option value="pie">饼图</option>
            <option value="scatter">散点图</option>
            <option value="area">面积图</option>
            <option value="histogram">直方图</option>
            <option value="box">箱线图</option>
            <option value="heatmap">热力图</option>
          </select>
        </label>

        <label class="field">
          <span>配图风格</span>
          <select v-model="illustrationStyle">
            <option value="auto">自动</option>
            <option value="business">商务风</option>
            <option value="tech">科技风</option>
            <option value="education">教育风</option>
            <option value="medical">医疗风</option>
            <option value="academic">学术风</option>
            <option value="sketch">手绘风</option>
          </select>
        </label>

        <label class="field">
          <span>配图模型</span>
          <select v-model="imageModel">
            <option value="local">本地预览</option>
            <option value="flux">Flux</option>
            <option value="wanx">通义万相</option>
          </select>
        </label>

        <template v-if="activeMode === 'ppt'">
        <label class="field">
          <span>PPT 文件</span>
          <input type="file" accept=".pptx" @change="handleFileChange" />
        </label>

        <label class="field">
          <span>处理页码<span v-if="slideCount">（共 {{ slideCount }} 页）</span></span>
          <input v-model.number="slideNumber" type="number" min="1" :max="slideCount || undefined" />
        </label>

        <div class="slide-preview-card">
          <div class="preview-card-header">
            <span>当前页预览</span>
            <strong v-if="slidePreviewLoading">加载中...</strong>
          </div>
          <img v-if="slidePreviewUrl" :src="slidePreviewUrl" alt="slide preview" class="slide-preview-image" />
          <p v-else-if="slidePreviewError" class="status error">{{ slidePreviewError }}</p>
          <p v-else class="placeholder">上传 PPT 后，切换页码时会在这里实时显示当前页。</p>
        </div>

        <button class="primary-btn" :disabled="loading" @click="submitForm">
          {{ loading ? "处理中..." : "一键生成图表与配图" }}
        </button>
        </template>

        <template v-else>
>>>>>>> main
          <label class="field">
            <span>语义分析模式</span>
            <select v-model="semanticMode">
              <option value="local">本地规则</option>
              <option value="qwen">千问 API</option>
            </select>
          </label>

          <template v-if="activeMode === 'ppt'">
            <div class="field upload-field">
              <span>PPT 文件</span>
              <div class="upload-row">
                <input
                  ref="fileInput"
                  class="visually-hidden"
                  type="file"
                  accept=".pptx"
                  @change="handleFileChange"
                />
                <button type="button" class="upload-trigger" @click="openFilePicker">
                  {{ fileInfo ? "重新选择" : "选择文件" }}
                </button>
                <div class="upload-copy">
                  <strong>{{ fileInfo ? fileInfo.name : "未选择文件" }}</strong>
                  <span>{{ fileInfo ? fileInfo.size : "支持 .pptx 文件上传" }}</span>
                </div>
              </div>
            </div>

            <label class="field">
              <span>处理页码</span>
              <input v-model.number="slideNumber" type="number" min="1" />
            </label>
          </template>

          <template v-else>
            <label class="field">
              <span>业务文本</span>
              <textarea v-model="demoText" rows="8" placeholder="例如：营收: 120"></textarea>
            </label>
          </template>

          <div class="button-row">
            <button
              type="button"
              class="primary-btn"
              :disabled="loading || demoLoading"
              @click="activeMode === 'ppt' ? submitForm() : runDemo()"
            >
              {{ loading || demoLoading ? "处理中..." : primaryActionLabel }}
            </button>
            <button type="button" class="secondary-btn" :disabled="loading || demoLoading" @click="regenerateIllustration">
              重新生成配图
            </button>
          </div>

          <div class="progress-card">
            <div class="progress-meta">
              <span>处理进度 · {{ semanticModeLabel }}</span>
              <strong>{{ progressValue }}%</strong>
            </div>
            <div class="progress-track">
              <div
                data-animate-metric
                class="progress-fill metric-bar"
                :style="{ width: `${progressValue}%` }"
              ></div>
            </div>
          </div>

          <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>
        </div>

        <div class="rail-block">
          <div class="section-head">
            <div>
              <h2>风格</h2>
              <p>模型、风格和风控参数。</p>
            </div>
            <span class="section-kicker">STYLE</span>
          </div>

          <div class="chip-group">
            <button
              v-for="item in modelOptions"
              :key="item.value"
              type="button"
              class="chip-btn"
              :class="{ active: selectedModel === item.value }"
              @click="selectedModel = item.value"
            >
              {{ item.label }}
            </button>
          </div>

          <div class="chip-group wrap">
            <button
              v-for="item in styleOptions"
              :key="item.value"
              type="button"
              class="chip-btn"
              :class="{ active: selectedStyle === item.value }"
              @click="onStyleChange(item.value)"
            >
              {{ item.label }}
            </button>
          </div>

          <div class="switch-row">
            <span>ControlNet 风格控制</span>
            <button type="button" class="switch-btn" @click="controlNetEnabled = !controlNetEnabled">
              {{ controlNetEnabled ? "已开启" : "已关闭" }}
            </button>
          </div>

          <label class="field">
            <span>ControlNet 强度：{{ Math.round(controlNetStrength * 100) }}%</span>
            <input v-model.number="controlNetStrength" type="range" min="0.1" max="1" step="0.01" />
          </label>
        </div>
      </aside>

      <section class="stage">
        <div class="section-head stage-head">
          <div>
            <h2>预览画布</h2>
            <p>图表、配图和对比视图会在这里同步展示。</p>
          </div>
          <div class="stage-actions">
            <span class="section-kicker">{{ previewModeLabel }}</span>
            <div class="tab-switch">
              <button
                v-for="tab in previewTabs"
                :key="tab.value"
                type="button"
                class="tab-btn"
                :class="{ active: activePreview === tab.value }"
                @click="activePreview = tab.value"
              >
                {{ tab.label }}
              </button>
            </div>
          </div>
        </div>

<<<<<<< HEAD
        <div class="canvas-shell">
          <Transition name="panel-swap" mode="out-in">
            <div :key="activePreview" class="preview-switcher">
              <template v-if="activePreview === 'chart'">
                <div v-if="chartPreviewUrl" class="preview-frame reveal-frame">
                  <img :src="chartPreviewUrl" alt="chart preview" />
                </div>
                <div v-else class="empty-state">
                  <div class="empty-bars">
                    <span></span><span></span><span></span><span></span>
                  </div>
                  <p>图表结果会显示在这里</p>
                </div>
              </template>

              <template v-else-if="activePreview === 'illustration'">
                <div v-if="illustrationPreviewUrl" class="preview-frame reveal-frame">
                  <img :src="illustrationPreviewUrl" alt="illustration preview" />
                </div>
                <div v-else class="empty-state illustration-state">
                  <div class="empty-illustration">
                    <span></span><span></span><span></span>
                  </div>
                  <p>配图结果会显示在这里</p>
                </div>
              </template>

              <template v-else>
                <div class="compare-grid">
                  <article class="compare-panel">
                    <div class="compare-head">
                      <strong>图表</strong>
                      <span>{{ chartPreviewUrl ? "已生成" : "等待生成" }}</span>
                    </div>
                    <div v-if="chartPreviewUrl" class="preview-frame small reveal-frame">
                      <img :src="chartPreviewUrl" alt="chart preview" />
                    </div>
                    <div v-else class="empty-state small">
                      <div class="empty-bars">
                        <span></span><span></span><span></span><span></span>
                      </div>
                      <p>图表结果会显示在这里</p>
                    </div>
                  </article>

                  <article class="compare-panel">
                    <div class="compare-head">
                      <strong>配图</strong>
                      <span>{{ illustrationPreviewUrl ? "已生成" : "等待生成" }}</span>
                    </div>
                    <div v-if="illustrationPreviewUrl" class="preview-frame small reveal-frame">
                      <img :src="illustrationPreviewUrl" alt="illustration preview" />
                    </div>
                    <div v-else class="empty-state small illustration-state">
                      <div class="empty-illustration">
                        <span></span><span></span><span></span>
                      </div>
                      <p>配图结果会显示在这里</p>
                    </div>
                  </article>
                </div>
              </template>
            </div>
          </Transition>
=======
        <button class="secondary-btn" :disabled="loading || demoLoading" @click="rerunCurrentMode">
          重新生成当前结果
        </button>

        <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>
      </div>

      <div class="panel">
        <h2>文件基本信息</h2>
        <div v-if="fileInfo" class="info-list">
          <p><strong>文件名：</strong>{{ fileInfo.name }}</p>
          <p><strong>文件大小：</strong>{{ fileInfo.size }}</p>
          <p><strong>文件类型：</strong>{{ fileInfo.type }}</p>
          <p><strong>修改时间：</strong>{{ fileInfo.lastModified }}</p>
          <p><strong>目标页码：</strong>{{ slideNumber }}</p>
          <p v-if="slideCount"><strong>PPT 总页数：</strong>{{ slideCount }}</p>
>>>>>>> main
        </div>

<<<<<<< HEAD
        <div class="canvas-footer">
          <span class="metric-chip">CLIP {{ clipScoreText }}</span>
          <span class="metric-chip">{{ clipStatus }}</span>
          <span class="metric-chip">轮次 {{ generationRound }}</span>
          <span class="metric-chip">页码 {{ slideNumber }}</span>
=======
    <section class="result-grid">
      <div class="panel preview-panel">
        <h2>图表预览区</h2>
        <img v-if="chartPreviewUrl" :src="chartPreviewUrl" alt="chart preview" class="preview-image" />
        <p v-else class="placeholder">处理完成后，这里会展示图表 PNG 或本地预览图。</p>
      </div>

      <div class="panel preview-panel">
        <h2>配图区</h2>
        <img v-if="illustrationPreviewUrl" :src="illustrationPreviewUrl" alt="illustration preview" class="preview-image" />
        <p v-else class="placeholder">处理完成后，这里会展示配图预览。</p>
      </div>
    </section>

    <section class="result-grid secondary-grid">
      <div class="panel result-panel">
        <h2>Pipeline 日志与状态</h2>
        <div v-if="intentInfo" class="intent-card">
          <p><strong>推荐图表：</strong>{{ intentInfo.chart_type }}</p>
          <p><strong>语义来源：</strong>{{ intentInfo.source || "heuristic" }}</p>
          <p><strong>所选模式：</strong>{{ semanticModeText }}</p>
          <p><strong>手动修正：</strong>{{ chartOverrideText }}</p>
          <p><strong>判断依据：</strong>{{ intentInfo.reason || intentInfo.summary }}</p>
          <p><strong>配图主题：</strong>{{ intentInfo.visual_theme || "未提供" }}</p>
          <p><strong>配图模型：</strong>{{ illustrationMeta?.image_model || intentInfo.image_model || imageModel }}</p>
          <p><strong>配图风格：</strong>{{ illustrationMeta?.illustration_style || intentInfo.illustration_style || illustrationStyle }}</p>
          <p><strong>匹配分数：</strong>{{ clipScoreText }}</p>
          <p v-if="illustrationMeta?.regenerate_hint" class="warning-text">当前配图匹配分数偏低，建议点击“重新生成当前结果”。</p>
>>>>>>> main
        </div>
      </section>

      <aside class="rail">
        <div class="rail-block">
          <div class="section-head">
            <div>
              <h2>结果摘要</h2>
              <p>配置、匹配度和当前候选项。</p>
            </div>
            <span class="section-kicker">{{ workflowStatus }}</span>
          </div>

          <div class="summary-list">
            <div class="summary-item">
              <span>模型</span>
              <strong>{{ modelLabel }}</strong>
            </div>
            <div class="summary-item">
              <span>风格</span>
              <strong>{{ styleLabel }}</strong>
            </div>
            <div class="summary-item">
              <span>ControlNet</span>
              <strong>{{ controlNetEnabled ? "开启" : "关闭" }}</strong>
            </div>
            <div class="summary-item">
              <span>ControlNet 强度</span>
              <strong>{{ Math.round(controlNetStrength * 100) }}%</strong>
            </div>
            <div class="summary-item">
              <span>CLIP 评分</span>
              <strong>{{ clipScoreText }}</strong>
            </div>
            <div class="summary-item">
              <span>语义模式</span>
              <strong>{{ semanticModeLabel }}</strong>
            </div>
          </div>

          <div v-if="fileInfo" class="file-card">
            <p><span>文件名</span><strong>{{ fileInfo.name }}</strong></p>
            <p><span>文件大小</span><strong>{{ fileInfo.size }}</strong></p>
            <p><span>文件类型</span><strong>{{ fileInfo.type }}</strong></p>
            <p><span>修改时间</span><strong>{{ fileInfo.lastModified }}</strong></p>
            <p><span>目标页码</span><strong>{{ slideNumber }}</strong></p>
          </div>

          <div class="clip-meter">
            <div class="clip-meter-top">
              <span>语义匹配度</span>
              <strong>{{ clipScoreText }}</strong>
            </div>
            <div class="progress-track">
              <div class="progress-fill clip-fill" :style="{ width: `${clipScorePercent}%` }"></div>
            </div>
            <p class="clip-note">当前结果：{{ clipStatus }}</p>
          </div>

          <div class="candidate-list">
            <button
              v-for="(item, index) in candidatePool"
              :key="item.id"
              type="button"
              class="candidate-row"
              :class="{ active: selectedCandidateIndex === index }"
              @click="selectCandidate(index)"
            >
              <div class="candidate-swatch" :style="{ background: `linear-gradient(135deg, ${item.tones[0]}, ${item.tones[1]})` }"></div>
              <div class="candidate-copy">
                <div class="candidate-title">
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.score.toFixed(2) }}</span>
                </div>
                <p>{{ item.subtitle }}</p>
                <div class="candidate-bar">
                  <span :style="{ width: `${Math.round(item.score * 100)}%` }"></span>
                </div>
              </div>
            </button>
          </div>

          <div v-if="selectedCandidate" class="candidate-detail">
            <div class="candidate-detail-head">
              <strong>{{ selectedCandidate.title }}</strong>
              <span>Rank {{ selectedCandidate.rank }}</span>
            </div>
            <p>{{ selectedCandidate.subtitle }}</p>
            <div class="candidate-detail-meta">
              <span>{{ selectedCandidateHint }}</span>
              <strong>{{ selectedCandidateScore.toFixed(2) }}</strong>
            </div>
          </div>
        </div>

<<<<<<< HEAD
        <div class="rail-block">
          <div class="section-head">
            <div>
              <h2>流程轨迹</h2>
              <p>语义判断、生成步骤与输出日志。</p>
            </div>
            <span class="section-kicker">TRACE</span>
          </div>

          <div v-if="intentInfo" class="intent-card">
            <p><span>推荐图表</span><strong>{{ intentInfo.chart_type }}</strong></p>
            <p><span>语义来源</span><strong>{{ intentInfo.source || 'heuristic' }}</strong></p>
            <p><span>判断依据</span><strong>{{ intentInfo.reason || intentInfo.summary }}</strong></p>
            <p><span>配图主题</span><strong>{{ intentInfo.visual_theme || '未提供' }}</strong></p>
          </div>

          <div class="stage-list">
            <div v-for="item in stageCards" :key="item.stage + item.status" class="stage-item">
              <span>{{ item.label }}</span>
              <strong :class="`stage-${item.status}`">{{ item.status }}</strong>
            </div>
          </div>

          <div v-if="recentLogs.length" class="log-list">
            <p v-for="log in recentLogs" :key="log">{{ log }}</p>
          </div>
          <pre v-else-if="response">{{ JSON.stringify(response, null, 2) }}</pre>
          <p v-else class="placeholder">处理完成后，这里会展示后端返回结构化结果和阶段日志。</p>

          <a v-if="downloadUrl" :href="downloadUrl" class="download-link">下载增强版 PPT</a>
        </div>
      </aside>
        </section>
      </section>

      <section v-else-if="currentPage === 'report'" key="report" class="page report-page">
        <div class="page-toolbar">
          <button type="button" class="back-btn" @click="navigateTo('workspace')">返回工作台</button>
          <div>
            <span class="section-kicker">{{ selectedPageLabel }}</span>
            <h2>质量报告</h2>
            <p>把结果摘要、候选配图、CLIP 分数和流程日志放在独立页面，阅读压力会小很多。</p>
          </div>
          <div class="toolbar-actions">
            <button type="button" class="secondary-btn" @click="navigateTo('docs')">查看说明文档</button>
          </div>
        </div>

        <section class="report-grid">
          <article class="report-card">
            <div class="section-head">
              <div>
                <h2>结果摘要</h2>
                <p>配置、匹配度和当前候选项。</p>
              </div>
              <span class="section-kicker">{{ workflowStatus }}</span>
            </div>

            <div class="summary-list">
              <div class="summary-item">
                <span>模型</span>
                <strong>{{ modelLabel }}</strong>
              </div>
              <div class="summary-item">
                <span>风格</span>
                <strong>{{ styleLabel }}</strong>
              </div>
              <div class="summary-item">
                <span>ControlNet</span>
                <strong>{{ controlNetEnabled ? "开启" : "关闭" }}</strong>
              </div>
              <div class="summary-item">
                <span>CLIP 评分</span>
                <strong>{{ clipScoreText }}</strong>
              </div>
            </div>

            <div v-if="fileInfo" class="file-card">
              <p><span>文件名</span><strong>{{ fileInfo.name }}</strong></p>
              <p><span>文件大小</span><strong>{{ fileInfo.size }}</strong></p>
              <p><span>修改时间</span><strong>{{ fileInfo.lastModified }}</strong></p>
              <p><span>目标页码</span><strong>{{ slideNumber }}</strong></p>
            </div>

            <div class="gauge-card" :style="clipGaugeStyle">
              <div data-animate-metric class="gauge-ring metric-ring">
                <div class="gauge-core">
                  <span>语义匹配度</span>
                  <strong>{{ clipScoreText }}</strong>
                  <p>{{ clipStatus }}</p>
                </div>
              </div>
              <div class="gauge-caption">
                <span>当前结果</span>
                <strong>{{ clipStatus }}</strong>
              </div>
            </div>
          </article>

          <article class="report-card">
            <div class="section-head">
              <div>
                <h2>候选配图</h2>
                <p>用于对比预览和重新生成判断。</p>
              </div>
              <span class="section-kicker">RANK</span>
            </div>

            <div class="candidate-list">
              <button
                v-for="(item, index) in candidatePool"
                :key="item.id"
                type="button"
                class="candidate-row"
                :class="{ active: selectedCandidateIndex === index }"
                @click="selectCandidate(index)"
              >
                <div class="candidate-swatch" :style="{ background: `linear-gradient(135deg, ${item.tones[0]}, ${item.tones[1]})` }"></div>
                <div class="candidate-copy">
                  <div class="candidate-title">
                    <strong>{{ item.title }}</strong>
                    <span>{{ item.score.toFixed(2) }}</span>
                  </div>
                  <p>{{ item.subtitle }}</p>
                  <div class="candidate-bar">
                    <span
                      data-animate-metric
                      class="metric-bar"
                      :style="{ width: `${Math.round(item.score * 100)}%` }"
                    ></span>
                  </div>
                </div>
              </button>
            </div>

            <div v-if="selectedCandidate" class="candidate-detail">
              <div class="candidate-detail-head">
                <strong>{{ selectedCandidate.title }}</strong>
                <span>Rank {{ selectedCandidate.rank }}</span>
              </div>
              <p>{{ selectedCandidate.subtitle }}</p>
              <div class="candidate-detail-meta">
                <span>{{ selectedCandidateHint }}</span>
                <strong>{{ selectedCandidateScore.toFixed(2) }}</strong>
              </div>
            </div>
          </article>

          <article class="report-card wide-card">
            <div class="section-head">
              <div>
                <h2>流程轨迹</h2>
                <p>语义判断、生成步骤与输出日志。</p>
              </div>
              <span class="section-kicker">TRACE</span>
            </div>

            <div v-if="intentInfo" class="intent-card">
              <p><span>推荐图表</span><strong>{{ intentInfo.chart_type }}</strong></p>
              <p><span>语义来源</span><strong>{{ intentInfo.source || "heuristic" }}</strong></p>
              <p><span>判断依据</span><strong>{{ intentInfo.reason || intentInfo.summary }}</strong></p>
              <p><span>配图主题</span><strong>{{ intentInfo.visual_theme || "未提供" }}</strong></p>
            </div>

            <div class="stage-list">
              <div v-for="item in stageCards" :key="item.stage + item.status" class="stage-item">
                <span>{{ item.label }}</span>
                <strong :class="`stage-${item.status}`">{{ item.status }}</strong>
              </div>
            </div>

            <div v-if="recentLogs.length" class="log-list">
              <p v-for="log in recentLogs" :key="log">{{ log }}</p>
            </div>
            <pre v-else-if="response">{{ JSON.stringify(response, null, 2) }}</pre>
            <p v-else class="placeholder">处理完成后，这里会展示后端返回结构化结果和阶段日志。</p>

            <a v-if="downloadUrl" :href="downloadUrl" class="download-link">下载增强版 PPT</a>
          </article>
        </section>
      </section>

      <section v-else key="docs" class="page docs-page">
        <div class="page-toolbar">
          <button type="button" class="back-btn" @click="navigateTo('home')">返回首页</button>
          <div>
            <span class="section-kicker">{{ selectedPageLabel }}</span>
            <h2>前端使用说明与风格控制文档</h2>
            <p>这里可以作为你后续提交“前端使用说明 + 风格控制文档”的雏形。</p>
          </div>
          <div class="toolbar-actions">
            <button type="button" class="secondary-btn" @click="navigateTo('workspace')">去工作台</button>
          </div>
        </div>

        <section class="docs-grid">
          <article class="doc-card">
            <h3>推荐操作流程</h3>
            <ol class="step-list">
              <li>进入生成工作台，选择 PPT 模式或文本演示。</li>
              <li>上传 PPTX 文件并填写目标页码。</li>
              <li>选择语义分析模式、配图模型和风格标签。</li>
              <li>调整 ControlNet 强度后点击生成。</li>
              <li>进入质量报告页查看 CLIP 分数、候选配图和流程日志。</li>
            </ol>
          </article>

          <article class="doc-card">
            <h3>风格控制说明</h3>
            <div class="style-doc-grid">
              <div v-for="item in styleGuideCards" :key="item.value" class="style-doc-item">
                <span class="style-icon" :style="{ background: `linear-gradient(135deg, ${item.accent[0]}, ${item.accent[1]})` }">
                  {{ item.glyph }}
                </span>
                <div>
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.copy }}</span>
                </div>
              </div>
            </div>
          </article>

          <article class="doc-card">
            <h3>质量报告口径</h3>
            <p>
              当前页面展示的是前端侧的质量报告结构：CLIP 分数、平均目标、候选图排名、流程日志和下载入口。
              后续如果后端补充真实 CLIP 批量结果，可以直接映射到这里。
            </p>
            <div class="quality-target">
              <span>最终目标</span>
              <strong>CLIP 平均 ≥ 0.78</strong>
            </div>
          </article>
        </section>
      </section>
    </Transition>
=======
      <div class="panel milestone-panel">
        <h2>前五周交付</h2>
        <ul>
          <li>上传 PPT、页码选择、基础信息与日志展示</li>
          <li>实时进度条、重试状态、图表预览区与配图区</li>
          <li>文本到图表演示、千问 / 本地双模式切换</li>
          <li>图表类型手动修正、配图模型与风格选择</li>
          <li>增强版 PPT 下载输出</li>
        </ul>
        <a v-if="downloadUrl" :href="downloadUrl" class="download-link">下载增强版 PPT</a>
      </div>
    </section>
>>>>>>> main
  </main>
</template>

<style scoped>
.app-shell {
  --bg: #f6f8fb;
  --surface: rgba(255, 255, 255, 0.82);
  --surface-strong: #ffffff;
  --surface-soft: rgba(255, 255, 255, 0.68);
  --text: #0f172a;
  --muted: #5f6c86;
  --border: rgba(15, 23, 42, 0.06);
  --accent: #1a73e8;
  --accent-strong: #0f5de7;
  --accent-weak: rgba(26, 115, 232, 0.1);
  --accent-ghost: rgba(94, 92, 230, 0.08);
  --shadow: 0 24px 58px rgba(15, 23, 42, 0.06);
  position: relative;
  isolation: isolate;
  min-height: 100vh;
  color: var(--text);
  background:
    radial-gradient(circle at 10% 8%, rgba(16, 185, 129, 0.14), transparent 28%),
    radial-gradient(circle at 92% 0%, rgba(26, 115, 232, 0.14), transparent 24%),
    linear-gradient(180deg, #f8fbff 0%, #eef3f8 100%);
}

.app-shell.theme-dark {
  --bg: #0b1220;
  --surface: rgba(15, 23, 42, 0.76);
  --surface-strong: #111827;
  --surface-soft: rgba(15, 23, 42, 0.56);
  --text: #e5eefb;
  --muted: #a1aec0;
  --border: rgba(148, 163, 184, 0.14);
  --accent: #6ea8fe;
  --accent-strong: #4d8df7;
  --accent-weak: rgba(110, 168, 254, 0.14);
  --accent-ghost: rgba(110, 168, 254, 0.08);
  --shadow: 0 30px 70px rgba(2, 6, 23, 0.3);
  background:
    radial-gradient(circle at 10% 10%, rgba(16, 185, 129, 0.08), transparent 28%),
    radial-gradient(circle at 92% 0%, rgba(110, 168, 254, 0.08), transparent 24%),
    linear-gradient(180deg, #0b1220 0%, #111827 100%);
}

.appbar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  backdrop-filter: blur(16px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-button {
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--accent), #10b981);
  color: #ffffff;
  font-size: 13px;
  font-weight: 700;
}

.brand h1 {
  margin: 0;
  font-size: 17px;
  line-height: 1.2;
}

.brand p {
  margin: 3px 0 0;
  font-size: 12px;
  color: var(--muted);
}

.appnav {
  display: inline-flex;
  justify-content: center;
  gap: 6px;
  padding: 4px;
  justify-self: center;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--surface-soft);
}

.nav-btn {
  min-height: 34px;
  padding: 7px 12px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
  transition: color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.nav-btn:hover,
.nav-btn.active {
  color: var(--text);
  background: var(--surface-strong);
}

.nav-btn.active {
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

.appbar-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.meta-pill,
.section-kicker,
.metric-chip {
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--accent-weak);
  color: var(--text);
  font-size: 12px;
}

.meta-pill {
  padding: 8px 12px;
}

.appbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ghost-btn,
.primary-btn,
.secondary-btn,
.mode-switch button,
.chip-btn,
.tab-btn,
.switch-btn,
.upload-trigger {
  border-radius: 12px;
  border: 1px solid var(--border);
  font: inherit;
  transition:
    transform 0.18s ease,
    background 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    color 0.18s ease,
    opacity 0.18s ease;
}

.ghost-btn,
.secondary-btn,
.mode-switch button,
.chip-btn,
.tab-btn,
.switch-btn,
.upload-trigger {
  background: var(--surface-soft);
  color: var(--text);
}

.ghost-btn,
.primary-btn,
.secondary-btn {
  padding: 10px 14px;
  cursor: pointer;
  font-weight: 600;
}

.primary-btn {
  border-color: transparent;
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  background-size: 160% 160%;
  color: #ffffff;
  box-shadow: 0 12px 24px rgba(26, 115, 232, 0.24);
}

.secondary-btn {
  background: linear-gradient(180deg, var(--surface-strong), var(--surface-soft));
  border-color: var(--border);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.ghost-btn:hover:not(:disabled),
.primary-btn:hover:not(:disabled),
.secondary-btn:hover:not(:disabled),
.mode-switch button:hover,
.chip-btn:hover,
.tab-btn:hover,
.switch-btn:hover,
.upload-trigger:hover {
  transform: translateY(-1px);
}

.ghost-btn:hover:not(:disabled),
.secondary-btn:hover:not(:disabled),
.mode-switch button:hover,
.chip-btn:hover,
.tab-btn:hover,
.switch-btn:hover {
  border-color: rgba(26, 115, 232, 0.28);
  background: rgba(26, 115, 232, 0.06);
}

.primary-btn:focus-visible,
.secondary-btn:focus-visible,
.ghost-btn:focus-visible,
.mode-switch button:focus-visible,
.chip-btn:focus-visible,
.tab-btn:focus-visible,
.switch-btn:focus-visible,
.upload-trigger:focus-visible {
  outline: 2px solid rgba(26, 115, 232, 0.35);
  outline-offset: 2px;
}

.primary-btn:disabled,
.secondary-btn:disabled,
.ghost-btn:disabled {
  cursor: wait;
  opacity: 0.6;
  box-shadow: none;
}

.page {
  position: relative;
  z-index: 1;
  max-width: 1320px;
  margin: 0 auto;
  padding: 28px 20px 36px;
}

.home-page {
  display: grid;
  gap: 18px;
}

.hero-panel,
.entry-card,
.overview-strip article,
.page-toolbar,
.report-card,
.doc-card {
  border: 1px solid var(--border);
  border-radius: 20px;
  background: var(--surface);
  box-shadow: var(--shadow);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.hero-card,
.entry-card,
.overview-strip article,
.page-toolbar,
.report-card,
.doc-card,
.stage,
.rail-block,
.summary-item,
.candidate-row,
.compare-panel,
.file-card,
.intent-card,
.gauge-card,
.stage-item {
  position: relative;
  overflow: hidden;
  isolation: isolate;
}

.hero-card::before,
.entry-card::before,
.overview-strip article::before,
.page-toolbar::before,
.report-card::before,
.doc-card::before,
.stage::before,
.rail-block::before,
.summary-item::before,
.candidate-row::before,
.compare-panel::before,
.file-card::before,
.intent-card::before,
.gauge-card::before,
.stage-item::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1.2px;
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.48) 0%,
    rgba(255, 255, 255, 0.16) 18%,
    rgba(255, 255, 255, 0) 40%,
    rgba(255, 255, 255, 0) 60%,
    rgba(125, 211, 252, 0.18) 82%,
    rgba(255, 255, 255, 0.44) 100%
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  opacity: 0.78;
}

.hero-panel {
  min-height: 360px;
  padding: 36px;
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.8fr);
  gap: 24px;
  align-items: end;
  overflow: hidden;
  position: relative;
  isolation: isolate;
  background:
    radial-gradient(circle at var(--spotlight-x, 50%) var(--spotlight-y, 50%), rgba(26, 115, 232, 0.18), transparent 42%),
    radial-gradient(circle at 16% 18%, rgba(26, 115, 232, 0.16), transparent 34%),
    radial-gradient(circle at 86% 24%, rgba(16, 185, 129, 0.14), transparent 30%),
    var(--surface);
}

.hero-panel::before,
.hero-panel::after {
  content: "";
  position: absolute;
  z-index: 0;
  pointer-events: none;
}

.hero-panel::before {
  right: 48px;
  top: 32px;
  width: 200px;
  height: 200px;
  border-radius: 36px;
  border: 1px solid rgba(26, 115, 232, 0.14);
  background:
    linear-gradient(135deg, rgba(26, 115, 232, 0.12), rgba(16, 185, 129, 0.08)),
    radial-gradient(circle at 28% 28%, rgba(255, 255, 255, 0.45), transparent 30%);
  transform: rotate(14deg);
  filter: blur(0.2px);
  opacity: 0.9;
}

.hero-panel::after {
  right: 16px;
  bottom: 28px;
  width: 280px;
  height: 170px;
  border-radius: 999px;
  border: 1px solid rgba(26, 115, 232, 0.12);
  background:
    linear-gradient(90deg, rgba(26, 115, 232, 0.08), rgba(16, 185, 129, 0.06)),
    radial-gradient(circle, rgba(255, 255, 255, 0.45), transparent 58%);
  transform: skewX(-8deg);
  opacity: 0.75;
}

.hero-copy {
  max-width: 760px;
  position: relative;
  z-index: 1;
}

.eyebrow {
  display: inline-flex;
  margin-bottom: 14px;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-copy h2,
.page-toolbar h2 {
  margin: 0;
  color: var(--text);
}

.hero-headline {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  row-gap: 0.12em;
  font-size: clamp(32px, 5vw, 56px);
  line-height: 1.05;
  letter-spacing: -0.05em;
}

.blur-word {
  display: inline-block;
  margin-right: 0.28em;
  opacity: 0;
  filter: blur(10px);
  transform: translate3d(0, 28px, 0);
  will-change: transform, opacity, filter;
}

.blur-word.visible {
  animation: heroWordReveal 700ms ease-out both;
  animation-delay: var(--word-delay, 0ms);
}

.hero-copy p,
.page-toolbar p,
.entry-card p,
.overview-strip p,
.doc-card p {
  color: var(--muted);
  line-height: 1.65;
}

.hero-copy p {
  max-width: 620px;
  margin: 18px 0 0;
  font-size: 16px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
}

.hero-card {
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background:
    radial-gradient(circle at 18% 18%, rgba(255, 255, 255, 0.28), transparent 34%),
    linear-gradient(180deg, var(--surface-strong), var(--surface-soft));
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  position: relative;
  z-index: 1;
}

.hero-card strong {
  display: block;
  margin-top: 18px;
  font-size: 34px;
  letter-spacing: -0.04em;
}

.hero-card p {
  margin: 8px 0 18px;
  color: var(--muted);
}

.hero-meter {
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--accent-weak);
}

.hero-meter span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #10b981, var(--accent));
}

.entry-grid,
.overview-strip,
.report-grid,
.docs-grid {
  display: grid;
  gap: 16px;
}

.entry-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.entry-card {
  min-height: 210px;
  padding: 22px;
  text-align: left;
  color: var(--text);
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
  position: relative;
  overflow: hidden;
  isolation: isolate;
  background:
    radial-gradient(circle at var(--spotlight-x, 50%) var(--spotlight-y, 50%), rgba(26, 115, 232, 0.18), transparent 42%),
    linear-gradient(180deg, var(--surface-strong), var(--surface-soft));
}

.entry-card > * {
  position: relative;
  z-index: 1;
}

.entry-card:hover {
  transform: translateY(-3px);
  border-color: rgba(26, 115, 232, 0.28);
  box-shadow: 0 20px 46px rgba(15, 23, 42, 0.1);
}

.entry-card span {
  display: inline-flex;
  padding: 7px 10px;
  border-radius: 10px;
  background: var(--accent-weak);
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
}

.entry-card::after {
  position: absolute;
  right: 18px;
  top: 10px;
  z-index: 0;
  color: var(--accent);
  font-size: 66px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.08em;
  opacity: 0.08;
  pointer-events: none;
}

.entry-card:nth-child(1)::after {
  content: "01";
}

.entry-card:nth-child(2)::after {
  content: "02";
}

.entry-card:nth-child(3)::after {
  content: "03";
}

.entry-card h3,
.doc-card h3 {
  margin: 18px 0 8px;
  font-size: 20px;
}

.primary-entry {
  background:
    radial-gradient(circle at var(--spotlight-x, 50%) var(--spotlight-y, 50%), rgba(26, 115, 232, 0.18), transparent 42%),
    linear-gradient(135deg, rgba(26, 115, 232, 0.12), transparent),
    linear-gradient(180deg, var(--surface-strong), var(--surface-soft));
}

.overview-strip {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.overview-strip article,
.report-card,
.doc-card {
  padding: 22px;
  background:
    radial-gradient(circle at var(--spotlight-x, 50%) var(--spotlight-y, 50%), rgba(26, 115, 232, 0.12), transparent 42%),
    var(--surface);
}

.overview-strip span,
.quality-target span {
  color: var(--muted);
  font-size: 12px;
}

.overview-strip strong,
.quality-target strong {
  display: block;
  margin-top: 6px;
  font-size: 20px;
}

.page-toolbar {
  margin-bottom: 16px;
  padding: 18px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
  background:
    radial-gradient(circle at var(--spotlight-x, 50%) var(--spotlight-y, 50%), rgba(26, 115, 232, 0.14), transparent 42%),
    linear-gradient(180deg, var(--surface-strong), var(--surface-soft));
}

.page-toolbar h2 {
  margin-top: 8px;
  font-size: 28px;
  letter-spacing: -0.03em;
}

.page-toolbar p {
  margin: 6px 0 0;
}

.toolbar-actions {
  display: flex;
  justify-content: flex-end;
}

.back-btn,
.text-action {
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--surface-soft);
  color: var(--text);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.back-btn {
  padding: 10px 14px;
}

.back-btn::before {
  content: "←";
  margin-right: 6px;
}

.text-action {
  padding: 8px 12px;
  color: var(--accent);
}

.report-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.report-card {
  min-width: 0;
}

.wide-card {
  grid-column: 1 / -1;
}

.docs-grid {
  grid-template-columns: minmax(240px, 3fr) minmax(0, 6fr) minmax(240px, 3fr);
}

.step-list {
  margin: 12px 0 0;
  padding-left: 20px;
  color: var(--muted);
  line-height: 1.8;
}

.style-doc-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.style-doc-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
  margin: 0;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background:
    linear-gradient(180deg, var(--surface-strong), var(--surface-soft)),
    var(--surface-soft);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

.style-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.12);
}

.style-doc-item strong,
.style-doc-item span {
  display: block;
}

.style-doc-item span {
  margin-top: 6px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.55;
}

.quality-target {
  margin-top: 18px;
  padding: 18px;
  border-radius: 16px;
  background: var(--accent-weak);
}

.workspace {
  max-width: 1600px;
  margin: 0 auto;
  padding: 16px 20px 28px;
  display: grid;
  grid-template-columns: minmax(300px, 340px) minmax(0, 1fr) minmax(300px, 360px);
  gap: 16px;
  align-items: start;
}

.compact-workspace {
  max-width: 1320px;
  padding: 0;
  grid-template-columns: minmax(280px, 320px) minmax(0, 1.35fr);
}

.compact-workspace > .rail:last-child {
  display: none;
}

.rail,
.stage {
  border: 1px solid var(--border);
  border-radius: 14px;
  background:
    radial-gradient(circle at var(--spotlight-x, 50%) var(--spotlight-y, 50%), rgba(26, 115, 232, 0.12), transparent 42%),
    var(--surface);
  box-shadow: var(--shadow);
  backdrop-filter: blur(16px);
  position: relative;
  overflow: hidden;
  isolation: isolate;
}

.rail {
  position: sticky;
  top: 76px;
  padding: 14px;
  align-self: start;
}

.stage {
  min-height: calc(100vh - 140px);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.rail-block + .rail-block {
  margin-top: 12px;
}

.rail-block {
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, 0.08);
  border-radius: 16px;
  background:
    radial-gradient(circle at var(--spotlight-x, 50%) var(--spotlight-y, 50%), rgba(26, 115, 232, 0.12), transparent 42%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.26), rgba(255, 255, 255, 0.06)),
    var(--surface-soft);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(16px);
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.section-head h2 {
  margin: 0;
  font-size: 16px;
  line-height: 1.2;
}

.section-head p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.field {
  display: grid;
  gap: 8px;
  margin-bottom: 14px;
}

.upload-field {
  gap: 8px;
}

.upload-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: linear-gradient(180deg, var(--surface-strong), var(--surface-soft));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.upload-trigger {
  min-height: 38px;
  padding: 0 15px;
  border: 1px solid transparent;
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 10px 18px rgba(26, 115, 232, 0.16);
  transition: transform 180ms ease, box-shadow 180ms ease, opacity 180ms ease;
}

.upload-trigger:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 12px 20px rgba(26, 115, 232, 0.18);
}

.upload-copy {
  min-width: 0;
  display: grid;
  gap: 3px;
}

.upload-copy strong,
.upload-copy span {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.upload-copy strong {
  color: var(--text);
  font-size: 13px;
}

.upload-copy span {
  color: var(--muted);
  font-size: 12px;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.field span,
.summary-item span,
.file-card span,
.intent-card span,
.candidate-copy p,
.candidate-detail p,
.clip-note,
.placeholder,
.compare-head span,
.candidate-detail-meta span,
.candidate-title span,
.brand p {
  color: var(--muted);
}

.field textarea,
.field select,
.field input[type="number"],
.field input[type="file"] {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface-soft);
  color: var(--text);
  padding: 11px 12px;
}

.field textarea {
  min-height: 128px;
  resize: vertical;
}

.field input[type="range"] {
  width: 100%;
  accent-color: var(--accent);
}

.mode-switch,
.chip-group,
.tab-switch,
.button-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.chip-group.wrap {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.mode-switch {
  margin-bottom: 14px;
  padding: 4px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface-soft);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.mode-switch button,
.chip-btn,
.tab-btn,
.switch-btn {
  min-height: 38px;
  padding: 8px 12px;
  cursor: pointer;
}

.mode-switch button {
  flex: 1;
  border-color: transparent;
  background: transparent;
  color: var(--muted);
}

.mode-switch button.active,
.chip-btn.active,
.tab-btn.active {
  border-color: transparent;
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  color: #fff;
  box-shadow: 0 10px 22px rgba(26, 115, 232, 0.18);
}

.mode-switch button.active {
  background: linear-gradient(180deg, var(--surface-strong), var(--surface-soft));
  color: var(--text);
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
  border-color: rgba(148, 163, 184, 0.35);
}

.chip-btn {
  border: 1px solid var(--border);
  background: linear-gradient(180deg, var(--surface-strong), var(--surface-soft));
  color: var(--text);
  font-size: 13px;
  line-height: 1;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.chip-btn.active {
  box-shadow: 0 8px 18px rgba(26, 115, 232, 0.18);
}

.switch-btn,
.tab-btn {
  border-color: var(--border);
  background: var(--surface-soft);
  color: var(--muted);
}

.switch-btn {
  font-weight: 600;
}

.tab-btn.active {
  box-shadow: 0 8px 18px rgba(26, 115, 232, 0.18);
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 8px 0 10px;
  color: var(--text);
}

.progress-card {
  margin-top: 14px;
}

.progress-meta,
.clip-meter-top,
.candidate-title,
.candidate-detail-head,
.candidate-detail-meta,
.compare-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.progress-meta {
  margin-bottom: 8px;
}

.progress-track {
  height: 10px;
  border-radius: 999px;
  background: var(--accent-weak);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background:
    linear-gradient(90deg, var(--accent), #10b981),
    repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.25) 0 8px, transparent 8px 16px);
  background-size: 100% 100%, 24px 24px;
  transition: width 0.24s ease;
  transform-origin: left center;
}

.clip-fill {
  background:
    linear-gradient(90deg, #10b981, var(--accent)),
    repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.22) 0 8px, transparent 8px 16px);
}

[data-animate-metric] {
  opacity: 0;
}

[data-animate-metric].is-visible {
  opacity: 1;
}

.metric-bar {
  transform: scaleX(0.72);
  transform-origin: left center;
  will-change: transform, opacity;
}

.metric-bar.is-visible {
  animation:
    metricBarReveal 900ms cubic-bezier(0.16, 1, 0.3, 1) both,
    stripeShift 1.8s linear infinite;
}

.metric-ring {
  transform: scale(0.86) rotate(-8deg);
  transform-origin: center;
  will-change: transform, opacity;
}

.metric-ring.is-visible {
  animation: metricRingReveal 980ms cubic-bezier(0.16, 1, 0.3, 1) both;
}

.status.error {
  margin-top: 12px;
  color: #e11d48;
}

.summary-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.summary-item,
.file-card,
.gauge-card,
.candidate-detail,
.intent-card,
.compare-panel {
  border: 1px solid var(--border);
  border-radius: 14px;
  background:
    radial-gradient(circle at var(--spotlight-x, 50%) var(--spotlight-y, 50%), rgba(26, 115, 232, 0.12), transparent 42%),
    var(--surface-soft);
  backdrop-filter: blur(16px);
  position: relative;
  overflow: hidden;
  isolation: isolate;
}

.summary-item {
  min-height: 84px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.summary-item strong,
.file-card strong,
.intent-card strong,
.candidate-detail strong {
  display: block;
  margin-top: 4px;
  color: var(--text);
  font-weight: 600;
}

.summary-item strong {
  font-size: 18px;
}

.file-card {
  margin-top: 12px;
  padding: 16px;
}

.file-card p,
.intent-card p {
  margin: 0 0 10px;
}

.file-card p:last-child,
.intent-card p:last-child {
  margin-bottom: 0;
}

.clip-meter {
  margin-top: 12px;
}

.gauge-card {
  margin-top: 12px;
  padding: 18px;
  display: grid;
  gap: 14px;
  place-items: center;
  background:
    radial-gradient(circle at var(--spotlight-x, 50%) var(--spotlight-y, 50%), rgba(26, 115, 232, 0.12), transparent 42%),
    radial-gradient(circle at top, rgba(26, 115, 232, 0.08), transparent 52%),
    var(--surface-soft);
}

.gauge-ring {
  width: min(100%, 210px);
  aspect-ratio: 1;
  border-radius: 50%;
  padding: 12px;
  background:
    conic-gradient(
      from 220deg,
      #10b981 0%,
      #10b981 calc(var(--score) * 1%),
      rgba(191, 211, 239, 0.7) calc(var(--score) * 1%),
      rgba(191, 211, 239, 0.7) 100%
    );
  box-shadow: 0 18px 30px rgba(15, 23, 42, 0.08);
}

.gauge-core {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: grid;
  place-items: center;
  text-align: center;
  background:
    linear-gradient(180deg, var(--surface-strong), var(--surface-soft)),
    var(--surface-strong);
}

.gauge-core span {
  color: var(--muted);
  font-size: 12px;
}

.gauge-core strong {
  margin-top: 6px;
  color: var(--text);
  font-size: 40px;
  line-height: 1;
  letter-spacing: -0.05em;
}

.gauge-core p {
  margin: 8px 0 0;
  color: var(--accent);
  font-size: 12px;
  font-weight: 600;
}

.gauge-caption {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 0 4px;
  color: var(--muted);
  font-size: 12px;
}

.gauge-caption strong {
  color: var(--text);
}

.clip-note {
  margin: 10px 0 0;
  font-size: 12px;
}

.candidate-list {
  display: grid;
  gap: 12px;
  margin-top: 12px;
}

.candidate-row {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  gap: 12px;
  width: 100%;
  padding: 12px;
  text-align: left;
  border: 1px solid var(--border);
  border-radius: 14px;
  background:
    radial-gradient(circle at var(--spotlight-x, 50%) var(--spotlight-y, 50%), rgba(26, 115, 232, 0.12), transparent 42%),
    var(--surface-soft);
  backdrop-filter: blur(16px);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  isolation: isolate;
}

.candidate-row.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent-weak) inset;
}

.candidate-swatch {
  min-height: 64px;
  border-radius: 12px;
}

.candidate-copy {
  display: grid;
  gap: 6px;
}

.candidate-title strong,
.candidate-detail-head strong,
.compare-head strong {
  color: var(--text);
}

.candidate-copy p,
.candidate-detail p,
.intent-card p {
  margin: 0;
  line-height: 1.55;
  font-size: 12px;
}

.candidate-bar {
  height: 6px;
  border-radius: 999px;
  background: var(--accent-weak);
  overflow: hidden;
}

.candidate-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background:
    linear-gradient(90deg, var(--accent), #10b981),
    repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.25) 0 8px, transparent 8px 16px);
  background-size: 100% 100%, 24px 24px;
}

.candidate-detail {
  margin-top: 12px;
  padding: 16px;
}

.candidate-detail-head,
.candidate-detail-meta,
.compare-head {
  margin-bottom: 8px;
}

.candidate-detail-meta {
  margin-top: 10px;
}

.section-kicker,
.metric-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 10px;
}

.stage-head {
  margin-bottom: 0;
}

.stage-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.canvas-shell {
  flex: 1;
  border: 1px solid var(--border);
  border-radius: 16px;
  background:
    radial-gradient(circle at top, rgba(26, 115, 232, 0.05), transparent 54%),
    var(--surface-soft);
  padding: 14px;
}

.preview-frame,
.empty-state,
.compare-panel .preview-frame.small,
.compare-panel .empty-state.small {
  width: 100%;
  aspect-ratio: 16 / 10;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background:
    linear-gradient(180deg, var(--surface-strong), rgba(255, 255, 255, 0.8)),
    var(--surface-strong);
}

.preview-frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.empty-state {
  display: grid;
  place-items: center;
  text-align: center;
  padding: 22px;
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border-style: dashed;
}

.empty-state::before,
.empty-state::after {
  content: "";
  position: absolute;
  z-index: 0;
  inset: auto;
  pointer-events: none;
}

.empty-state::before {
  left: 50%;
  top: 44%;
  transform: translate(-50%, -50%);
  width: 180px;
  height: 180px;
  border-radius: 50%;
  border: 1px solid rgba(26, 115, 232, 0.12);
  background: radial-gradient(circle, rgba(26, 115, 232, 0.08), transparent 68%);
  animation: floatPulse 4.8s ease-in-out infinite;
}

.empty-state::after {
  left: 50%;
  top: 54%;
  transform: translate(-50%, -50%);
  width: 250px;
  height: 120px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(26, 115, 232, 0.08), rgba(16, 185, 129, 0.08));
  filter: blur(10px);
  animation: glowSlide 5.5s ease-in-out infinite;
}

.empty-bars,
.empty-illustration {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: end;
  justify-content: center;
  gap: 10px;
  height: 118px;
}

.empty-bars span {
  width: 28px;
  border-radius: 10px 10px 4px 4px;
  background: linear-gradient(180deg, var(--accent), #10b981);
  box-shadow: 0 10px 18px rgba(26, 115, 232, 0.12);
}

.empty-bars span:nth-child(1) {
  height: 56px;
}

.empty-bars span:nth-child(2) {
  height: 90px;
}

.empty-bars span:nth-child(3) {
  height: 72px;
}

.empty-bars span:nth-child(4) {
  height: 110px;
}

.empty-illustration span {
  width: 56px;
  height: 86px;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(26, 115, 232, 0.9), rgba(16, 185, 129, 0.82));
  box-shadow: 0 10px 20px rgba(26, 115, 232, 0.14);
}

.empty-illustration span:nth-child(2) {
  height: 112px;
}

.empty-illustration span:nth-child(3) {
  height: 68px;
}

.empty-state p {
  margin: 14px 0 0;
  color: var(--muted);
  font-size: 13px;
  position: relative;
  z-index: 1;
}

.compare-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.compare-panel {
  padding: 14px;
}

.compare-head {
  margin-bottom: 10px;
  font-size: 13px;
}

.compare-head span {
  font-size: 12px;
}

.canvas-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.metric-chip {
  padding: 8px 10px;
}

.rail-block p:last-child {
  margin-bottom: 0;
}

.intent-card {
  padding: 16px;
  margin-bottom: 12px;
}

.intent-card p {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.intent-card span {
  flex: 0 0 auto;
  font-size: 12px;
}

.intent-card strong {
  text-align: right;
}

.stage-list {
  display: grid;
  gap: 10px;
  margin-bottom: 12px;
}

.stage-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background:
    radial-gradient(circle at var(--spotlight-x, 50%) var(--spotlight-y, 50%), rgba(26, 115, 232, 0.12), transparent 42%),
    var(--surface-soft);
  backdrop-filter: blur(16px);
  font-size: 12px;
  position: relative;
  overflow: hidden;
  isolation: isolate;
}

.stage-completed {
  color: #16a34a;
}

.stage-running,
.stage-retrying {
  color: #d97706;
}

.stage-pending {
  color: var(--muted);
}

.stage-failed {
  color: #e11d48;
}

.log-list {
  max-height: 220px;
  overflow: auto;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: rgba(2, 6, 23, 0.94);
  color: #e2e8f0;
}

.log-list p {
  margin: 0 0 8px;
  font-size: 12px;
  line-height: 1.5;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

.download-link {
  display: inline-flex;
  margin-top: 12px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
}

pre {
  margin: 0;
  max-height: 240px;
  overflow: auto;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: rgba(2, 6, 23, 0.94);
  color: #e2e8f0;
  font-size: 12px;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

.placeholder {
  font-size: 13px;
  margin: 0;
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 260ms ease, transform 260ms ease;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(14px);
}

.page-fade-enter-to,
.page-fade-leave-from {
  opacity: 1;
  transform: translateY(0);
}

@media (max-width: 1320px) {
  .workspace {
    grid-template-columns: 1fr;
  }

  .rail,
  .stage {
    position: static;
  }

  .stage {
    min-height: auto;
  }

  .compact-workspace {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 840px) {
  .appbar {
    grid-template-columns: 1fr;
    justify-items: start;
  }

  .appbar-meta {
    justify-content: flex-start;
  }

  .appnav {
    width: 100%;
    justify-content: flex-start;
    overflow-x: auto;
  }

  .appbar-actions {
    width: 100%;
  }

  .appbar-actions .primary-btn,
  .appbar-actions .ghost-btn {
    flex: 1;
  }

  .summary-list,
  .compare-grid {
    grid-template-columns: 1fr;
  }

  .hero-panel,
  .entry-grid,
  .overview-strip,
  .page-toolbar,
  .report-grid,
  .docs-grid,
  .style-doc-grid {
    grid-template-columns: 1fr;
  }

  .page-toolbar {
    align-items: stretch;
  }

  .toolbar-actions {
    justify-content: flex-start;
  }

  .chip-group.wrap {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .page {
    padding: 14px 12px 26px;
  }

  .hero-panel,
  .entry-card,
  .overview-strip article,
  .page-toolbar,
  .report-card,
  .doc-card {
    border-radius: 14px;
  }

  .hero-panel {
    min-height: auto;
    padding: 22px;
  }

  .workspace {
    padding: 12px;
  }

  .compact-workspace {
    padding: 0;
  }

  .rail,
  .stage {
    padding: 12px;
    border-radius: 12px;
  }

  .button-row,
  .mode-switch,
  .chip-group,
  .tab-switch,
  .appbar-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .chip-group.wrap {
    grid-template-columns: 1fr;
  }

  .candidate-row {
    grid-template-columns: 1fr;
  }

  .preview-frame,
  .empty-state,
  .compare-panel .preview-frame.small,
  .compare-panel .empty-state.small {
    aspect-ratio: 4 / 3;
  }
}

.app-shell {
  position: relative;
  overflow: hidden;
}

.app-shell::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(26, 115, 232, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(26, 115, 232, 0.04) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.58), transparent 82%);
  opacity: 0.28;
  animation: gridDrift 36s linear infinite;
}

.app-shell::after {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 12% 20%, rgba(26, 115, 232, 0.16), transparent 18%),
    radial-gradient(circle at 84% 16%, rgba(16, 185, 129, 0.14), transparent 16%),
    radial-gradient(circle at 76% 82%, rgba(139, 92, 246, 0.12), transparent 18%),
    radial-gradient(circle at 52% 50%, rgba(255, 255, 255, 0.14), transparent 30%);
  background-size: 100% 100%;
  filter: blur(18px) saturate(1.08);
  opacity: 0.78;
  mix-blend-mode: screen;
  animation: meshDrift 28s ease-in-out infinite alternate;
}

.app-shell.theme-dark::after {
  opacity: 0.42;
  background:
    radial-gradient(circle at 12% 20%, rgba(110, 168, 254, 0.08), transparent 18%),
    radial-gradient(circle at 84% 16%, rgba(16, 185, 129, 0.06), transparent 16%),
    radial-gradient(circle at 76% 82%, rgba(139, 92, 246, 0.05), transparent 18%);
}

.app-shell.theme-dark::before {
  opacity: 0.18;
  background-image:
    linear-gradient(rgba(110, 168, 254, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(110, 168, 254, 0.08) 1px, transparent 1px);
}

.app-shell > * {
  position: relative;
  z-index: 1;
}

.app-shell.is-ready .appbar {
  animation: floatIn 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.app-shell.is-ready .workspace > .rail:first-child {
  animation: floatIn 0.55s cubic-bezier(0.22, 1, 0.36, 1) both 0.08s;
}

.app-shell.is-ready .workspace > .stage {
  animation: floatIn 0.55s cubic-bezier(0.22, 1, 0.36, 1) both 0.16s;
}

.app-shell.is-ready .workspace > .rail:last-child {
  animation: floatIn 0.55s cubic-bezier(0.22, 1, 0.36, 1) both 0.24s;
}

.rail,
.stage {
  transition: transform 220ms ease, box-shadow 220ms ease, border-color 220ms ease;
}

.rail:hover,
.stage:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.1);
}

.rail-block {
  transition: transform 180ms ease, opacity 180ms ease;
}

.app-shell.is-ready .rail-block {
  animation: riseIn 0.42s ease both;
}

.app-shell.is-ready .rail-block:nth-child(1) {
  animation-delay: 0.1s;
}

.app-shell.is-ready .rail-block:nth-child(2) {
  animation-delay: 0.18s;
}

.app-shell.is-ready .summary-item {
  animation: riseIn 0.42s ease both;
}

.app-shell.is-ready .summary-item:nth-child(1) {
  animation-delay: 0.08s;
}

.app-shell.is-ready .summary-item:nth-child(2) {
  animation-delay: 0.12s;
}

.app-shell.is-ready .summary-item:nth-child(3) {
  animation-delay: 0.16s;
}

.app-shell.is-ready .summary-item:nth-child(4) {
  animation-delay: 0.2s;
}

.app-shell.is-ready .summary-item:nth-child(5) {
  animation-delay: 0.24s;
}

.app-shell.is-ready .summary-item:nth-child(6) {
  animation-delay: 0.28s;
}

.summary-item:hover,
.candidate-row:hover,
.compare-panel:hover {
  transform: translateY(-2px);
  border-color: rgba(26, 115, 232, 0.26);
}

.primary-btn {
  background-size: 180% 180%;
  animation: gradientSweep 8s ease infinite;
}

.progress-fill {
  background-size: 100% 100%, 24px 24px;
  animation: stripeShift 1.6s linear infinite;
}

.candidate-row {
  transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease, background 180ms ease;
}

.app-shell.is-ready .candidate-row {
  animation: riseIn 0.42s ease both;
}

.app-shell.is-ready .candidate-row:nth-child(1) {
  animation-delay: 0.08s;
}

.app-shell.is-ready .candidate-row:nth-child(2) {
  animation-delay: 0.14s;
}

.app-shell.is-ready .candidate-row:nth-child(3) {
  animation-delay: 0.2s;
}

.candidate-swatch {
  transition: transform 220ms ease, filter 220ms ease;
}

.candidate-row:hover .candidate-swatch,
.candidate-row.active .candidate-swatch {
  transform: scale(1.03);
  filter: saturate(1.08);
}

.candidate-bar span {
  background-size: 100% 100%, 24px 24px;
  animation: stripeShift 1.8s linear infinite;
}

.candidate-detail,
.file-card,
.clip-meter,
.intent-card,
.compare-panel {
  transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
}

.canvas-shell {
  overflow: hidden;
}

.preview-switcher {
  width: 100%;
}

.reveal-frame {
  animation: revealScale 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}

.panel-swap-enter-active,
.panel-swap-leave-active {
  transition: opacity 240ms ease, transform 240ms ease;
}

.panel-swap-enter-from,
.panel-swap-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.985);
}

.panel-swap-enter-to,
.panel-swap-leave-from {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.preview-frame,
.empty-state,
.compare-panel .preview-frame.small,
.compare-panel .empty-state.small {
  transition: transform 220ms ease, box-shadow 220ms ease, border-color 220ms ease;
}

.preview-frame:hover,
.compare-panel:hover .preview-frame,
.compare-panel:hover .empty-state {
  transform: translateY(-2px);
  box-shadow: 0 16px 34px rgba(15, 23, 42, 0.08);
}

.empty-bars span {
  transform-origin: bottom;
  animation: barPulse 1.55s ease-in-out infinite;
}

.empty-bars span:nth-child(2) {
  animation-delay: 0.1s;
}

.empty-bars span:nth-child(3) {
  animation-delay: 0.2s;
}

.empty-bars span:nth-child(4) {
  animation-delay: 0.3s;
}

.empty-illustration span {
  animation: floatUp 2.8s ease-in-out infinite;
}

.empty-illustration span:nth-child(2) {
  animation-delay: 0.15s;
}

.empty-illustration span:nth-child(3) {
  animation-delay: 0.3s;
}

.metric-chip {
  animation: chipGlow 4s ease-in-out infinite;
}

.log-list {
  animation: fadeIn 0.45s ease both;
}

.download-link {
  transition: transform 180ms ease, opacity 180ms ease;
}

.download-link:hover {
  transform: translateY(-1px);
}

.app-shell.is-ready .stage-item {
  animation: riseIn 0.4s ease both;
}

.app-shell.is-ready .stage-item:nth-child(1) {
  animation-delay: 0.06s;
}

.app-shell.is-ready .stage-item:nth-child(2) {
  animation-delay: 0.1s;
}

.app-shell.is-ready .stage-item:nth-child(3) {
  animation-delay: 0.14s;
}

.app-shell.is-ready .stage-item:nth-child(4) {
  animation-delay: 0.18s;
}

.app-shell.is-ready .stage-item:nth-child(5) {
  animation-delay: 0.22s;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

@keyframes floatIn {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes riseIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes gridDrift {
  from {
    transform: translate3d(0, 0, 0);
  }
  to {
    transform: translate3d(36px, 36px, 0);
  }
}

@keyframes stripeShift {
  from {
    background-position: 0 0, 0 0;
  }
  to {
    background-position: 0 0, 24px 0;
  }
}

@keyframes barPulse {
  0%,
  100% {
    transform: scaleY(0.92);
  }
  50% {
    transform: scaleY(1.04);
  }
}

@keyframes floatUp {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

@keyframes chipGlow {
  0%,
  100% {
    box-shadow: 0 0 0 rgba(26, 115, 232, 0);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(26, 115, 232, 0.04);
  }
}

@keyframes gradientSweep {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

@keyframes revealScale {
  from {
    opacity: 0;
    transform: scale(0.985);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes floatPulse {
  0%,
  100% {
    transform: translate(-50%, -50%) scale(0.96);
    opacity: 0.56;
  }
  50% {
    transform: translate(-50%, -50%) scale(1.04);
    opacity: 0.92;
  }
}

@keyframes glowSlide {
  0%,
  100% {
    transform: translate(-50%, -50%) translateX(-12px) scale(0.98);
    opacity: 0.42;
  }
  50% {
    transform: translate(-50%, -50%) translateX(12px) scale(1.02);
    opacity: 0.72;
  }
}

@keyframes metricBarReveal {
  0% {
    transform: scaleX(0.22);
    opacity: 0;
  }
  65% {
    transform: scaleX(1.03);
    opacity: 1;
  }
  100% {
    transform: scaleX(1);
    opacity: 1;
  }
}

@keyframes metricRingReveal {
  0% {
    transform: scale(0.82) rotate(-10deg);
    opacity: 0;
  }
  62% {
    transform: scale(1.03) rotate(2deg);
    opacity: 1;
  }
  100% {
    transform: scale(1) rotate(0deg);
    opacity: 1;
  }
}

@keyframes heroWordReveal {
  0% {
    transform: translate3d(0, 28px, 0);
    opacity: 0;
    filter: blur(10px);
  }
  50% {
    transform: translate3d(0, -5px, 0);
    opacity: 0.56;
    filter: blur(5px);
  }
  100% {
    transform: translate3d(0, 0, 0);
    opacity: 1;
    filter: blur(0px);
  }
}

@keyframes meshDrift {
  0% {
    transform: translate3d(-1.5%, -0.5%, 0) scale(1);
  }
  50% {
    transform: translate3d(1.5%, 1.2%, 0) scale(1.04);
  }
  100% {
    transform: translate3d(-0.5%, 2%, 0) scale(1.02);
  }
}
</style>
