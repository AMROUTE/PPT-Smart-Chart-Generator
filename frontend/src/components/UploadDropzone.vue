<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  file: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["select"]);
const dragging = ref(false);

const dropzoneText = computed(() => {
  if (props.file) {
    return `${props.file.name} · ${(props.file.size / 1024 / 1024).toFixed(2)} MB`;
  }
  return "拖拽 PPTX 到这里，或点击选择文件";
});

function handleFiles(files) {
  const [selected] = files || [];
  if (selected) {
    emit("select", selected);
  }
}

function onInputChange(event) {
  handleFiles(event.target.files);
}

function onDragOver(event) {
  event.preventDefault();
  dragging.value = true;
}

function onDragLeave() {
  dragging.value = false;
}

function onDrop(event) {
  event.preventDefault();
  dragging.value = false;
  handleFiles(event.dataTransfer?.files);
}
</script>

<template>
  <label
    class="flex h-full min-h-64 cursor-pointer items-center justify-center rounded-3xl border-2 border-dashed border-gray-200 bg-gray-50/80 p-8 transition-all duration-300 ease-out hover:-translate-y-1 hover:border-gray-300 hover:shadow-md"
    :class="dragging ? 'border-gray-400 bg-slate-50 shadow-sm' : ''"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
  >
    <input class="sr-only" type="file" accept=".pptx" @change="onInputChange" />
    <div class="flex max-w-md flex-col items-center text-center">
      <div class="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-white text-gray-500 shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
        <svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M12 16V7m0 0-3.5 3.5M12 7l3.5 3.5M5 16.5v1A2.5 2.5 0 0 0 7.5 20h9a2.5 2.5 0 0 0 2.5-2.5v-1"
            stroke="currentColor"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.7"
          />
        </svg>
      </div>
      <strong class="text-xl font-semibold tracking-tight text-gray-900">拖拽上传 PPTX</strong>
      <p class="mt-3 text-sm leading-6 text-gray-500">将演示文稿拖到这里，或点击从本地选择文件。</p>
      <p class="mt-4 rounded-full bg-white px-4 py-2 text-sm font-medium text-gray-500 shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
        {{ dropzoneText }}
      </p>
    </div>
  </label>
</template>
