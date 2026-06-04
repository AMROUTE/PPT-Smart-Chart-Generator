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
  <div class="flex h-screen w-full flex-col overflow-hidden bg-[#F9F9F9] lg:flex-row">
    <aside class="flex w-full flex-shrink-0 flex-col gap-4 border-b border-gray-200 bg-white/50 p-4 backdrop-blur-xl lg:h-full lg:w-64 lg:justify-between lg:border-b-0 lg:border-r">
      <div class="space-y-4 lg:space-y-8">
        <div class="space-y-3 px-2 pt-2">
          <p class="text-[11px] font-medium uppercase tracking-[0.24em] text-gray-400">SmartChart Hub</p>
          <h2 class="text-2xl font-semibold tracking-tight text-gray-900 lg:text-[30px]">项目工作区</h2>
        </div>

        <nav class="flex gap-2 overflow-x-auto pb-1 lg:block lg:space-y-2 lg:overflow-visible lg:pb-0">
          <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" custom v-slot="{ navigate, isActive }">
            <button
              type="button"
              class="whitespace-nowrap rounded-full px-4 py-3 text-center text-sm font-medium transition-all duration-300 ease-in-out lg:w-full lg:text-left"
              :class="
                isActive
                  ? 'bg-gray-200/70 text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:-translate-y-0.5 hover:bg-white/80 hover:text-gray-900 hover:shadow-sm'
              "
              @click="navigate"
            >
              {{ item.label }}
            </button>
          </RouterLink>
        </nav>
      </div>

      <div class="flex items-center justify-between gap-3 rounded-2xl border border-white/50 bg-white/70 p-3 shadow-[0_8px_30px_rgb(0,0,0,0.04)] backdrop-blur-xl lg:block lg:space-y-4 lg:p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-gray-100 text-gray-500">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="M12 12c2.761 0 5-2.462 5-5.5S14.761 1 12 1 7 3.462 7 6.5 9.239 12 12 12Zm0 2c-4.418 0-8 2.91-8 6.5 0 .828.672 1.5 1.5 1.5h13c.828 0 1.5-.672 1.5-1.5 0-3.59-3.582-6.5-8-6.5Z"
                fill="currentColor"
              />
            </svg>
          </div>
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold tracking-tight text-gray-900">{{ props.currentUser.name }}</p>
            <p class="truncate text-sm text-gray-500">{{ props.currentUser.username || "workspace-user" }}</p>
          </div>
        </div>

        <button
          type="button"
          class="shrink-0 rounded-full border border-gray-200 bg-white px-4 py-3 text-sm font-medium text-gray-700 transition-all duration-200 ease-in-out hover:-translate-y-0.5 hover:bg-gray-50 hover:shadow-sm active:scale-[0.98] lg:w-full"
          @click="emit('logout')"
        >
          退出登录
        </button>
      </div>
    </aside>

    <section class="relative min-h-0 flex-1 overflow-y-auto">
      <RouterView />
    </section>
  </div>
</template>
