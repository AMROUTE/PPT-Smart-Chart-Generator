import { computed, ref } from "vue";
import { requestLogin, requestRegister } from "../services/api";

const STORAGE_KEY = "ppt-smart-chart-user";
const storedUser = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : "";
const currentUser = ref(storedUser ? JSON.parse(storedUser) : null);

export function useAuth() {
  const isAuthenticated = computed(() => Boolean(currentUser.value));

  function validateCredentials(username, password) {
    if (!username?.trim()) {
      throw new Error("请输入用户名。");
    }
    if (!password?.trim()) {
      throw new Error("请输入密码。");
    }
  }

  function persistUser(user) {
    currentUser.value = {
      id: user.id,
      name: user.display_name,
      username: user.username,
      role: "project-member",
    };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(currentUser.value));
  }

  async function login(username, password) {
    validateCredentials(username, password);
    const formData = new FormData();
    formData.append("username", username.trim());
    formData.append("password", password);
    const payload = await requestLogin(formData);
    persistUser(payload.user);
  }

  async function register(username, password) {
    validateCredentials(username, password);
    const formData = new FormData();
    formData.append("username", username.trim());
    formData.append("password", password);
    const payload = await requestRegister(formData);
    persistUser(payload.user);
  }

  function logout() {
    currentUser.value = null;
    window.localStorage.removeItem(STORAGE_KEY);
  }

  return {
    currentUser,
    isAuthenticated,
    login,
    register,
    logout,
  };
}
