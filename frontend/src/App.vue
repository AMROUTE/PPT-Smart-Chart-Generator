<script setup>
import AppShell from "./components/AppShell.vue";
import { useAuth } from "./composables/useAuth";
import LoginView from "./views/LoginView.vue";

const { currentUser, isAuthenticated, login, register, logout } = useAuth();

async function handleLogin(credentials) {
  await login(credentials.username, credentials.password);
}

async function handleRegister(credentials) {
  await register(credentials.username, credentials.password);
}
</script>

<template>
  <LoginView v-if="!isAuthenticated" :on-login="handleLogin" :on-register="handleRegister" />
  <AppShell v-else :current-user="currentUser" @logout="logout" />
</template>
