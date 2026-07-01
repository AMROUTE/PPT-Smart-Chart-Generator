<script setup>
import { computed } from "vue";

import SelectMenu from "../components/SelectMenu.vue";
import { illustrationStyleOptions, imageModelOptions, semanticModeOptions } from "../config/options";
import { useUserSettings } from "../composables/useUserSettings";

const { settings, resetSettings } = useUserSettings();

const missingDefaultKeys = computed(() => {
  const missing = [];
  if (settings.defaultSemanticMode === "qwen" && !settings.customQwenApiKey?.trim()) {
    missing.push("Qwen API Key");
  }
  if (settings.defaultImageModel === "wanx" && !settings.customWanxApiKey?.trim()) {
    missing.push("WANX API Key");
  }
  if (settings.defaultImageModel === "flux" && !settings.customFluxApiKey?.trim()) {
    missing.push("FLUX API Key");
  }
  return missing;
});
</script>

<template>
  <main class="w-full">
    <div class="mx-auto w-full max-w-6xl p-4 sm:p-6 xl:p-8">
      <div class="space-y-8">
        <section class="rounded-2xl border border-white/50 bg-white/60 p-5 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl sm:p-8">
          <p class="text-[11px] font-medium uppercase tracking-[0.24em] text-gray-400">Personal Settings</p>
          <h1 class="mt-3 text-4xl font-semibold tracking-tight text-gray-900 sm:text-5xl">个人设置</h1>
          <p class="mt-4 max-w-3xl text-base leading-7 text-gray-500">
            在这里配置你自己的 API key、默认语义模式、默认配图模型和调用模型。保存后，工作台会自动带上这些配置。
          </p>
          <p v-if="missingDefaultKeys.length" class="mt-5 rounded-2xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-700">
            当前默认配置还缺少 {{ missingDefaultKeys.join("、") }}。
          </p>
        </section>

        <section class="grid grid-cols-12 gap-6 xl:gap-8">
          <div class="col-span-12 rounded-2xl border border-white/50 bg-white/60 p-5 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl sm:p-8 lg:col-span-7">
            <h2 class="text-2xl font-semibold tracking-tight text-gray-900">模型与 Key</h2>
            <div class="mt-8 space-y-5">
              <label class="block space-y-2">
                <span class="text-sm font-medium text-gray-500">Qwen API Key</span>
                <input
                  v-model="settings.customQwenApiKey"
                  type="password"
                  placeholder="选择 Qwen 语义分析时必填"
                  class="w-full rounded-2xl border border-transparent bg-gray-100 px-4 py-3 text-sm text-gray-900 outline-none transition-all duration-200 ease-in-out placeholder:text-gray-400 focus:border-gray-300 focus:bg-white focus:ring-1 focus:ring-gray-300 focus:shadow-sm"
                />
              </label>

              <label class="block space-y-2">
                <span class="text-sm font-medium text-gray-500">Qwen 模型</span>
                <input
                  v-model="settings.customQwenModel"
                  type="text"
                  placeholder="例如：qwen-plus"
                  class="w-full rounded-2xl border border-transparent bg-gray-100 px-4 py-3 text-sm text-gray-900 outline-none transition-all duration-200 ease-in-out placeholder:text-gray-400 focus:border-gray-300 focus:bg-white focus:ring-1 focus:ring-gray-300 focus:shadow-sm"
                />
              </label>

              <label class="block space-y-2">
                <span class="text-sm font-medium text-gray-500">WANX API Key</span>
                <input
                  v-model="settings.customWanxApiKey"
                  type="password"
                  placeholder="选择 WANX 配图时必填"
                  class="w-full rounded-2xl border border-transparent bg-gray-100 px-4 py-3 text-sm text-gray-900 outline-none transition-all duration-200 ease-in-out placeholder:text-gray-400 focus:border-gray-300 focus:bg-white focus:ring-1 focus:ring-gray-300 focus:shadow-sm"
                />
              </label>

              <label class="block space-y-2">
                <span class="text-sm font-medium text-gray-500">FLUX API Key</span>
                <input
                  v-model="settings.customFluxApiKey"
                  type="password"
                  placeholder="选择 FLUX 配图时必填"
                  class="w-full rounded-2xl border border-transparent bg-gray-100 px-4 py-3 text-sm text-gray-900 outline-none transition-all duration-200 ease-in-out placeholder:text-gray-400 focus:border-gray-300 focus:bg-white focus:ring-1 focus:ring-gray-300 focus:shadow-sm"
                />
              </label>
            </div>
          </div>

          <div class="relative z-10 col-span-12 overflow-visible rounded-2xl border border-white/50 bg-white/60 p-5 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl sm:p-8 lg:col-span-5">
            <h2 class="text-2xl font-semibold tracking-tight text-gray-900">默认调用配置</h2>
            <div class="mt-8 space-y-5">
              <label class="relative block space-y-2">
                <span class="text-sm font-medium text-gray-500">默认语义模式</span>
                <SelectMenu v-model="settings.defaultSemanticMode" :options="semanticModeOptions" />
              </label>

              <label class="relative block space-y-2">
                <span class="text-sm font-medium text-gray-500">默认配图模型</span>
                <SelectMenu v-model="settings.defaultImageModel" :options="imageModelOptions" />
              </label>

              <label class="relative block space-y-2">
                <span class="text-sm font-medium text-gray-500">默认配图风格</span>
                <SelectMenu v-model="settings.defaultIllustrationStyle" :options="illustrationStyleOptions" />
              </label>

              <button
                type="button"
                class="mt-2 w-full rounded-full border border-gray-200 bg-white px-5 py-3 text-sm font-medium text-gray-700 transition-all duration-200 ease-in-out hover:bg-gray-50 active:scale-[0.98]"
                @click="resetSettings"
              >
                恢复默认配置
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  </main>
</template>
