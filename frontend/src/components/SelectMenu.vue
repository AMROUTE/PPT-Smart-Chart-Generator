<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  options: {
    type: Array,
    required: true,
  },
});

const emit = defineEmits(["update:modelValue"]);

const open = ref(false);
const root = ref(null);

const selectedOption = computed(
  () => props.options.find((item) => item.value === props.modelValue) ?? props.options[0] ?? null,
);

function toggleOpen() {
  open.value = !open.value;
}

function selectOption(value) {
  emit("update:modelValue", value);
  open.value = false;
}

function closeOnOutside(event) {
  if (!root.value?.contains(event.target)) {
    open.value = false;
  }
}

function closeOnEscape(event) {
  if (event.key === "Escape") {
    open.value = false;
  }
}

onMounted(() => {
  document.addEventListener("mousedown", closeOnOutside);
  document.addEventListener("keydown", closeOnEscape);
});

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", closeOnOutside);
  document.removeEventListener("keydown", closeOnEscape);
});
</script>

<template>
  <div ref="root" class="relative" :class="open ? 'z-[120]' : 'z-0'">
      <button
        type="button"
        class="flex w-full items-center justify-between gap-4 rounded-2xl border border-transparent bg-gray-100 px-4 py-3 text-left transition-all duration-200 ease-in-out hover:bg-gray-50 focus:border-gray-300 focus:bg-white focus:outline-none focus:ring-1 focus:ring-gray-300 focus:shadow-sm"
        :class="open ? 'relative z-50 bg-white ring-1 ring-gray-300 shadow-sm' : ''"
        @click="toggleOpen"
      >
      <div class="min-w-0">
        <strong class="block text-sm font-semibold tracking-tight text-gray-900">{{ selectedOption?.label }}</strong>
        <span v-if="selectedOption?.hint" class="mt-1 block text-xs leading-5 text-gray-500">{{ selectedOption.hint }}</span>
      </div>
      <span class="flex h-5 w-5 flex-shrink-0 items-center justify-center text-gray-400 transition-transform duration-200" :class="open ? 'rotate-180' : ''" aria-hidden="true">
        <svg class="h-4 w-4" viewBox="0 0 20 20" fill="none">
          <path d="M5 7.5 10 12.5l5-5" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" />
        </svg>
      </span>
    </button>

      <div
        v-if="open"
        class="absolute left-0 right-0 top-[calc(100%+0.75rem)] z-[100] max-h-80 overflow-y-auto space-y-2 rounded-2xl border border-white/50 bg-white/95 p-3 shadow-[0_20px_60px_rgb(0,0,0,0.14)] backdrop-blur-xl"
      >
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        class="flex w-full items-start justify-between gap-3 rounded-2xl px-4 py-3 text-left transition-all duration-200 ease-in-out hover:-translate-y-0.5 hover:bg-gray-50"
        :class="option.value === modelValue ? 'bg-gray-100 text-gray-900' : 'text-gray-700'"
        @click="selectOption(option.value)"
      >
        <div class="min-w-0">
          <strong class="block text-sm font-semibold tracking-tight">{{ option.label }}</strong>
          <span v-if="option.hint" class="mt-1 block text-xs leading-5 text-gray-500">{{ option.hint }}</span>
        </div>
        <span v-if="option.value === modelValue" class="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center text-gray-900" aria-hidden="true">
          <svg class="h-4 w-4" viewBox="0 0 20 20" fill="none">
            <path d="m5 10 3.2 3.2L15 6.5" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.9" />
          </svg>
        </span>
      </button>
    </div>
  </div>
</template>
