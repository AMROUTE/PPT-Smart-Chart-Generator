<script setup>
import { computed, ref } from "vue";

const file = ref(null);
const slideNumber = ref(1);
const loading = ref(false);
const errorMessage = ref("");
const response = ref(null);

const fileInfo = computed(() => {
  if (!file.value) {
    return null;
  }
  return {
    name: file.value.name,
    size: `${(file.value.size / 1024 / 1024).toFixed(2)} MB`,
    type: file.value.type || "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    lastModified: new Date(file.value.lastModified).toLocaleString("zh-CN"),
  };
});

async function submitForm() {
  errorMessage.value = "";
  response.value = null;

  if (!file.value) {
    errorMessage.value = "请先上传 PPTX 文件。";
    return;
  }

  loading.value = true;
  const formData = new FormData();
  formData.append("file", file.value);
  formData.append("slide_number", String(slideNumber.value));

  try {
    const res = await fetch("/api/process", {
      method: "POST",
      body: formData,
    });
    const payload = await res.json();
    if (!res.ok) {
      throw new Error(payload.detail || "处理失败，请稍后再试。");
    }
    response.value = payload;
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    loading.value = false;
  }
}

function handleFileChange(event) {
  const [selected] = event.target.files || [];
  file.value = selected ?? null;
}
</script>

<template>
  <main class="page-shell">
    <section class="hero-card">
      <p class="eyebrow">Week 1 Delivery</p>
      <h1>语义驱动的 PPT 智能图表生成系统</h1>
      <p class="hero-copy">
        前端已切换到 Vue 3。当前版本聚焦第一周目标：上传 PPT、选择页码、查看基础信息，并联通后端处理入口。
      </p>
    </section>

    <section class="workspace-grid">
      <div class="panel">
        <h2>上传与处理</h2>
        <label class="field">
          <span>PPT 文件</span>
          <input type="file" accept=".pptx" @change="handleFileChange" />
        </label>

        <label class="field">
          <span>处理页码</span>
          <input v-model.number="slideNumber" type="number" min="1" />
        </label>

        <button class="primary-btn" :disabled="loading" @click="submitForm">
          {{ loading ? "处理中..." : "一键生成图表与配图" }}
        </button>

        <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>
      </div>

      <div class="panel">
        <h2>文件基本信息</h2>
        <div v-if="fileInfo" class="info-list">
          <p><strong>文件名：</strong>{{ fileInfo.name }}</p>
          <p><strong>文件大小：</strong>{{ fileInfo.size }}</p>
          <p><strong>文件类型：</strong>{{ fileInfo.type }}</p>
          <p><strong>修改时间：</strong>{{ fileInfo.lastModified }}</p>
          <p><strong>目标页码：</strong>{{ slideNumber }}</p>
        </div>
        <p v-else class="placeholder">上传文件后，这里会显示本地识别到的基础信息。</p>
      </div>
    </section>

    <section class="result-grid">
      <div class="panel result-panel">
        <h2>Pipeline 返回结果</h2>
        <pre v-if="response">{{ JSON.stringify(response, null, 2) }}</pre>
        <p v-else class="placeholder">处理完成后，这里会展示后端返回的结构化结果。</p>
      </div>

      <div class="panel milestone-panel">
        <h2>第一周里程碑</h2>
        <ul>
          <li>Vue 3 前端骨架已建立</li>
          <li>PPT 上传与页码选择已完成</li>
          <li>可展示文件基础信息</li>
          <li>可调用后端 `/api/process` 接口</li>
        </ul>
      </div>
    </section>
  </main>
</template>
