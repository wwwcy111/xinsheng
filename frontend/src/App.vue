<script setup lang="ts">
import { RouterView } from "vue-router";
import { useToast } from "./composables/useToast";

const { toast } = useToast();
</script>

<template>
  <RouterView />

  <!-- 全局轻提示 -->
  <Transition name="toast">
    <div v-if="toast.visible" class="toast">{{ toast.message }}</div>
  </Transition>
</template>