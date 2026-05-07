<script setup>
import { useUserSettings } from "../composables/useUserSettings";

const { settings, resetSettings } = useUserSettings();
</script>

<template>
  <main class="page-shell inner-page">
    <section class="hero-card">
      <p class="eyebrow">Personal Settings</p>
      <h1>个人设置</h1>
      <p class="hero-copy">
        在这里配置你自己的 API key、默认语义模式、默认配图模型和调用模型。保存后，工作台会自动带上这些配置。
      </p>
    </section>

    <section class="workspace-grid workspace-grid-wide">
      <div class="panel">
        <h2>模型与 Key</h2>
        <label class="field">
          <span>Qwen API Key</span>
          <input v-model="settings.customQwenApiKey" type="password" placeholder="留空则使用系统默认 key" />
        </label>

        <label class="field">
          <span>Qwen 模型</span>
          <input v-model="settings.customQwenModel" type="text" placeholder="例如：qwen-plus" />
        </label>

        <label class="field">
          <span>WANX API Key</span>
          <input v-model="settings.customWanxApiKey" type="password" placeholder="用于通义万相配图" />
        </label>

        <label class="field">
          <span>FLUX API Key</span>
          <input v-model="settings.customFluxApiKey" type="password" placeholder="用于 Flux 配图" />
        </label>
      </div>

      <div class="panel">
        <h2>默认调用配置</h2>
        <label class="field">
          <span>默认语义模式</span>
          <select v-model="settings.defaultSemanticMode">
            <option value="local">本地规则</option>
            <option value="qwen">千问 API</option>
          </select>
        </label>

        <label class="field">
          <span>默认配图模型</span>
          <select v-model="settings.defaultImageModel">
            <option value="local">本地预览</option>
            <option value="wanx">通义万相</option>
            <option value="flux">Flux</option>
          </select>
        </label>

        <label class="field">
          <span>默认配图风格</span>
          <select v-model="settings.defaultIllustrationStyle">
            <option value="auto">自动</option>
            <option value="business">商务风</option>
            <option value="tech">科技风</option>
            <option value="education">教育风</option>
            <option value="medical">医疗风</option>
            <option value="academic">学术风</option>
            <option value="sketch">手绘风</option>
          </select>
        </label>

        <button class="secondary-btn" @click="resetSettings">恢复默认配置</button>
      </div>
    </section>
  </main>
</template>
