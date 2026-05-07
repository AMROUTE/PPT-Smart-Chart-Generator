<script setup>
import { computed, ref, watch } from "vue";

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
const semanticMode = ref("local");
const chartTypeOverride = ref("auto");
const illustrationStyle = ref("auto");
const imageModel = ref("local");
const slidePreviewUrl = ref("");
const slidePreviewLoading = ref(false);
const slidePreviewError = ref("");
const slideCount = ref(0);
const uploadToken = ref("");

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
    finalizeProgress(payload.pipeline);
  } catch (error) {
    errorMessage.value = error.message;
    stopProgress(true);
  } finally {
    demoLoading.value = false;
  }
}

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
</script>

<template>
  <main class="page-shell">
    <section class="hero-card">
      <p class="eyebrow">Week 2 Delivery</p>
      <h1>SmartChart语义识别PPT图表生成</h1>
      <p class="hero-copy">
        当前版本功能：上传 PPT、查看实时进度、预览图表与配图，并回显后端日志。
      </p>
    </section>

    <section class="workspace-grid">
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
      </div>

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
  </main>
</template>
