<script setup lang="ts">
import type { MindNode } from "../types";

// 递归渲染思维导图树，不依赖图形库
defineOptions({ name: "MindMapTree" });

withDefaults(
  defineProps<{
    node?: MindNode | null;
    depth?: number;
  }>(),
  { depth: 0 },
);
</script>

<template>
  <div v-if="node" class="mind-node" :class="`depth-${depth}`">
    <div class="node-title">
      <span class="dot" :class="`dot-${depth}`" />
      {{ node.title }}
    </div>
    <div v-if="node.children?.length" class="children">
      <MindMapTree
        v-for="(child, index) in node.children"
        :key="index"
        :node="child"
        :depth="depth + 1"
      />
    </div>
  </div>
</template>

<style scoped>
.mind-node + .mind-node {
  margin-top: 6px;
}

.node-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #33363c;
  padding: 6px 10px;
  background: #f7f9fc;
  border-radius: 10px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 3px;
  flex: none;
}

.dot-0 { background: var(--brand); }
.dot-1 { background: var(--mint); }
.dot-2 { background: var(--amber); }

.children {
  margin-left: 14px;
  padding-left: 12px;
  border-left: 1px dashed rgba(61, 123, 255, 0.22);
  margin-top: 6px;
  display: grid;
  gap: 6px;
}
</style>