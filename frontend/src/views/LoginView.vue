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
  <main class="auth-shell">
    <section class="auth-card">
      <p class="eyebrow">Workspace Access</p>
      <h1>登录 SmartChart 工作台</h1>
      <p class="hero-copy">
        登录后可进行 PPT 拖拽上传、逐页解析、图表生成与增强版 PPT 导出。
      </p>

      <label class="field">
        <span>用户名</span>
        <input v-model="username" type="text" placeholder="例如：amanzhuole" @keyup.enter="submitLogin" />
      </label>

      <label class="field">
        <span>密码</span>
        <input v-model="password" type="password" placeholder="输入任意测试密码" @keyup.enter="submitLogin" />
      </label>

      <button class="primary-btn" @click="submitLogin">进入工作台</button>
      <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>
    </section>
  </main>
</template>
