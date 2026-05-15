import { computed, ref } from "vue";
import { requestLogin } from "../services/api";

const STORAGE_KEY = "ppt-smart-chart-user";
const storedUser = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : "";
const currentUser = ref(storedUser ? JSON.parse(storedUser) : null);

export function useAuth() {
  const isAuthenticated = computed(() => Boolean(currentUser.value));

  async function login(username, password) {
    if (!username?.trim()) {
      throw new Error("请输入用户名。");
    }
    if (!password?.trim()) {
      throw new Error("请输入密码。");
    }
    const formData = new FormData();
    formData.append("username", username.trim());
    formData.append("password", password);
    const payload = await requestLogin(formData);
    currentUser.value = {
      name: payload.user.display_name,
      username: payload.user.username,
      role: "project-member",
    };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(currentUser.value));
  }

  function logout() {
    currentUser.value = null;
    window.localStorage.removeItem(STORAGE_KEY);
  }

  return {
    currentUser,
    isAuthenticated,
    login,
    logout,
  };
}
