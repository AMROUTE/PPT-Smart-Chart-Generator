<script setup>
defineProps({
  slides: {
    type: Array,
    default: () => [],
  },
  activeSlide: {
    type: Number,
    default: 1,
  },
});

const emit = defineEmits(["select-slide"]);
</script>

<template>
  <div class="panel">
    <h2>每页 PPT 解析</h2>
    <div v-if="slides.length" class="outline-list">
      <button
        v-for="item in slides"
        :key="item.slide_number"
        class="outline-card"
        :class="{ active: item.slide_number === activeSlide }"
        @click="emit('select-slide', item.slide_number)"
      >
        <div class="outline-title">
          <strong>第 {{ item.slide_number }} 页</strong>
          <span>{{ item.table_count }} 个表格 · {{ item.shape_count }} 个元素</span>
        </div>
        <p>{{ item.text_content || "该页暂无可提取文本。" }}</p>
        <small v-if="item.table_titles?.length">表格：{{ item.table_titles.join("、") }}</small>
      </button>
    </div>
    <p v-else class="placeholder">上传 PPT 后，这里会显示整份文档的逐页解析结果。</p>
  </div>
</template>
