<script setup lang="ts">
import { RouterLink, useRoute } from "vue-router";

// 应用外壳：顶部品牌栏 + 内容插槽 + 底部三栏导航
const route = useRoute();
</script>

<template>
  <div class="app-frame">
    <header class="topbar">
      <div class="brand">
        <span class="brand-mark">声</span>
        新声
      </div>
      <div class="head-actions">
        <slot name="actions" />
      </div>
    </header>

    <slot />

    <nav class="tabbar">
      <RouterLink to="/home" :class="{ active: route.path === '/home' }">
        <span class="tab-icon">✨</span>搭子
      </RouterLink>
      <RouterLink to="/notes" :class="{ active: route.path === '/notes' }">
        <span class="tab-icon">📝</span>笔记
      </RouterLink>
      <RouterLink to="/plaza" :class="{ active: route.path === '/plaza' }">
        <span class="tab-icon">🛍️</span>广场
      </RouterLink>
    </nav>
  </div>
</template>

<style scoped>
.head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>