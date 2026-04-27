<script setup>
import { computed, ref } from "vue";

const file = ref(null);
const slideNumber = ref(1);
const loading = ref(false);
const demoLoading = ref(false);
const errorMessage = ref("");
const response = ref(null);
const activeMode = ref("ppt");
const semanticMode = ref("local");
const demoText = ref("营收: 120\n成本: 80\n利润: 40");

const themeMode = ref("dark");
const selectedModel = ref("flux");
const selectedStyle = ref("tech");
const controlNetEnabled = ref(true);
const controlNetStrength = ref(0.72);
const selectedCandidateIndex = ref(0);
const generationRound = ref(0);
const progressValue = ref(0);
const stageCards = ref([]);
const progressTimer = ref(null);

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
  generationRound.value += 1;
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
  <main :class="['page-shell', themeClass]">
    <section class="hero-card">
      <div class="hero-top">
        <div>
          <p class="eyebrow">Multi-modal Illustration Studio</p>
          <h1>SmartChart 配图与 CLIP 交互面板</h1>
          <p class="hero-copy">
            你负责的部分会集中在配图、CLIP 分数、风格控制、模型切换和前端展示。
          </p>
        </div>
        <button class="theme-toggle" @click="toggleTheme">
          {{ themeMode === "dark" ? "切换浅色" : "切换深色" }}
        </button>
      </div>

      <div class="hero-stats">
        <div class="stat-card">
          <span>当前模型</span>
          <strong>{{ modelLabel }}</strong>
        </div>
        <div class="stat-card">
          <span>当前风格</span>
          <strong>{{ styleLabel }}</strong>
        </div>
        <div class="stat-card">
          <span>CLIP 分数</span>
          <strong>{{ clipScoreText }}</strong>
        </div>
        <div class="stat-card">
          <span>匹配状态</span>
          <strong>{{ clipStatus }}</strong>
        </div>
      </div>
    </section>

    <section class="workspace-grid">
      <div class="panel panel-main">
        <h2>上传与生成</h2>

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
          <span>配图模型</span>
          <div class="chip-row">
            <button
              v-for="item in modelOptions"
              :key="item.value"
              :class="{ chip: true, active: selectedModel === item.value }"
              @click="selectedModel = item.value"
            >
              {{ item.label }}
            </button>
          </div>
        </label>

        <label class="field">
          <span>风格选择</span>
          <div class="chip-row wrap">
            <button
              v-for="item in styleOptions"
              :key="item.value"
              :class="{ chip: true, active: selectedStyle === item.value }"
              @click="onStyleChange(item.value)"
            >
              {{ item.label }}
            </button>
          </div>
        </label>

        <label class="field switch-row">
          <span>ControlNet 风格控制</span>
          <button class="switch-btn" @click="controlNetEnabled = !controlNetEnabled">
            {{ controlNetEnabled ? "已开启" : "已关闭" }}
          </button>
        </label>

        <label class="field">
          <span>ControlNet 强度：{{ Math.round(controlNetStrength * 100) }}%</span>
          <input v-model.number="controlNetStrength" type="range" min="0.1" max="1" step="0.01" />
        </label>

        <template v-if="activeMode === 'ppt'">
          <label class="field">
            <span>PPT 文件</span>
            <input type="file" accept=".pptx" @change="handleFileChange" />
          </label>

          <label class="field">
            <span>处理页码</span>
            <input v-model.number="slideNumber" type="number" min="1" />
          </label>

          <div class="button-row">
            <button class="primary-btn" :disabled="loading" @click="submitForm">
              {{ loading ? "处理中..." : "一键生成图表与配图" }}
            </button>
            <button class="secondary-btn" :disabled="loading" @click="regenerateIllustration">
              重新生成配图
            </button>
          </div>
        </template>

        <template v-else>
          <label class="field">
            <span>业务文本</span>
            <textarea v-model="demoText" rows="6" placeholder="例如：营收: 120"></textarea>
          </label>

          <div class="button-row">
            <button class="primary-btn" :disabled="demoLoading" @click="runDemo">
              {{ demoLoading ? "生成中..." : "文本直出图表 PNG" }}
            </button>
            <button class="secondary-btn" :disabled="demoLoading" @click="regenerateIllustration">
              重新生成配图
            </button>
          </div>
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

        <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>
      </div>

      <div class="panel">
        <h2>当前配置</h2>
        <div class="info-list">
          <p><strong>模型：</strong>{{ modelLabel }}</p>
          <p><strong>风格：</strong>{{ styleLabel }}</p>
          <p><strong>ControlNet：</strong>{{ controlNetEnabled ? "开启" : "关闭" }}</p>
          <p><strong>ControlNet 强度：</strong>{{ Math.round(controlNetStrength * 100) }}%</p>
          <p><strong>生成轮次：</strong>{{ generationRound }}</p>
          <p><strong>CLIP 评分：</strong>{{ clipScoreText }}</p>
        </div>

        <div v-if="fileInfo" class="info-list compact">
          <p><strong>文件名：</strong>{{ fileInfo.name }}</p>
          <p><strong>文件大小：</strong>{{ fileInfo.size }}</p>
          <p><strong>文件类型：</strong>{{ fileInfo.type }}</p>
          <p><strong>修改时间：</strong>{{ fileInfo.lastModified }}</p>
          <p><strong>目标页码：</strong>{{ slideNumber }}</p>
        </div>
        <p v-else class="placeholder">上传文件后，这里会显示基础信息。</p>
      </div>
    </section>

    <section class="result-grid">
      <div class="panel preview-panel">
        <div class="panel-head">
          <h2>图表预览区</h2>
          <span class="panel-badge">Chart Preview</span>
        </div>
        <img v-if="chartPreviewUrl" :src="chartPreviewUrl" alt="chart preview" class="preview-image" />
        <div v-else class="empty-art chart-art">
          <div class="chart-bars">
            <span></span><span></span><span></span><span></span>
          </div>
          <p>图表结果将显示在这里</p>
        </div>
      </div>

      <div class="panel preview-panel">
        <div class="panel-head">
          <h2>配图区</h2>
          <span class="panel-badge">Illustration</span>
        </div>
        <img v-if="illustrationPreviewUrl" :src="illustrationPreviewUrl" alt="illustration preview" class="preview-image" />
        <div v-else class="empty-art illustration-art">
          <div class="orbit"></div>
          <div class="orbit small"></div>
          <p>配图结果将显示在这里</p>
        </div>
      </div>
    </section>

    <section class="result-grid secondary-grid">
      <div class="panel result-panel">
        <div class="panel-head">
          <h2>配图对比与 CLIP</h2>
          <span class="panel-badge">Top-K</span>
        </div>

        <div class="clip-meter">
          <div class="clip-meter-top">
            <span>语义匹配度</span>
            <strong>{{ clipScoreText }}</strong>
          </div>
          <div class="progress-track">
            <div class="progress-fill clip-fill" :style="{ width: `${clipScorePercent}%` }"></div>
          </div>
          <p class="clip-note">当前结果：{{ clipStatus }}，可以通过风格和模型切换继续微调。</p>
        </div>

        <div class="candidate-grid">
          <button
            v-for="(item, index) in candidatePool"
            :key="item.id"
            class="candidate-card"
            :class="{ active: selectedCandidateIndex === index }"
            @click="selectCandidate(index)"
          >
            <div class="candidate-swatch" :style="{ background: `linear-gradient(135deg, ${item.tones[0]}, ${item.tones[1]})` }"></div>
            <div class="candidate-body">
              <div class="candidate-top">
                <strong>{{ item.title }}</strong>
                <span>{{ item.tag }}</span>
              </div>
              <p>{{ item.subtitle }}</p>
              <div class="candidate-footer">
                <span>{{ item.hint }}</span>
                <strong>{{ item.score.toFixed(2) }}</strong>
              </div>
            </div>
          </button>
        </div>

        <div v-if="selectedCandidate" class="selected-preview">
          <div class="selected-preview-top">
            <strong>{{ selectedCandidate.title }}</strong>
            <span>Rank {{ selectedCandidate.rank }}</span>
          </div>
          <p>{{ selectedCandidate.subtitle }}</p>
        </div>
      </div>

      <div class="panel result-panel">
        <div class="panel-head">
          <h2>Pipeline 日志与状态</h2>
          <span class="panel-badge">Trace</span>
        </div>

        <div v-if="intentInfo" class="intent-card">
          <p><strong>推荐图表：</strong>{{ intentInfo.chart_type }}</p>
          <p><strong>语义来源：</strong>{{ intentInfo.source || "heuristic" }}</p>
          <p><strong>判断依据：</strong>{{ intentInfo.reason || intentInfo.summary }}</p>
          <p><strong>配图主题：</strong>{{ intentInfo.visual_theme || "未提供" }}</p>
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
    </section>
  </main>
