import { createRouter, createWebHistory } from "vue-router";

// 路由表：登录、标签、首页、笔记、广场
const router = createRouter({
  // 使用 Vite 注入的 base，兼容 GitHub Pages 子路径（/仓库名/）部署
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", redirect: "/home" },
    {
      path: "/login",
      name: "login",
      component: () => import("../views/LoginView.vue"),
      meta: { public: true },
    },
    {
      path: "/tags",
      name: "tags",
      component: () => import("../views/TagsView.vue"),
    },
    {
      path: "/home",
      name: "home",
      component: () => import("../views/HomeView.vue"),
    },
    {
      path: "/notes",
      name: "notes",
      component: () => import("../views/NotesView.vue"),
    },
    {
      path: "/plaza",
      name: "plaza",
      component: () => import("../views/PlazaView.vue"),
    },
  ],
  scrollBehavior: () => ({ top: 0 }),
});

// 未登录访问受保护页面时跳转登录页
router.beforeEach((to) => {
  const token = localStorage.getItem("xs_token");
  if (!to.meta.public && !token) {
    return { path: "/login", query: { redirect: to.fullPath } };
  }
  if (to.path === "/login" && token) {
    return "/home";
  }
  return true;
});

export default router;