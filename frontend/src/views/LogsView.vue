<script setup>
import { computed, onMounted, ref, watch } from "vue";

import { requestJobDetail, requestJobs } from "../services/api";

const jobs = ref([]);
const loading = ref(false);
const errorMessage = ref("");
const selectedJobId = ref("");
const selectedJobDetail = ref(null);
const detailLoading = ref(false);
const detailError = ref("");

async function fetchJobs() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const payload = await requestJobs(40);
    jobs.value = payload.jobs || [];
    if (!selectedJobId.value && jobs.value.length) {
      selectedJobId.value = jobs.value[0].request_id;
    }
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    loading.value = false;
  }
}

async function fetchJobDetail(requestId) {
  if (!requestId) {
    selectedJobDetail.value = null;
    return;
  }
  detailLoading.value = true;
  detailError.value = "";
  try {
    const payload = await requestJobDetail(requestId);
    selectedJobDetail.value = payload.job || null;
  } catch (error) {
    selectedJobDetail.value = null;
    detailError.value = error.message;
  } finally {
    detailLoading.value = false;
  }
}

onMounted(fetchJobs);

watch(selectedJobId, (requestId) => {
  fetchJobDetail(requestId);
});

const selectedJob = computed(
  () => jobs.value.find((job) => job.request_id === selectedJobId.value) ?? jobs.value[0] ?? null,
);
const detailJob = computed(() => selectedJobDetail.value ?? selectedJob.value);
const qualityStatus = computed(() => {
  const meta = detailJob.value?.illustration_meta;
  if (!meta) return "待生成";
  if (meta.regenerated) return "已重生成";
  if (meta.regenerate_hint) return "待复核";
  return "通过";
});
const qualityBadgeClass = computed(() => {
  if (qualityStatus.value === "已重生成") return "bg-amber-100 text-amber-700";
  if (qualityStatus.value === "待复核") return "bg-red-100 text-red-700";
  if (qualityStatus.value === "通过") return "bg-green-100 text-green-700";
  return "bg-gray-100 text-gray-600";
});

function badgeClass(kind, value) {
  const normalized = String(value || "unknown").toLowerCase();
  if (kind === "status") {
    if (normalized === "completed") return "bg-green-100 text-green-700";
    if (normalized === "running") return "bg-amber-100 text-amber-700";
    if (normalized === "retrying") return "bg-orange-100 text-orange-700";
    if (normalized === "failed") return "bg-red-100 text-red-700";
    return "bg-gray-100 text-gray-600";
  }
  if (normalized === "qwen") return "bg-blue-100 text-blue-700";
  if (normalized === "wanx") return "bg-violet-100 text-violet-700";
  if (normalized === "flux") return "bg-orange-100 text-orange-700";
  return "bg-gray-100 text-gray-600";
}

function actionText(action) {
  const map = {
    local_refined_prompt: "本地 refined prompt",
    manual_review_recommended: "建议人工复核",
    none: "无需重生成",
  };
  return map[action] ?? action ?? "等待评分";
}

function percentText(value) {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "—";
}

function qualityComponentItems(meta) {
  const components = meta?.quality_components || {};
  return Object.entries(components)
    .filter(([key]) => key !== "score")
    .map(([key, value]) => ({ key, value }));
}

function componentBadgeClass(value) {
  return value ? "border-green-200 bg-green-50 text-green-700" : "border-gray-200 bg-gray-50 text-gray-500";
}

function chartQualityStatusText(status) {
  const map = {
    pass: "通过",
    attention: "需留意",
    review: "待复核",
    fallback: "Fallback",
  };
  return map[status] ?? "待生成";
}

function chartQualityBadgeClass(status) {
  if (status === "pass") return "bg-green-100 text-green-700";
  if (status === "attention") return "bg-amber-100 text-amber-700";
  if (status === "review" || status === "fallback") return "bg-red-100 text-red-700";
  return "bg-gray-100 text-gray-600";
}
</script>

