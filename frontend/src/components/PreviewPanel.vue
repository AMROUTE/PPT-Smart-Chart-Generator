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
  <div
    class="h-full rounded-2xl border border-white/50 bg-white/60 p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-md"
  >
    <div class="mb-6 flex items-center justify-between gap-3">
      <h2 class="text-xl font-semibold tracking-tight text-gray-900">{{ title }}</h2>
      <span v-if="loading" class="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">加载中</span>
    </div>
    <div v-if="imageUrl" class="flex min-h-[22rem] items-center justify-center overflow-hidden rounded-2xl border border-gray-100 bg-gray-50/70 p-4">
      <img
        :src="imageUrl"
        :alt="title"
        class="max-h-[28rem] w-full rounded-xl object-contain"
      />
    </div>
    <div
      v-else
      class="flex h-[22rem] items-center justify-center rounded-2xl border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-500"
    >
      {{ placeholder }}
    </div>
  </div>
</template>
