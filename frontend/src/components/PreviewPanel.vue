<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  imageUrl: {
    type: String,
    default: "",
  },
  loading: {
    type: Boolean,
    default: false,
  },
  placeholder: {
    type: String,
    default: "暂无内容",
  },
});
</script>

<template>
  <div class="panel preview-panel">
    <div class="panel-header">
      <h2>{{ title }}</h2>
      <span v-if="loading" class="micro-badge">加载中</span>
    </div>
    <img v-if="imageUrl" :src="imageUrl" :alt="title" class="preview-image" />
    <p v-else class="placeholder">{{ placeholder }}</p>
  </div>
</template>
