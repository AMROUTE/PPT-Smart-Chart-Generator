<script setup>
defineProps({
  intentInfo: {
    type: Object,
    default: null,
  },
  illustrationMeta: {
    type: Object,
    default: null,
  },
  stageCards: {
    type: Array,
    default: () => [],
  },
  recentLogs: {
    type: Array,
    default: () => [],
  },
  semanticModeText: {
    type: String,
    default: "",
  },
  chartOverrideText: {
    type: String,
    default: "",
  },
  clipScoreText: {
    type: String,
    default: "",
  },
});

function stageBadgeClass(status) {
  const map = {
    completed: "bg-green-100 text-green-700",
    running: "bg-amber-100 text-amber-700",
    retrying: "bg-orange-100 text-orange-700",
    pending: "bg-gray-100 text-gray-600",
    failed: "bg-red-100 text-red-700",
  };
  return map[status] ?? "bg-gray-100 text-gray-600";
}

function qualityStatus(meta) {
  if (!meta) return "待生成";
  if (meta.regenerated) return "已重生成";
  if (meta.regenerate_hint) return "待复核";
  return "通过";
}

function qualityBadgeClass(meta) {
  const status = qualityStatus(meta);
  if (status === "已重生成") return "bg-amber-100 text-amber-700";
  if (status === "待复核") return "bg-red-100 text-red-700";
  if (status === "通过") return "bg-green-100 text-green-700";
  return "bg-gray-100 text-gray-600";
}

function regenerateActionText(action) {
  const map = {
    local_refined_prompt: "本地 refined prompt",
    manual_review_recommended: "建议人工复核",
    none: "无需重生成",
  };
  return map[action] ?? action ?? "等待评分";
}

function scoreText(value) {
  return value == null ? "—" : String(value);
}

function confidenceText(value) {
  if (value == null) return "—";
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : String(value);
}
</script>

