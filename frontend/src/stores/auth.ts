import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { fetchMe } from "../api/auth";
import type { User } from "../types";

const TOKEN_KEY = "xs_token";

// 登录态：token 存 localStorage，用户信息存内存
export const useAuthStore = defineStore("auth", () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || "");
  const user = ref<User | null>(null);
  const loading = ref(false);

  const isLoggedIn = computed(() => Boolean(token.value));
  const profileComplete = computed(() => Boolean(user.value?.profile_complete));

  function setToken(value: string) {
    token.value = value;
    localStorage.setItem(TOKEN_KEY, value);
  }

  function clear() {
    token.value = "";
    user.value = null;
    localStorage.removeItem(TOKEN_KEY);
  }

  async function loadMe() {
    if (!token.value) return null;
    loading.value = true;
    try {
      user.value = await fetchMe();
      return user.value;
    } finally {
      loading.value = false;
    }
  }

  return { token, user, loading, isLoggedIn, profileComplete, setToken, clear, loadMe };
});