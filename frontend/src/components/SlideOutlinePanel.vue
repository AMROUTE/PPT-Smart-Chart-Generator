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

function diagnosticsOf(item) {
  return item?.diagnostics || {};
}

function numericValue(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function pageKind(item) {
  const diagnostics = diagnosticsOf(item);
  if (item?.is_empty || diagnostics.is_empty) {
    return { label: "空页", className: "bg-gray-100 text-gray-500" };
  }
  if (numericValue(item?.table_count ?? diagnostics.table_count) > 0) {
    return { label: "表格页", className: "bg-blue-100 text-blue-700" };
  }
  if (numericValue(item?.picture_count ?? diagnostics.picture_count) > 0) {
    return { label: "图片页", className: "bg-emerald-100 text-emerald-700" };
  }
  if (numericValue(diagnostics.non_empty_text_shape_count) > 0 || item?.text_content) {
    return { label: "文本页", className: "bg-amber-100 text-amber-700" };
  }
  return { label: "待复核", className: "bg-red-100 text-red-700" };
}

function diagnosticBadges(item) {
  const diagnostics = diagnosticsOf(item);
  const badges = [];
  const pictureCount = numericValue(item?.picture_count ?? diagnostics.picture_count);
  const placeholderCount = numericValue(item?.placeholder_count ?? diagnostics.placeholder_count);
  const inferred = Boolean(diagnostics.has_inferred_table);
  const textCount = numericValue(diagnostics.non_empty_text_shape_count);

  if (pictureCount > 0) {
    badges.push(`${pictureCount} 图`);
  }
  if (placeholderCount > 0) {
    badges.push(`${placeholderCount} 占位`);
  }
  if (textCount > 0) {
    badges.push(`${textCount} 文本块`);
  }
  if (inferred) {
    badges.push("文本推断表格");
  }
  return badges;
}

function diagnosticMetrics(item) {
  const diagnostics = diagnosticsOf(item);
  return [
    { label: "表格", value: numericValue(item?.table_count ?? diagnostics.table_count) },
    { label: "图片", value: numericValue(item?.picture_count ?? diagnostics.picture_count) },
    { label: "文本块", value: numericValue(diagnostics.non_empty_text_shape_count) },
    { label: "元素", value: numericValue(item?.shape_count ?? diagnostics.shape_count) },
  ];
}
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
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <strong class="text-sm font-semibold tracking-tight text-gray-900">第 {{ item.slide_number }} 页</strong>
              <span class="rounded-full px-2.5 py-1 text-xs font-medium" :class="pageKind(item).className">
                {{ pageKind(item).label }}
              </span>
            </div>
            <div v-if="diagnosticBadges(item).length" class="mt-2 flex flex-wrap gap-1.5">
              <span
                v-for="badge in diagnosticBadges(item)"
                :key="badge"
                class="rounded-full border border-gray-200 bg-white/80 px-2 py-0.5 text-[11px] font-medium text-gray-500"
              >
                {{ badge }}
              </span>
            </div>
          </div>
          <span class="shrink-0 text-xs text-gray-400">{{ item.table_count }} 个表格 · {{ item.shape_count }} 个元素</span>
        </div>
        <p class="mt-3 max-h-24 overflow-hidden text-sm leading-6 text-gray-500">{{ item.text_content || "该页暂无可提取文本。" }}</p>
        <div class="mt-4 grid grid-cols-4 gap-2 border-t border-gray-100 pt-3">
          <div
            v-for="metric in diagnosticMetrics(item)"
            :key="metric.label"
            class="min-w-0"
          >
            <p class="text-[10px] font-medium text-gray-400">{{ metric.label }}</p>
            <p class="mt-1 text-sm font-semibold text-gray-800">{{ metric.value }}</p>
          </div>
        </div>
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
