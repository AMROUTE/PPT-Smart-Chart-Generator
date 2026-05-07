<script setup>
const props = defineProps({
  currentUser: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["logout"]);

const navItems = [
  { label: "总工作台", to: "/workspace" },
  { label: "日志界面", to: "/logs" },
  { label: "个人设置", to: "/settings" },
];
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar-card">
      <div>
        <p class="eyebrow">SmartChart Hub</p>
        <h2 class="sidebar-title">项目工作区</h2>
      </div>

      <nav class="sidebar-nav">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="sidebar-link">
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <p><strong>{{ currentUser.name }}</strong></p>
        <p>{{ currentUser.username || "workspace-user" }}</p>
        <button class="ghost-btn" @click="emit('logout')">退出登录</button>
      </div>
    </aside>

    <section class="app-shell-content">
      <RouterView />
    </section>
  </div>
</template>
