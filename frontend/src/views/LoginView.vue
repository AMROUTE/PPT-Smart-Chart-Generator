<script setup>
import { ref } from "vue";

const props = defineProps({
  onLogin: {
    type: Function,
    required: true,
  },
});

const username = ref("");
const password = ref("");
const errorMessage = ref("");

async function submitLogin() {
  errorMessage.value = "";
  try {
    await props.onLogin({
      username: username.value,
      password: password.value,
    });
  } catch (error) {
    errorMessage.value = error.message;
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
        <h1 class="text-5xl font-semibold tracking-tight text-gray-900">登录 SmartChart 工作台</h1>
        <p class="max-w-lg text-base leading-7 text-gray-500">
          登录后可进行 PPT 拖拽上传、逐页解析、图表生成与增强版 PPT 导出。
        </p>
      </div>

      <div class="mt-8 space-y-5">
        <label class="block space-y-2">
          <span class="text-sm font-medium text-gray-500">用户名</span>
          <input
            v-model="username"
            type="text"
            placeholder="例如：amanzhuole"
            class="w-full rounded-2xl border border-transparent bg-gray-100 px-4 py-3 text-sm text-gray-900 outline-none transition-all duration-200 ease-in-out placeholder:text-gray-400 focus:border-gray-300 focus:bg-white focus:ring-1 focus:ring-gray-300 focus:shadow-sm"
            @keyup.enter="submitLogin"
          />
        </label>

        <label class="block space-y-2">
          <span class="text-sm font-medium text-gray-500">密码</span>
          <input
            v-model="password"
            type="password"
            placeholder="输入任意测试密码"
            class="w-full rounded-2xl border border-transparent bg-gray-100 px-4 py-3 text-sm text-gray-900 outline-none transition-all duration-200 ease-in-out placeholder:text-gray-400 focus:border-gray-300 focus:bg-white focus:ring-1 focus:ring-gray-300 focus:shadow-sm"
            @keyup.enter="submitLogin"
          />
        </label>

        <button
          type="button"
          class="w-full rounded-full bg-gray-900 px-5 py-3 text-sm font-medium text-white transition-all duration-200 ease-in-out hover:bg-gray-800 active:scale-[0.98]"
          @click="submitLogin"
        >
          进入工作台
        </button>

        <p v-if="errorMessage" class="text-sm text-red-500">{{ errorMessage }}</p>
      </div>
    </section>
  </main>
</template>