<template>
  <main class="w-full">
    <div class="mx-auto w-full max-w-6xl p-4 sm:p-6 xl:p-8">
      <div class="space-y-8">
        <section class="rounded-2xl border border-white/50 bg-white/60 p-5 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl sm:p-8">
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p class="text-[11px] font-medium uppercase tracking-[0.24em] text-gray-400">Processing Records</p>
              <h1 class="mt-3 text-4xl font-semibold tracking-tight text-gray-900 sm:text-5xl">日志界面</h1>
              <p class="mt-4 max-w-3xl text-base leading-7 text-gray-500">
                追踪生成任务、质量评分、版式诊断和运行日志，为 Milestone 2 验收保留证据。
              </p>
            </div>
            <button
              type="button"
              class="w-fit rounded-full bg-gray-900 px-5 py-3 text-sm font-medium text-white transition-all duration-200 ease-in-out hover:bg-gray-800 active:scale-[0.98]"
              @click="fetchJobs"
            >
              刷新
            </button>
          </div>
        </section>

        <section class="flex flex-col gap-6 xl:h-[calc(100vh-4rem)] xl:flex-row">
          <div class="studio-scrollbar flex max-h-80 flex-col overflow-y-auto pr-1 xl:h-full xl:max-h-none xl:w-1/3 xl:pr-2">
            <div class="space-y-3">
              <div v-if="errorMessage" class="rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-500">
                {{ errorMessage }}
              </div>
              <div
                v-else-if="loading"
                class="rounded-2xl border border-white/50 bg-white/60 p-6 text-sm text-gray-500 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl"
              >
                正在加载任务记录...
              </div>
              <template v-else-if="jobs.length">
                <button
                  v-for="job in jobs"
                  :key="job.request_id"
                  type="button"
                  class="w-full rounded-2xl border border-transparent bg-white/60 p-4 text-left shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg hover:border-gray-200"
                  :class="selectedJob?.request_id === job.request_id ? 'border-gray-200 bg-white' : ''"
                  @click="selectedJobId = job.request_id"
                >
                  <div class="flex items-start justify-between gap-3">
                    <strong class="font-mono text-sm text-gray-800">{{ job.request_id }}</strong>
                    <span class="rounded-full px-2.5 py-1 text-xs font-medium" :class="badgeClass('status', job.status)">
                      {{ job.status }}
                    </span>
                  </div>
                  <div class="mt-3 flex flex-wrap gap-2">
                    <span class="rounded-full px-2.5 py-1 text-xs font-medium" :class="badgeClass('meta', job.semantic_mode)">
                      {{ job.semantic_mode }}
                    </span>
                    <span class="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">
                      {{ job.source_type }}
                    </span>
                    <span class="rounded-full px-2.5 py-1 text-xs font-medium" :class="badgeClass('meta', job.image_model)">
                      {{ job.image_model }}
                    </span>
                  </div>
                  <p class="mt-3 text-sm text-gray-800">
                    第 {{ job.slide_number }} 页 · {{ job.chart_type || "auto" }} · {{ job.progress || 0 }}%
                  </p>
                  <p class="mt-1 text-xs text-gray-400">{{ job.updated_at }}</p>
                </button>
              </template>
              <div
                v-else
                class="rounded-2xl border border-white/50 bg-white/60 p-6 text-sm text-gray-500 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl"
              >
                暂无处理记录。
              </div>
            </div>
          </div>

          <div class="studio-scrollbar flex min-h-[32rem] flex-1 flex-col overflow-y-auto rounded-2xl border border-gray-100 bg-white p-5 shadow-sm sm:p-8">
            <Transition name="fade-up" mode="out-in">
              <div v-if="selectedJob && detailJob" :key="selectedJob.request_id" class="flex flex-col">
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <p class="text-sm font-medium text-gray-500">Selected Job</p>
                    <h2 class="mt-2 font-mono text-lg font-semibold tracking-tight text-gray-900">
                      {{ selectedJob.request_id }}
                    </h2>
                  </div>
                  <span class="rounded-full px-3 py-1 text-xs font-medium" :class="badgeClass('status', detailJob.status)">
                    {{ detailJob.status }}
                  </span>
                </div>

                <div v-if="detailLoading" class="mt-6 rounded-2xl border border-gray-100 bg-gray-50 p-4 text-sm text-gray-500">
                  正在加载任务详情...
                </div>
                <div v-else-if="detailError" class="mt-6 rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-500">
                  {{ detailError }}
                </div>

                <div class="mt-8 grid grid-cols-1 gap-4 xl:grid-cols-2">
                  <div class="rounded-2xl bg-gray-50 p-5">
                    <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Source</p>
                    <p class="mt-2 text-sm text-gray-800">{{ detailJob.source_type }}</p>
                  </div>
                  <div class="rounded-2xl bg-gray-50 p-5">
                    <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Slide</p>
                    <p class="mt-2 text-sm text-gray-800">第 {{ detailJob.slide_number }} 页</p>
                  </div>
                  <div class="rounded-2xl bg-gray-50 p-5">
                    <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Semantic Mode</p>
                    <p class="mt-2 text-sm text-gray-800">{{ detailJob.semantic_mode }}</p>
                  </div>
                  <div class="rounded-2xl bg-gray-50 p-5">
                    <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Image Model</p>
                    <p class="mt-2 text-sm text-gray-800">{{ detailJob.image_model }}</p>
                  </div>
                  <div class="rounded-2xl bg-gray-50 p-5">
                    <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Chart Type</p>
                    <p class="mt-2 text-sm text-gray-800">{{ detailJob.chart_type || detailJob.chart_type_override || "自动推荐" }}</p>
                  </div>
                  <div class="rounded-2xl bg-gray-50 p-5">
                    <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Illustration Style</p>
                    <p class="mt-2 text-sm text-gray-800">{{ detailJob.illustration_style }}</p>
                  </div>
                </div>

                <div v-if="detailJob.chart_spec && Object.keys(detailJob.chart_spec).length" class="mt-8 rounded-2xl border border-gray-100 bg-gray-50 p-6">
                  <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Chart Quality</p>
                      <h3 class="mt-2 text-sm font-semibold tracking-tight text-gray-900">图表生成质量</h3>
                    </div>
                    <div class="flex flex-wrap gap-2">
                      <span class="w-fit rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">
                        {{ detailJob.chart_spec.quality_score ?? "—" }} / 10
                      </span>
                      <span class="w-fit rounded-full px-3 py-1 text-xs font-medium" :class="chartQualityBadgeClass(detailJob.chart_spec.quality_status)">
                        {{ chartQualityStatusText(detailJob.chart_spec.quality_status) }}
                      </span>
                    </div>
                  </div>

                  <div class="mt-5 grid grid-cols-2 gap-3 xl:grid-cols-4">
                    <div class="rounded-2xl bg-white px-4 py-3">
                      <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Data Points</p>
                      <p class="mt-2 text-sm font-semibold text-gray-900">{{ detailJob.chart_spec.data_points ?? "—" }}</p>
                    </div>
                    <div class="rounded-2xl bg-white px-4 py-3">
                      <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Series</p>
                      <p class="mt-2 text-sm font-semibold text-gray-900">{{ detailJob.chart_spec.series_count ?? "—" }}</p>
                    </div>
                    <div class="rounded-2xl bg-white px-4 py-3">
                      <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Coverage</p>
                      <p class="mt-2 text-sm font-semibold text-gray-900">{{ percentText(detailJob.chart_spec.quality_checks?.numeric_coverage) }}</p>
                    </div>
                    <div class="rounded-2xl bg-white px-4 py-3">
                      <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Readability</p>
                      <p class="mt-2 text-sm font-semibold text-gray-900">{{ detailJob.chart_spec.quality_checks?.readability || "full" }}</p>
                    </div>
                  </div>
                  <div v-if="detailJob.chart_spec.review_reason" class="mt-4 rounded-2xl bg-white px-4 py-3">
                    <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Quality Gate</p>
                    <p class="mt-2 text-sm leading-6 text-gray-600">{{ detailJob.chart_spec.review_reason }}</p>
                  </div>
                </div>

                <div v-if="detailJob.illustration_meta && Object.keys(detailJob.illustration_meta).length" class="mt-8 rounded-2xl border border-gray-100 bg-gray-50 p-6">
                  <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Illustration Quality</p>
                      <h3 class="mt-2 text-sm font-semibold tracking-tight text-gray-900">配图评分与重生成</h3>
                    </div>
                    <span class="w-fit rounded-full px-3 py-1 text-xs font-medium" :class="qualityBadgeClass">
                      {{ qualityStatus }}
                    </span>
                  </div>

                  <div class="mt-5 grid grid-cols-2 gap-3 xl:grid-cols-4">
                    <div class="rounded-2xl bg-white px-4 py-3">
                      <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Initial</p>
                      <p class="mt-2 text-sm font-semibold text-gray-900">{{ detailJob.illustration_meta.initial_clip_score ?? "—" }}</p>
                    </div>
                    <div class="rounded-2xl bg-white px-4 py-3">
                      <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Final</p>
                      <p class="mt-2 text-sm font-semibold text-gray-900">{{ detailJob.illustration_meta.clip_score ?? "—" }}</p>
                    </div>
                    <div class="rounded-2xl bg-white px-4 py-3">
                      <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Threshold</p>
                      <p class="mt-2 text-sm font-semibold text-gray-900">{{ detailJob.illustration_meta.score_threshold ?? 6.5 }}</p>
                    </div>
                    <div class="rounded-2xl bg-white px-4 py-3">
                      <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Attempts</p>
                      <p class="mt-2 text-sm font-semibold text-gray-900">{{ detailJob.illustration_meta.regenerate_attempts ?? 0 }}</p>
                    </div>
                  </div>

                  <div class="mt-4 rounded-2xl bg-white px-4 py-3">
                    <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Action</p>
                    <p class="mt-2 text-sm font-semibold text-gray-900">{{ actionText(detailJob.illustration_meta.regenerate_action) }}</p>
                    <p v-if="detailJob.illustration_meta.regenerate_reason" class="mt-2 text-sm leading-6 text-gray-500">
                      {{ detailJob.illustration_meta.regenerate_reason }}
                    </p>
                  </div>

                  <div v-if="qualityComponentItems(detailJob.illustration_meta).length" class="mt-4 rounded-2xl bg-white px-4 py-3">
                    <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Quality Components</p>
                    <div class="mt-3 flex flex-wrap gap-2">
                      <span
                        v-for="item in qualityComponentItems(detailJob.illustration_meta)"
                        :key="item.key"
                        class="rounded-full border px-2.5 py-1 text-xs font-medium"
                        :class="componentBadgeClass(item.value)"
                      >
                        {{ item.key }}
                      </span>
                    </div>
                  </div>

                  <div v-if="detailJob.illustration_meta.local_render_features?.length" class="mt-4 rounded-2xl bg-white px-4 py-3">
                    <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Local Render Features</p>
                    <div class="mt-3 flex flex-wrap gap-2">
                      <span
                        v-for="feature in detailJob.illustration_meta.local_render_features"
                        :key="feature"
                        class="rounded-full border border-blue-100 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700"
                      >
                        {{ feature }}
                      </span>
                    </div>
                  </div>
                </div>

                <div v-if="detailJob.layout && Object.keys(detailJob.layout).length" class="mt-8 rounded-2xl border border-gray-100 bg-gray-50 p-6">
                  <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p class="text-xs uppercase tracking-[0.18em] text-gray-400">PPT Layout</p>
                      <h3 class="mt-2 text-sm font-semibold tracking-tight text-gray-900">写回版式诊断</h3>
                    </div>
                    <span class="w-fit rounded-full px-3 py-1 text-xs font-medium" :class="detailJob.layout.layout_warning ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'">
                      {{ detailJob.layout.insertion_mode || "inline" }}
                    </span>
                  </div>
                  <div class="mt-5 grid gap-3 xl:grid-cols-3">
                    <div class="rounded-2xl bg-white px-4 py-3">
                      <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Overlap Score</p>
                      <p class="mt-2 text-sm font-semibold text-gray-900">{{ detailJob.layout.overlap_score ?? "—" }}</p>
                    </div>
                    <div class="rounded-2xl bg-white px-4 py-3">
                      <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Pair Overlap</p>
                      <p class="mt-2 text-sm font-semibold text-gray-900">{{ detailJob.layout.pair_overlap ?? "—" }}</p>
                    </div>
                    <div class="rounded-2xl bg-white px-4 py-3">
                      <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Original Preserved</p>
                      <p class="mt-2 text-sm font-semibold text-gray-900">{{ detailJob.layout.original_slide_preserved ? "是" : "否" }}</p>
                    </div>
                  </div>
                </div>

                <div v-if="detailJob.stage_history?.length" class="mt-8 rounded-2xl border border-gray-100 bg-gray-50 p-6">
                  <h3 class="text-sm font-semibold tracking-tight text-gray-900">阶段记录</h3>
                  <div class="mt-4 space-y-3">
                    <div
                      v-for="stage in detailJob.stage_history"
                      :key="stage.stage + stage.timestamp"
                      class="flex items-center justify-between gap-3 rounded-2xl bg-white px-4 py-3 text-sm"
                    >
                      <span class="font-medium text-gray-800">{{ stage.stage }}</span>
                      <span class="rounded-full px-3 py-1 text-xs font-medium" :class="badgeClass('status', stage.status)">
                        {{ stage.status }}
                      </span>
                    </div>
                  </div>
                </div>

                <div v-if="detailJob.logs?.length" class="mt-8 rounded-2xl border border-gray-900 bg-gray-950 p-5">
                  <h3 class="text-sm font-semibold tracking-tight text-white">运行日志</h3>
                  <div class="mt-4 space-y-2">
                    <p v-for="log in detailJob.logs" :key="log" class="font-mono text-xs leading-6 text-gray-300">{{ log }}</p>
                  </div>
                </div>

                <div class="mt-8 rounded-2xl border border-gray-100 bg-gray-50 p-6">
                  <h3 class="text-sm font-semibold tracking-tight text-gray-900">时间信息</h3>
                  <div class="mt-4 space-y-3 text-sm text-gray-500">
                    <p><span class="font-medium text-gray-800">创建时间：</span>{{ detailJob.created_at }}</p>
                    <p><span class="font-medium text-gray-800">更新时间：</span>{{ detailJob.updated_at }}</p>
                  </div>
                </div>
              </div>

              <div
                v-else
                key="empty"
                class="flex flex-1 items-center justify-center rounded-2xl border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-500"
              >
                选择左侧记录后查看详情。
              </div>
            </Transition>
          </div>
        </section>
      </div>
    </div>
  </main>
</template>
