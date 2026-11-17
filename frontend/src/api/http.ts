import axios from "axios";

import { useToast } from "../composables/useToast";

// 统一请求实例：自动携带 Token，统一解包 {code, message, data}
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "/api/v1",
  timeout: 30000,
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("xs_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => {
    const body = response.data;
    if (body && typeof body.code === "number" && body.code !== 0) {
      useToast().show(body.message || "请求失败");
      return Promise.reject(new Error(body.message || "请求失败"));
    }
    return body?.data ?? body;
  },
  (error) => {
    const status = error.response?.status;
    const message = error.response?.data?.message || error.message || "网络异常";

    if (status === 401) {
      localStorage.removeItem("xs_token");
      // BASE_URL 在 GitHub Pages 下为 /仓库名/，避免跳到域名根目录造成 404
      const loginPath = `${import.meta.env.BASE_URL}login`.replace(/\/{2,}/g, "/");
      if (!window.location.pathname.startsWith(loginPath)) {
        window.location.href = loginPath;
      }
    }
    useToast().show(message);
    return Promise.reject(error);
  },
);

export default http;