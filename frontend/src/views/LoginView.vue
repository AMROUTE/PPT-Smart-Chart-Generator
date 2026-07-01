<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  onLogin: {
    type: Function,
    required: true,
  },
  onRegister: {
    type: Function,
    required: true,
  },
});

const mode = ref("login");
const username = ref("");
const password = ref("");
const confirmPassword = ref("");
const errorMessage = ref("");
const loading = ref(false);

const isRegisterMode = computed(() => mode.value === "register");
const title = computed(() => (isRegisterMode.value ? "创建 SmartChart 账号" : "登录 SmartChart 工作台"));
const submitText = computed(() => {
  if (loading.value) {
    return isRegisterMode.value ? "正在创建..." : "正在登录...";
  }
  return isRegisterMode.value ? "创建账号并进入" : "进入工作台";
});

function switchMode(nextMode) {
  mode.value = nextMode;
  errorMessage.value = "";
  confirmPassword.value = "";
}

async function submitAuth() {
  errorMessage.value = "";
  if (isRegisterMode.value && password.value !== confirmPassword.value) {
    errorMessage.value = "两次输入的密码不一致。";
    return;
  }
  loading.value = true;
  try {
    const action = isRegisterMode.value ? props.onRegister : props.onLogin;
    await action({
      username: username.value,
      password: password.value,
    });
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-[#F9F9F9] px-6 py-12">
    <section
      class="w-full max-w-xl rounded-3xl border border-white/50 bg-white/60 p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-md"
    >
      <div class="space-y-4">
        <p class="text-[11px] font-medium uppercase tracking-[0.24em] text-gray-400">Workspace Access</p>
        <h1 class="text-5xl font-semibold tracking-tight text-gray-900">{{ title }}</h1>
        <p class="max-w-lg text-base leading-7 text-gray-500">
          登录后可进行 PPT 拖拽上传、逐页解析、图表生成与增强版 PPT 导出。
        </p>
      </div>

      <div class="mt-8 space-y-5">
        <div class="grid grid-cols-2 rounded-full bg-gray-100 p-1">
          <button
            type="button"
            class="rounded-full px-4 py-2 text-sm font-medium transition-all duration-200 ease-in-out active:scale-[0.98]"
            :class="mode === 'login' ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-900'"
            @click="switchMode('login')"
          >
            登录
          </button>
          <button
            type="button"
            class="rounded-full px-4 py-2 text-sm font-medium transition-all duration-200 ease-in-out active:scale-[0.98]"
            :class="mode === 'register' ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-900'"
            @click="switchMode('register')"
          >
            注册
          </button>
        </div>

        <label class="block space-y-2">
          <span class="text-sm font-medium text-gray-500">用户名</span>
          <input
            v-model="username"
            type="text"
            placeholder=""
            class="w-full rounded-2xl border border-transparent bg-gray-100 px-4 py-3 text-sm text-gray-900 outline-none transition-all duration-200 ease-in-out placeholder:text-gray-400 focus:border-gray-300 focus:bg-white focus:ring-1 focus:ring-gray-300 focus:shadow-sm"
            @keyup.enter="submitAuth"
          />
        </label>

        <label class="block space-y-2">
          <span class="text-sm font-medium text-gray-500">密码</span>
          <input
            v-model="password"
            type="password"
            placeholder=""
            class="w-full rounded-2xl border border-transparent bg-gray-100 px-4 py-3 text-sm text-gray-900 outline-none transition-all duration-200 ease-in-out placeholder:text-gray-400 focus:border-gray-300 focus:bg-white focus:ring-1 focus:ring-gray-300 focus:shadow-sm"
            @keyup.enter="submitAuth"
          />
        </label>

        <label v-if="isRegisterMode" class="block space-y-2">
          <span class="text-sm font-medium text-gray-500">确认密码</span>
          <input
            v-model="confirmPassword"
            type="password"
            placeholder=""
            class="w-full rounded-2xl border border-transparent bg-gray-100 px-4 py-3 text-sm text-gray-900 outline-none transition-all duration-200 ease-in-out placeholder:text-gray-400 focus:border-gray-300 focus:bg-white focus:ring-1 focus:ring-gray-300 focus:shadow-sm"
            @keyup.enter="submitAuth"
          />
        </label>

        <button
          type="button"
          class="w-full rounded-full bg-gray-900 px-5 py-3 text-sm font-medium text-white transition-all duration-200 ease-in-out hover:bg-gray-800 active:scale-[0.98]"
          :disabled="loading"
          @click="submitAuth"
        >
          {{ submitText }}
        </button>

        <p v-if="errorMessage" class="text-sm text-red-500">{{ errorMessage }}</p>
      </div>
    </section>
  </main>
</template>