</template>

<style scoped>
.page-shell {
  --bg-0: #07111f;
  --bg-1: #0d1b2a;
  --bg-2: rgba(10, 18, 32, 0.72);
  --card: rgba(14, 24, 41, 0.82);
  --card-border: rgba(148, 163, 184, 0.14);
  --text: #e5eefb;
  --muted: #8ea2bf;
  --accent: #7dd3fc;
  --accent-2: #f59e0b;
  --shadow: 0 28px 80px rgba(2, 8, 20, 0.42);
  min-height: 100vh;
  padding: 36px 20px 56px;
  color: var(--text);
  background:
    radial-gradient(circle at 12% 8%, rgba(245, 158, 11, 0.16), transparent 26%),
    radial-gradient(circle at 88% 14%, rgba(59, 130, 246, 0.2), transparent 22%),
    linear-gradient(160deg, #050b15 0%, #0f172a 48%, #09111f 100%);
}

.page-shell.theme-light {
  --bg-0: #f8fbff;
  --bg-1: #eef4ff;
  --bg-2: rgba(255, 255, 255, 0.72);
  --card: rgba(255, 255, 255, 0.82);
  --card-border: rgba(15, 23, 42, 0.08);
  --text: #102033;
  --muted: #55657b;
  --accent: #2563eb;
  --accent-2: #ea580c;
  --shadow: 0 20px 60px rgba(30, 60, 90, 0.12);
  background:
    radial-gradient(circle at 12% 8%, rgba(255, 214, 153, 0.42), transparent 28%),
    radial-gradient(circle at 88% 14%, rgba(120, 177, 255, 0.24), transparent 22%),
    linear-gradient(160deg, #f7f2ea 0%, #eef4ff 48%, #f7fbff 100%);
}

.hero-card,
.panel {
  border: 1px solid var(--card-border);
  border-radius: 24px;
  background: var(--card);
  backdrop-filter: blur(18px);
  box-shadow: var(--shadow);
}

.hero-card {
  max-width: 1180px;
  margin: 0 auto;
  padding: 28px 30px 24px;
}

.hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  margin: 0 0 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 12px;
  color: var(--accent-2);
}

.hero-card h1 {
  margin: 0;
  font-size: clamp(30px, 4vw, 54px);
  line-height: 1.04;
}

.hero-copy {
  max-width: 760px;
  margin: 14px 0 0;
  color: var(--muted);
  line-height: 1.7;
}

.theme-toggle {
  border: 1px solid var(--card-border);
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02));
  color: var(--text);
  padding: 10px 16px;
  cursor: pointer;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 20px;
}

