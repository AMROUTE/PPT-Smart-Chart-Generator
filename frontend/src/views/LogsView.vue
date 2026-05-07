<script setup>
import { onMounted, ref } from "vue";

import { requestJobs } from "../services/api";

const jobs = ref([]);
const loading = ref(false);
const errorMessage = ref("");

async function fetchJobs() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const payload = await requestJobs(40);
    jobs.value = payload.jobs || [];
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    loading.value = false;
  }
}

onMounted(fetchJobs);
</script>

<template>
  <main class="page-shell inner-page">
    <section class="hero-card">
      <p class="eyebrow">Processing Records</p>
      <h1>日志界面</h1>
      <p class="hero-copy">这里展示数据库里最近的处理任务，包括来源、模型、状态和生成结果路径。</p>
    </section>

    <section class="workspace-grid workspace-grid-wide">
      <div class="panel">
        <div class="panel-header">
          <h2>最近任务</h2>
          <button class="ghost-btn" @click="fetchJobs">刷新</button>
        </div>
        <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>
        <p v-else-if="loading" class="placeholder">正在加载任务记录...</p>
        <div v-else-if="jobs.length" class="outline-list">
          <div v-for="job in jobs" :key="job.request_id" class="outline-card plain-card">
            <div class="outline-title">
              <strong>{{ job.request_id }}</strong>
              <span>{{ job.status }}</span>
            </div>
            <p>来源：{{ job.source_type }} · 第 {{ job.slide_number }} 页 · 语义模式：{{ job.semantic_mode }}</p>
            <p>图表修正：{{ job.chart_type_override || "自动推荐" }} · 配图风格：{{ job.illustration_style }} · 配图模型：{{ job.image_model }}</p>
            <small>创建时间：{{ job.created_at }} ｜ 更新时间：{{ job.updated_at }}</small>
          </div>
        </div>
        <p v-else class="placeholder">数据库里暂时还没有处理记录。</p>
      </div>

      <div class="panel">
        <h2>日志说明</h2>
        <ul class="plain-list">
          <li>`source_type` 区分 PPT 上传与文本演示。</li>
          <li>`status` 展示任务最终完成状态。</li>
          <li>这里的数据来自后端 SQLite 数据库中的 `processing_jobs` 表。</li>
        </ul>
      </div>
    </section>
  </main>
</template>
