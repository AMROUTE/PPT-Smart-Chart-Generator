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
      <p class="text-sm leading-6 text-gray-500"><span class="font-medium text-gray-900">语义来源：</span>{{ intentInfo.source || "heuristic" }}</p>
      <p class="text-sm leading-6 text-gray-500"><span class="font-medium text-gray-900">所选模式：</span>{{ semanticModeText }}</p>
      <p class="text-sm leading-6 text-gray-500"><span class="font-medium text-gray-900">手动修正：</span>{{ chartOverrideText }}</p>
      <p class="text-sm leading-6 text-gray-500"><span class="font-medium text-gray-900">判断依据：</span>{{ intentInfo.reason || intentInfo.summary }}</p>
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