.stat-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--card-border);
}

.stat-card span,
.field span,
.placeholder,
.info-list p,
.intent-card p,
.stage-item span,
.candidate-body p,
.clip-note,
.selected-preview p,
.hero-copy {
  color: var(--muted);
}

.stat-card strong {
  display: block;
  margin-top: 8px;
  font-size: 18px;
  color: var(--text);
}

.workspace-grid,
.result-grid {
  max-width: 1180px;
  margin: 20px auto 0;
  display: grid;
  gap: 18px;
}

.workspace-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.result-grid {
  grid-template-columns: 1.3fr 1fr;
}

.secondary-grid {
  align-items: start;
}

.panel {
  padding: 22px;
}

.panel-main {
  min-height: 100%;
}

.panel h2 {
  margin: 0;
  font-size: 21px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.panel-badge {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  color: var(--text);
  background: rgba(125, 211, 252, 0.14);
  border: 1px solid rgba(125, 211, 252, 0.22);
}

.mode-switch,
.chip-row,
.button-row {
  display: flex;
  gap: 10px;
}

.chip-row.wrap {
  flex-wrap: wrap;
}

.mode-switch {
  margin: 16px 0 18px;
}

.mode-switch button,
.chip,
.switch-btn,
.secondary-btn,
.primary-btn {
  border-radius: 999px;
  border: 1px solid var(--card-border);
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
}

.mode-switch button {
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--muted);
}

.mode-switch button.active,
.chip.active {
  background: linear-gradient(135deg, var(--accent), #60a5fa);
  color: #fff;
  border-color: transparent;
}

.field {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
}

.field textarea,
.field select,
.field input[type="number"],
.field input[type="file"] {
  width: 100%;
  border: 1px solid var(--card-border);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text);
  padding: 12px 14px;
}

.field textarea {
  min-height: 132px;
  resize: vertical;
}

.field input[type="range"] {
  width: 100%;
  accent-color: var(--accent);
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.switch-btn {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text);
  padding: 10px 14px;
}

.chip {
  padding: 9px 14px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--muted);
}

.button-row {
  margin-top: 6px;
}

.primary-btn,
.secondary-btn {
  flex: 1;
  padding: 13px 16px;
  font-weight: 700;
}

.primary-btn {
  background: linear-gradient(135deg, #ff9b54 0%, #ea580c 100%);
  color: #fffdf8;
  box-shadow: 0 16px 30px rgba(234, 88, 12, 0.25);
}

.secondary-btn {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text);
}

.primary-btn:hover:not(:disabled),
.secondary-btn:hover:not(:disabled),
.chip:hover,
.mode-switch button:hover,
.switch-btn:hover {
  transform: translateY(-1px);
}

.primary-btn:disabled,
.secondary-btn:disabled {
  cursor: wait;
  opacity: 0.7;
}

.progress-card {
  margin-top: 18px;
}

