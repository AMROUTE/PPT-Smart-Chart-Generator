<script setup>
import { computed, onMounted, ref } from "vue";

import { requestJobs } from "../services/api";

const jobs = ref([]);
const loading = ref(false);
const errorMessage = ref("");
const selectedJobId = ref("");

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

onMounted(fetchJobs);

const selectedJob = computed(
  () => jobs.value.find((job) => job.request_id === selectedJobId.value) ?? jobs.value[0] ?? null,
);

function badgeClass(kind, value) {
  const normalized = String(value || "unknown").toLowerCase();
  if (kind === "status") {
    if (normalized === "completed") return "bg-green-100 text-green-700";
    if (normalized === "running") return "bg-amber-100 text-amber-700";
    if (normalized === "failed") return "bg-red-100 text-red-700";
    return "bg-gray-100 text-gray-600";
  }
  if (normalized === "qwen") return "bg-blue-100 text-blue-700";
  if (normalized === "wanx") return "bg-violet-100 text-violet-700";
  if (normalized === "flux") return "bg-orange-100 text-orange-700";
  return "bg-gray-100 text-gray-600";
}
</script>

<template>
  <main class="w-full">
    <div class="mx-auto w-full max-w-6xl p-8">
      <div class="space-y-8">
        <section class="rounded-2xl border border-white/50 bg-white/60 p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl">
          <div class="flex items-center justify-between gap-4">
            <div>
              <p class="text-[11px] font-medium uppercase tracking-[0.24em] text-gray-400">Processing Records</p>
              <h1 class="mt-3 text-5xl font-semibold tracking-tight text-gray-900">日志界面</h1>
              <p class="mt-4 max-w-3xl text-base leading-7 text-gray-500">
                追踪并管理您的所有生成任务。选择左侧记录以查看完整的处理状态、参数及时间线。
              </p>
            </div>
            <button
              type="button"
              class="rounded-full bg-gray-900 px-5 py-3 text-sm font-medium text-white transition-all duration-200 ease-in-out hover:bg-gray-800 active:scale-[0.98]"
              @click="fetchJobs"
            >
              刷新
            </button>
          </div>
        </section>

        <section class="flex h-[calc(100vh-4rem)] gap-6">
          <div class="studio-scrollbar flex h-full w-1/3 flex-col overflow-y-auto pr-2">
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
                  <p class="mt-3 text-sm text-gray-800">第 {{ job.slide_number }} 页 · {{ job.illustration_style }}</p>
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

          <div class="flex flex-1 flex-col rounded-2xl border border-gray-100 bg-white p-8 shadow-sm">
            <Transition name="fade-up" mode="out-in">
              <div v-if="selectedJob" :key="selectedJob.request_id" class="flex h-full flex-col">
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <p class="text-sm font-medium text-gray-500">Selected Job</p>
                    <h2 class="mt-2 font-mono text-lg font-semibold tracking-tight text-gray-900">
                      {{ selectedJob.request_id }}
                    </h2>
                  </div>
                  <span class="rounded-full px-3 py-1 text-xs font-medium" :class="badgeClass('status', selectedJob.status)">
                    {{ selectedJob.status }}
                  </span>
                </div>

                <div class="mt-8 grid grid-cols-1 gap-4 xl:grid-cols-2">
                  <div class="rounded-2xl bg-gray-50 p-5">
                    <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Source</p>
                    <p class="mt-2 text-sm text-gray-800">{{ selectedJob.source_type }}</p>
                  </div>
                  <div class="rounded-2xl bg-gray-50 p-5">
                    <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Slide</p>
                    <p class="mt-2 text-sm text-gray-800">第 {{ selectedJob.slide_number }} 页</p>
                  </div>
                  <div class="rounded-2xl bg-gray-50 p-5">
                    <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Semantic Mode</p>
                    <p class="mt-2 text-sm text-gray-800">{{ selectedJob.semantic_mode }}</p>
                  </div>
                  <div class="rounded-2xl bg-gray-50 p-5">
                    <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Image Model</p>
                    <p class="mt-2 text-sm text-gray-800">{{ selectedJob.image_model }}</p>
                  </div>
                  <div class="rounded-2xl bg-gray-50 p-5">
                    <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Chart Override</p>
                    <p class="mt-2 text-sm text-gray-800">{{ selectedJob.chart_type_override || "自动推荐" }}</p>
                  </div>
                  <div class="rounded-2xl bg-gray-50 p-5">
                    <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Illustration Style</p>
                    <p class="mt-2 text-sm text-gray-800">{{ selectedJob.illustration_style }}</p>
                  </div>
                </div>

                <div class="mt-8 rounded-2xl border border-gray-100 bg-gray-50 p-6">
                  <h3 class="text-sm font-semibold tracking-tight text-gray-900">时间信息</h3>
                  <div class="mt-4 space-y-3 text-sm text-gray-500">
                    <p><span class="font-medium text-gray-800">创建时间：</span>{{ selectedJob.created_at }}</p>
                    <p><span class="font-medium text-gray-800">更新时间：</span>{{ selectedJob.updated_at }}</p>
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
