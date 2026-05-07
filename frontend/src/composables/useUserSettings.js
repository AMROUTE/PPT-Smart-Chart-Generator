import { reactive, watch } from "vue";

const STORAGE_KEY = "ppt-smart-chart-settings";

const defaults = {
  customQwenApiKey: "",
  customQwenModel: "qwen-plus",
  customWanxApiKey: "",
  customFluxApiKey: "",
  defaultSemanticMode: "local",
  defaultImageModel: "local",
  defaultIllustrationStyle: "auto",
};

const saved = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : "";
const state = reactive(saved ? { ...defaults, ...JSON.parse(saved) } : { ...defaults });

if (typeof window !== "undefined") {
  watch(
    state,
    (value) => {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    },
    { deep: true },
  );
}

export function useUserSettings() {
  function resetSettings() {
    Object.assign(state, defaults);
  }

  return {
    settings: state,
    resetSettings,
  };
}