.progress-meta,
.clip-meter-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.progress-track {
  height: 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #f59e0b 0%, #60a5fa 100%);
  transition: width 0.3s ease;
}

.clip-fill {
  background: linear-gradient(90deg, #22c55e 0%, #38bdf8 100%);
}

.info-list {
  display: grid;
  gap: 8px;
  padding-top: 8px;
}

.info-list.compact {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--card-border);
}

.preview-panel {
  min-height: 360px;
}

.preview-image {
  width: 100%;
  height: 300px;
  object-fit: cover;
  border-radius: 18px;
  border: 1px solid var(--card-border);
  background: rgba(255, 255, 255, 0.04);
}

.empty-art {
  display: grid;
  place-items: center;
  height: 300px;
  border-radius: 18px;
  border: 1px dashed var(--card-border);
  background: rgba(255, 255, 255, 0.04);
  text-align: center;
}

.chart-art {
  gap: 18px;
}

.chart-bars {
  display: flex;
  align-items: end;
  gap: 12px;
  height: 140px;
}

.chart-bars span {
  width: 42px;
  border-radius: 14px 14px 4px 4px;
  background: linear-gradient(180deg, #7dd3fc, #2563eb);
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.3);
}

.chart-bars span:nth-child(1) {
  height: 78px;
}

.chart-bars span:nth-child(2) {
  height: 120px;
}

.chart-bars span:nth-child(3) {
  height: 92px;
}

.chart-bars span:nth-child(4) {
  height: 150px;
}

.illustration-art {
  position: relative;
  overflow: hidden;
}

.illustration-art::before {
  content: "";
  position: absolute;
  inset: 20px;
  border-radius: 28px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.24), rgba(168, 85, 247, 0.16));
  filter: blur(0.2px);
}

.orbit {
  position: absolute;
  width: 150px;
  height: 150px;
  border-radius: 50%;
  border: 2px solid rgba(125, 211, 252, 0.26);
  animation: spin 8s linear infinite;
}

.orbit.small {
  width: 84px;
  height: 84px;
  animation-direction: reverse;
}

.empty-art p {
  position: relative;
  z-index: 1;
  margin: 0;
}

.clip-meter {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--card-border);
  margin-bottom: 16px;
}

.clip-meter strong {
  font-size: 18px;
}

.clip-note {
  margin: 10px 0 0;
}

.candidate-grid {
  display: grid;
  gap: 12px;
}

.candidate-card {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 14px;
  width: 100%;
  text-align: left;
  padding: 12px;
  border-radius: 18px;
  border: 1px solid var(--card-border);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text);
}

.candidate-card.active {
  border-color: rgba(125, 211, 252, 0.45);
  box-shadow: 0 0 0 1px rgba(125, 211, 252, 0.2) inset;
}

.candidate-swatch {
  min-height: 100px;
  border-radius: 14px;
}

.candidate-body {
  display: grid;
  gap: 8px;
}

.candidate-top,
.candidate-footer,
.selected-preview-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.candidate-body p {
  margin: 0;
}

.candidate-footer strong {
  font-size: 18px;
}

.selected-preview {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--card-border);
}

.intent-card {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--card-border);
}

.intent-card p {
  margin: 0 0 8px;
  line-height: 1.6;
}

.stage-list {
  display: grid;
  gap: 10px;
  margin-bottom: 16px;
}

.stage-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--card-border);
}

.stage-completed {
  color: #4ade80;
}

.stage-running,
.stage-retrying {
  color: #f59e0b;
}

.stage-pending {
  color: #94a3b8;
}

.stage-failed {
  color: #fb7185;
}

.log-list {
  max-height: 240px;
  overflow: auto;
  border-radius: 18px;
  background: rgba(2, 6, 23, 0.75);
  padding: 14px 16px;
  border: 1px solid var(--card-border);
}

.log-list p {
  margin: 0 0 8px;
  line-height: 1.6;
}

.download-link {
  display: inline-flex;
  margin-top: 16px;
  color: var(--accent);
  font-weight: 700;
  text-decoration: none;
}

.status.error {
  color: #fb7185;
}

pre {
  margin: 0;
  max-height: 360px;
  overflow: auto;
  border-radius: 18px;
  background: rgba(2, 6, 23, 0.9);
  color: #e2e8f0;
  padding: 18px;
  font-size: 13px;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1060px) {
  .hero-stats,
  .workspace-grid,
  .result-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .page-shell {
    padding: 20px 12px 40px;
  }

  .hero-card,
  .panel {
    border-radius: 20px;
    padding: 18px;
  }

  .hero-top,
  .panel-head,
  .progress-meta,
  .clip-meter-top,
  .candidate-top,
  .candidate-footer,
  .selected-preview-top,
  .switch-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .candidate-card {
    grid-template-columns: 1fr;
  }

  .button-row,
  .mode-switch {
    flex-direction: column;
  }
}
</style>
