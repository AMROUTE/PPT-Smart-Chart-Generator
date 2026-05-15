<script setup>
import AppShell from "./components/AppShell.vue";
import { useAuth } from "./composables/useAuth";
import LoginView from "./views/LoginView.vue";

const { currentUser, isAuthenticated, login, logout } = useAuth();

async function handleLogin(credentials) {
  await login(credentials.username, credentials.password);
}
</script>

<template>
  <LoginView v-if="!isAuthenticated" :on-login="handleLogin" />
  <AppShell v-else :current-user="currentUser" @logout="logout" />
</template>
