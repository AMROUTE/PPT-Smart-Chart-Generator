<script setup>
import { computed, ref, watch } from "vue";

import PipelineStatus from "../components/PipelineStatus.vue";
import PreviewPanel from "../components/PreviewPanel.vue";
import SlideOutlinePanel from "../components/SlideOutlinePanel.vue";
import UploadDropzone from "../components/UploadDropzone.vue";
import { useUserSettings } from "../composables/useUserSettings";
import { requestDemo, requestProcess, requestSlideOutline, requestSlidePreview } from "../services/api";

const { settings } = useUserSettings();

const file = ref(null);
const slideNumber = ref(1);
const loading = ref(false);
const errorMessage = ref("");
const response = ref(null);
const activeMode = ref("ppt");
const demoText = ref("营收: 120\n成本: 80\n利润: 40");
const demoLoading = ref(false);
const progressValue = ref(0);
const stageCards = ref([]);
const semanticMode = ref(settings.defaultSemanticMode);
const chartTypeOverride = ref("auto");
const illustrationStyle = ref(settings.defaultIllustrationStyle);
const imageModel = ref(settings.defaultImageModel);
const slidePreviewUrl = ref("");
const slidePreviewLoading = ref(false);
const slidePreviewError = ref("");
const slideCount = ref(0);
const uploadToken = ref("");
const slideOutline = ref([]);
const widgetOrder = ref(["chart", "illustration", "pipeline", "outline"]);
const draggedWidget = ref("");

const progressTemplate = [
  { stage: "parse_ppt", label: "解析内容" },
  { stage: "semantic_analysis", label: "语义分析" },
  { stage: "generate_chart", label: "生成图表" },
  { stage: "generate_illustration", label: "生成配图" },
  { stage: "save_pptx", label: "输出结果" },
];

let progressTimer = null;
let previewRequestId = 0;

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
const chartOverrideText = computed(() => (chartTypeOverride.value === "auto" ? "自动推荐" : chartTypeOverride.value));
const canPreview = computed(() => Boolean(file.value || uploadToken.value));

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
  formData.append("illustration_style", illustrationStyle.value);
  formData.append("image_model", imageModel.value);
  appendPersonalSettings(formData);

  try {
    const payload = await requestProcess(formData);
    response.value = payload;
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
  appendPersonalSettings(formData);

  try {
    const payload = await requestDemo(formData);
    response.value = payload;
    finalizeProgress(payload.pipeline);
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
  slideOutline.value = [];
  slideCount.value = 0;
  slideNumber.value = 1;
  response.value = null;
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
  } catch (error) {
    slidePreviewError.value = error.message;
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
  }
}

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

function selectOutlineSlide(targetSlide) {
  slideNumber.value = targetSlide;
}

function onWidgetDragStart(widgetKey) {
  draggedWidget.value = widgetKey;
}

function onWidgetDrop(targetKey) {
  if (!draggedWidget.value || draggedWidget.value === targetKey) {
    return;
  }
  const current = [...widgetOrder.value];
  const fromIndex = current.indexOf(draggedWidget.value);
  const toIndex = current.indexOf(targetKey);
  current.splice(fromIndex, 1);
  current.splice(toIndex, 0, draggedWidget.value);
  widgetOrder.value = current;
  draggedWidget.value = "";
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
  <main class="page-shell inner-page">
    <section class="hero-card">
      <p class="eyebrow">Workspace</p>
      <h1>总工作台</h1>
      <p class="hero-copy">
        这里集中完成上传、PPT 逐页解析、图表生成和配图预览。个人设置里的 API key 和模型会自动带到当前请求里。
      </p>
    </section>

    <section class="workspace-grid workspace-grid-wide">
      <div class="panel">
        <h2>上传与处理</h2>
        <div class="mode-switch">
          <button :class="{ active: activeMode === 'ppt' }" @click="activeMode = 'ppt'">PPT 模式</button>
          <button :class="{ active: activeMode === 'demo' }" @click="activeMode = 'demo'">文本演示</button>
        </div>

        <label class="field">
          <span>语义分析模式</span>
          <select v-model="semanticMode">
            <option value="local">本地规则</option>
            <option value="qwen">千问 API</option>
          </select>
        </label>

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
          <UploadDropzone :file="file" @select="handleSelectedFile" />

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
          <label class="field">
            <span>业务文本</span>
            <textarea v-model="demoText" rows="6" placeholder="例如：营收: 120"></textarea>
          </label>

          <button class="primary-btn" :disabled="demoLoading" @click="runDemo">
            {{ demoLoading ? "生成中..." : "文本直出图表 PNG" }}
          </button>
        </template>

        <div class="progress-card">
          <div class="progress-meta">
            <span>处理进度 · {{ semanticModeLabel }}</span>
            <strong>{{ progressValue }}%</strong>
          </div>
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: `${progressValue}%` }"></div>
          </div>
        </div>

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
        </div>
        <p v-else class="placeholder">上传文件后，这里会显示本地识别到的基础信息。</p>
      </div>
    </section>

    <section class="drag-tip">
      <span class="micro-badge">拖拽提示</span>
      <p>下面四个模块支持拖拽排序，便于你按自己的使用习惯重新排列。</p>
    </section>

    <section class="sortable-grid">
      <article
        v-for="widget in widgetOrder"
        :key="widget"
        class="sortable-item"
        draggable="true"
        @dragstart="onWidgetDragStart(widget)"
        @dragover.prevent
        @drop="onWidgetDrop(widget)"
      >
        <PreviewPanel
          v-if="widget === 'chart'"
          title="图表预览区"
          :image-url="chartPreviewUrl"
          placeholder="处理完成后，这里会展示图表 PNG。"
        />
        <PreviewPanel
          v-else-if="widget === 'illustration'"
          title="配图预览区"
          :image-url="illustrationPreviewUrl"
          placeholder="处理完成后，这里会展示配图预览。"
        />
        <PipelineStatus
          v-else-if="widget === 'pipeline'"
          :intent-info="intentInfo"
          :illustration-meta="illustrationMeta"
          :stage-cards="stageCards"
          :recent-logs="recentLogs"
          :semantic-mode-text="semanticModeText"
          :chart-override-text="chartOverrideText"
          :clip-score-text="clipScoreText"
        />
        <SlideOutlinePanel
          v-else-if="widget === 'outline'"
          :slides="slideOutline"
          :active-slide="slideNumber"
          @select-slide="selectOutlineSlide"
        />
      </article>
    </section>

    <section class="result-grid secondary-grid">
      <div class="panel milestone-panel">
        <h2>工作台能力</h2>
        <ul>
          <li>上传 PPT、逐页预览与逐页解析</li>
          <li>图表生成与配图预览</li>
          <li>手动修正图表类型</li>
          <li>个人 API key 与模型透传到本次调用</li>
          <li>增强版 PPT 下载输出</li>
        </ul>
        <a v-if="downloadUrl" :href="downloadUrl" class="download-link">下载增强版 PPT</a>
      </div>

      <div class="panel">
        <h2>当前调用配置</h2>
        <p><strong>Qwen 模型：</strong>{{ settings.customQwenModel || "qwen-plus" }}</p>
        <p><strong>默认语义模式：</strong>{{ settings.defaultSemanticMode }}</p>
        <p><strong>默认配图模型：</strong>{{ settings.defaultImageModel }}</p>
        <p><strong>默认配图风格：</strong>{{ settings.defaultIllustrationStyle }}</p>
      </div>
    </section>
  </main>
</template>
