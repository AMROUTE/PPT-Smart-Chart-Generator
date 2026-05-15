import { createRouter, createWebHistory } from "vue-router";

import DashboardView from "../views/DashboardView.vue";
import LogsView from "../views/LogsView.vue";
import SettingsView from "../views/SettingsView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/workspace" },
    { path: "/workspace", name: "workspace", component: DashboardView },
    { path: "/logs", name: "logs", component: LogsView },
    { path: "/settings", name: "settings", component: SettingsView },
  ],
});

export default router;
