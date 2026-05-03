<script setup>
import { computed, onMounted, ref } from "vue";

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
const progressTimer = ref(null);
const pageReady = ref(false);
const fileInput = ref(null);

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

const progressTemplate = [
  { stage: "parse_ppt", label: "解析内容" },
  { stage: "semantic_analysis", label: "语义分析" },
  { stage: "generate_chart", label: "生成图表" },
  { stage: "generate_illustration", label: "生成配图" },
  { stage: "save_pptx", label: "输出结果" },
];

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

onMounted(() => {
  window.requestAnimationFrame(() => {
    pageReady.value = true;
  });
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

async function regenerateIllustration() {
  selectedCandidateIndex.value = 0;
  if (activeMode.value === "ppt") {
    await submitForm();
    return;
  }
  await runDemo();
}

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
</script>

<template>
  <main :class="['app-shell', themeClass, { 'is-ready': pageReady }]">
    <header class="appbar">
      <div class="brand">
        <div class="brand-mark">SC</div>
        <div>
          <h1>SmartChart Studio</h1>
          <p>Multi-modal illustration workspace</p>
        </div>
      </div>

      <div class="appbar-meta">
        <span class="meta-pill">{{ workflowStatus }}</span>
        <span class="meta-pill">{{ modelLabel }}</span>
        <span class="meta-pill">{{ styleLabel }}</span>
        <span class="meta-pill">{{ semanticModeLabel }}</span>
      </div>

      <div class="appbar-actions">
        <button type="button" class="ghost-btn" @click="toggleTheme">
          {{ themeMode === "dark" ? "浅色" : "深色" }}
        </button>
        <button
          type="button"
          class="primary-btn"
          :disabled="loading || demoLoading"
          @click="activeMode === 'ppt' ? submitForm() : runDemo()"
        >
          {{ primaryActionLabel }}
        </button>
      </div>
    </header>

    <section class="workspace">
      <aside class="rail">
        <div class="rail-block">
          <div class="section-head">
            <div>
              <h2>输入</h2>
              <p>切换来源、模型和生成方式。</p>
            </div>
            <span class="section-kicker">{{ activeMode === "ppt" ? "PPT" : "TEXT" }}</span>
          </div>

          <div class="mode-switch">
            <button type="button" :class="{ active: activeMode === 'ppt' }" @click="activeMode = 'ppt'">
              PPT 模式
            </button>
            <button type="button" :class="{ active: activeMode === 'demo' }" @click="activeMode = 'demo'">
              文本演示
            </button>
          </div>

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
              <div class="progress-fill" :style="{ width: `${progressValue}%` }"></div>
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
        </div>

        <div class="canvas-footer">
          <span class="metric-chip">CLIP {{ clipScoreText }}</span>
          <span class="metric-chip">{{ clipStatus }}</span>
          <span class="metric-chip">轮次 {{ generationRound }}</span>
          <span class="metric-chip">页码 {{ slideNumber }}</span>
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
  </main>
</template>

<style scoped>
.app-shell {
  --bg: #f6f8fb;
  --surface: rgba(255, 255, 255, 0.88);
  --surface-strong: #ffffff;
  --surface-soft: rgba(255, 255, 255, 0.7);
  --text: #0f172a;
  --muted: #64748b;
  --border: rgba(15, 23, 42, 0.08);
  --accent: #1a73e8;
  --accent-strong: #0f5de7;
  --accent-weak: rgba(26, 115, 232, 0.12);
  --shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
  min-height: 100vh;
  color: var(--text);
  background: linear-gradient(180deg, #f8fafc 0%, #eef3f8 100%);
}

.app-shell.theme-dark {
  --bg: #0b1220;
  --surface: rgba(15, 23, 42, 0.84);
  --surface-strong: #111827;
  --surface-soft: rgba(15, 23, 42, 0.64);
  --text: #e5eefb;
  --muted: #9aa7b7;
  --border: rgba(148, 163, 184, 0.16);
  --accent: #6ea8fe;
  --accent-strong: #4d8df7;
  --accent-weak: rgba(110, 168, 254, 0.14);
  --shadow: 0 18px 44px rgba(2, 6, 23, 0.42);
  background: linear-gradient(180deg, #0b1220 0%, #111827 100%);
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
  backdrop-filter: blur(20px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
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

.workspace {
  max-width: 1600px;
  margin: 0 auto;
  padding: 16px 20px 28px;
  display: grid;
  grid-template-columns: minmax(300px, 340px) minmax(0, 1fr) minmax(300px, 360px);
  gap: 16px;
  align-items: start;
}

.rail,
.stage {
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--surface);
  box-shadow: var(--shadow);
  backdrop-filter: blur(20px);
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
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
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
  gap: 8px;
  flex-wrap: wrap;
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
}

.clip-fill {
  background:
    linear-gradient(90deg, #10b981, var(--accent)),
    repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.22) 0 8px, transparent 8px 16px);
}

.status.error {
  margin-top: 12px;
  color: #e11d48;
}

.summary-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.summary-item,
.file-card,
.clip-meter,
.candidate-detail,
.intent-card,
.compare-panel {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface-soft);
}

.summary-item {
  padding: 10px 12px;
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

.file-card {
  margin-top: 12px;
  padding: 12px;
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
  padding: 12px;
}

.clip-meter strong {
  font-size: 18px;
}

.clip-note {
  margin: 10px 0 0;
  font-size: 12px;
}

.candidate-list {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.candidate-row {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  gap: 12px;
  width: 100%;
  padding: 10px;
  text-align: left;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface-soft);
  cursor: pointer;
}

.candidate-row.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent-weak) inset;
}

.candidate-swatch {
  min-height: 64px;
  border-radius: 10px;
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
  padding: 12px;
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
  border-radius: 12px;
  background: var(--surface-soft);
  padding: 14px;
}

.preview-frame,
.empty-state,
.compare-panel .preview-frame.small,
.compare-panel .empty-state.small {
  width: 100%;
  aspect-ratio: 16 / 10;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: var(--surface-strong);
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
  padding: 20px;
}

.empty-bars,
.empty-illustration {
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
}

.compare-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.compare-panel {
  padding: 12px;
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
  padding: 12px;
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
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface-soft);
  font-size: 12px;
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
}

@media (max-width: 840px) {
  .appbar {
    grid-template-columns: 1fr;
    justify-items: start;
  }

  .appbar-meta {
    justify-content: flex-start;
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
}

@media (max-width: 640px) {
  .workspace {
    padding: 12px;
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
  pointer-events: none;
  background-image:
    linear-gradient(rgba(26, 115, 232, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(26, 115, 232, 0.05) 1px, transparent 1px);
  background-size: 36px 36px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.55), transparent 82%);
  opacity: 0.35;
  animation: gridDrift 32s linear infinite;
}

.app-shell.theme-dark::before {
  opacity: 0.2;
  background-image:
    linear-gradient(rgba(110, 168, 254, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(110, 168, 254, 0.08) 1px, transparent 1px);
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
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
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
</style>
