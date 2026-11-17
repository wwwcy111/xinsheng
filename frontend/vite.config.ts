import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// 开发环境将 /api 与 /uploads 代理到 FastAPI（8000 端口）
export default defineConfig({
  base: process.env.VITE_BASE || "/",
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/uploads": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});