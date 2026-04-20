<script setup>
import { computed, ref } from "vue";

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

const progressTemplate = [
  { stage: "parse_ppt", label: "解析内容" },
  { stage: "semantic_analysis", label: "语义分析" },
  { stage: "generate_chart", label: "生成图表" },
  { stage: "generate_illustration", label: "生成配图" },
  { stage: "save_pptx", label: "输出结果" },
];

let progressTimer = null;

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

const pipelineResult = computed(() => response.value?.pipeline ?? null);
const chartPreviewUrl = computed(() => pipelineResult.value?.chart_image_url ?? "");
const illustrationPreviewUrl = computed(() => pipelineResult.value?.illustration_image_url ?? "");
const downloadUrl = computed(() => pipelineResult.value?.final_pptx_url ?? "");
const recentLogs = computed(() => pipelineResult.value?.logs ?? []);
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

        <template v-if="activeMode === 'ppt'">
        <label class="field">
          <span>PPT 文件</span>
          <input type="file" accept=".pptx" @change="handleFileChange" />
        </label>

        <label class="field">
          <span>处理页码</span>
          <input v-model.number="slideNumber" type="number" min="1" />
        </label>

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
            <span>处理进度</span>
            <strong>{{ progressValue }}%</strong>
          </div>
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: `${progressValue}%` }"></div>
          </div>
        </div>

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
        <h2>前两周交付</h2>
        <ul>
          <li>上传 PPT、页码选择与基础信息展示</li>
          <li>实时进度条与阶段状态卡片</li>
          <li>图表预览区与配图区</li>
          <li>文本到图表 PNG 的本地演示链路</li>
        </ul>
        <a v-if="downloadUrl" :href="downloadUrl" class="download-link">下载增强版 PPT</a>
      </div>
    </section>
  </main>
</template>
