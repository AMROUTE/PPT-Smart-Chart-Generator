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
  <div
    class="h-full rounded-2xl border border-white/50 bg-white/60 p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-md"
  >
    <div class="mb-6">
      <h2 class="text-xl font-semibold tracking-tight text-gray-900">每页 PPT 解析</h2>
      <p class="mt-2 text-sm leading-6 text-gray-500">逐页查看提取到的表格、文本和页面结构。</p>
    </div>

    <div v-if="slides.length" class="space-y-3">
      <button
        v-for="item in slides"
        :key="item.slide_number"
        type="button"
        class="w-full rounded-2xl border px-4 py-4 text-left transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-sm"
        :class="
          item.slide_number === activeSlide
            ? 'border-gray-200 bg-gray-100/80'
            : 'border-gray-100 bg-white/80 hover:border-gray-200'
        "
        @click="emit('select-slide', item.slide_number)"
      >
        <div class="flex items-start justify-between gap-3">
          <strong class="text-sm font-semibold tracking-tight text-gray-900">第 {{ item.slide_number }} 页</strong>
          <span class="text-xs text-gray-400">{{ item.table_count }} 个表格 · {{ item.shape_count }} 个元素</span>
        </div>
        <p class="mt-2 text-sm leading-6 text-gray-500">{{ item.text_content || "该页暂无可提取文本。" }}</p>
        <small v-if="item.table_titles?.length" class="mt-2 block text-xs text-gray-400">
          表格：{{ item.table_titles.join("、") }}
        </small>
      </button>
    </div>

    <div
      v-else
      class="flex min-h-60 items-center justify-center rounded-2xl border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-500"
    >
      上传 PPT 后，这里会显示整份文档的逐页解析结果。
    </div>
  </div>
</template>