<template>
  <div
    class="h-full rounded-2xl border border-white/50 bg-white/60 p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-md"
  >
    <div class="mb-6">
      <h2 class="text-xl font-semibold tracking-tight text-gray-900">Pipeline 日志与状态</h2>
      <p class="mt-2 text-sm leading-6 text-gray-500">语义决策、生成阶段和回退信息都会在这里汇总。</p>
    </div>

    <div v-if="intentInfo" class="space-y-3 rounded-2xl border border-gray-100 bg-white/90 p-5">
      <p class="text-sm leading-6 text-gray-500"><span class="font-medium text-gray-900">推荐图表：</span>{{ intentInfo.chart_type }}</p>
      <p class="text-sm leading-6 text-gray-500"><span class="font-medium text-gray-900">语义意图：</span>{{ intentInfo.intent_category || "未标记" }}</p>
      <p class="text-sm leading-6 text-gray-500"><span class="font-medium text-gray-900">推荐置信度：</span>{{ confidenceText(intentInfo.recommendation_confidence) }}</p>
      <p class="text-sm leading-6 text-gray-500"><span class="font-medium text-gray-900">语义来源：</span>{{ intentInfo.source || "heuristic" }}</p>
      <p class="text-sm leading-6 text-gray-500"><span class="font-medium text-gray-900">所选模式：</span>{{ semanticModeText }}</p>
      <p class="text-sm leading-6 text-gray-500"><span class="font-medium text-gray-900">手动修正：</span>{{ chartOverrideText }}</p>
      <p class="text-sm leading-6 text-gray-500"><span class="font-medium text-gray-900">判断依据：</span>{{ intentInfo.reason || intentInfo.summary }}</p>
      <div v-if="intentInfo.recommendation_signals?.length" class="flex flex-wrap gap-2">
        <span
          v-for="signal in intentInfo.recommendation_signals"
          :key="signal"
          class="rounded-full border border-gray-200 bg-gray-50 px-2.5 py-1 text-xs font-medium text-gray-500"
        >
          {{ signal }}
        </span>
      </div>
      <p class="text-sm leading-6 text-gray-500"><span class="font-medium text-gray-900">配图主题：</span>{{ intentInfo.visual_theme || "未提供" }}</p>
      <p class="text-sm leading-6 text-gray-500">
        <span class="font-medium text-gray-900">配图模型：</span>{{ illustrationMeta?.image_model || intentInfo.image_model }}
      </p>
      <p class="text-sm leading-6 text-gray-500">
        <span class="font-medium text-gray-900">配图风格：</span>{{ illustrationMeta?.illustration_style || intentInfo.illustration_style }}
      </p>
      <p class="text-sm leading-6 text-gray-500"><span class="font-medium text-gray-900">匹配分数：</span>{{ clipScoreText }}</p>
      <p v-if="illustrationMeta?.generation_warning" class="text-sm leading-6 text-red-500">
        配图回退信息：{{ illustrationMeta.generation_warning }}
      </p>
    </div>

    <div v-if="illustrationMeta" class="mt-5 rounded-2xl border border-gray-100 bg-white/90 p-5">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-gray-400">Illustration Quality</p>
          <h3 class="mt-2 text-base font-semibold tracking-tight text-gray-900">配图评分与重生成</h3>
        </div>
        <span class="w-fit rounded-full px-3 py-1 text-xs font-medium" :class="qualityBadgeClass(illustrationMeta)">
          {{ qualityStatus(illustrationMeta) }}
        </span>
      </div>

      <div class="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div class="rounded-2xl bg-gray-50 px-4 py-3">
          <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Initial</p>
          <p class="mt-2 text-sm font-semibold text-gray-900">{{ scoreText(illustrationMeta.initial_clip_score) }}</p>
        </div>
        <div class="rounded-2xl bg-gray-50 px-4 py-3">
          <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Final</p>
          <p class="mt-2 text-sm font-semibold text-gray-900">{{ scoreText(illustrationMeta.clip_score) }}</p>
        </div>
        <div class="rounded-2xl bg-gray-50 px-4 py-3">
          <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Threshold</p>
          <p class="mt-2 text-sm font-semibold text-gray-900">{{ scoreText(illustrationMeta.score_threshold ?? 6.5) }}</p>
        </div>
        <div class="rounded-2xl bg-gray-50 px-4 py-3">
          <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Attempts</p>
          <p class="mt-2 text-sm font-semibold text-gray-900">{{ illustrationMeta.regenerate_attempts ?? 0 }}</p>
        </div>
      </div>

      <div class="mt-4 rounded-2xl bg-gray-50 px-4 py-3">
        <p class="text-[11px] uppercase tracking-[0.16em] text-gray-400">Action</p>
        <p class="mt-2 text-sm font-semibold text-gray-900">{{ regenerateActionText(illustrationMeta.regenerate_action) }}</p>
        <p v-if="illustrationMeta.regenerate_reason" class="mt-2 text-sm leading-6 text-gray-500">
          {{ illustrationMeta.regenerate_reason }}
        </p>
      </div>
    </div>

    <div class="mt-6 space-y-3">
      <div
        v-for="item in stageCards"
        :key="item.stage + item.status"
        class="flex items-center justify-between gap-3 rounded-2xl border border-gray-100 bg-white/80 px-4 py-3"
      >
        <span class="text-sm font-medium text-gray-800">{{ item.label }}</span>
        <strong class="rounded-full px-3 py-1 text-xs font-semibold" :class="stageBadgeClass(item.status)">
          {{ item.status }}
        </strong>
      </div>
    </div>

    <div
      v-if="recentLogs.length"
      class="mt-6 space-y-2 rounded-2xl border border-gray-100 bg-gray-950 p-5 text-sm text-gray-100"
    >
      <p v-for="log in recentLogs" :key="log" class="font-mono text-xs leading-6 text-gray-300">{{ log }}</p>
    </div>
    <p v-else class="mt-6 text-sm text-gray-500">处理完成后，这里会展示阶段状态和运行日志。</p>
  </div>
</template>
