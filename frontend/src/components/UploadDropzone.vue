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
  <label class="dropzone" :class="{ dragging }" @dragover="onDragOver" @dragleave="onDragLeave" @drop="onDrop">
    <input class="dropzone-input" type="file" accept=".pptx" @change="onInputChange" />
    <div class="dropzone-copy">
      <strong>拖拽上传</strong>
      <p>{{ dropzoneText }}</p>
    </div>
  </label>
</template>
