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
</script>

<template>
  <div class="panel result-panel">
    <h2>Pipeline 日志与状态</h2>
    <div v-if="intentInfo" class="intent-card">
      <p><strong>推荐图表：</strong>{{ intentInfo.chart_type }}</p>
      <p><strong>语义来源：</strong>{{ intentInfo.source || "heuristic" }}</p>
      <p><strong>所选模式：</strong>{{ semanticModeText }}</p>
      <p><strong>手动修正：</strong>{{ chartOverrideText }}</p>
      <p><strong>判断依据：</strong>{{ intentInfo.reason || intentInfo.summary }}</p>
      <p><strong>配图主题：</strong>{{ intentInfo.visual_theme || "未提供" }}</p>
      <p><strong>配图模型：</strong>{{ illustrationMeta?.image_model || intentInfo.image_model }}</p>
      <p><strong>配图风格：</strong>{{ illustrationMeta?.illustration_style || intentInfo.illustration_style }}</p>
      <p><strong>匹配分数：</strong>{{ clipScoreText }}</p>
      <p v-if="illustrationMeta?.generation_warning" class="warning-text">
        配图回退信息：{{ illustrationMeta.generation_warning }}
      </p>
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
    <p v-else class="placeholder">处理完成后，这里会展示阶段状态和运行日志。</p>
  </div>
</template>
