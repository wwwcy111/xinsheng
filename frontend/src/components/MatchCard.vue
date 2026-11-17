<script setup lang="ts">
import type { MatchItem } from "../types";

const props = defineProps<{ item: MatchItem; index: number }>();
const emit = defineEmits<{ greet: [id: number]; copied: [text: string] }>();

// 复制话题，便于直接粘贴到聊天窗口
async function copyTopic(text: string) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    document.body.removeChild(area);
  }
  emit("copied", text);
}
</script>

<template>
  <article class="match-card card rise" :class="`rise-${Math.min(index + 1, 4)}`">
    <div class="head">
      <div class="avatar">{{ item.nickname.slice(0, 1) }}</div>
      <div class="who">
        <div class="name">
          {{ item.nickname }}
          <span v-if="item.common_tags.length" class="badge">共同 {{ item.common_tags.length }} 个兴趣</span>
        </div>
        <div class="tags">
          <span v-for="tag in item.common_tags" :key="tag" class="mini-tag">{{ tag }}</span>
          <span v-if="!item.common_tags.length" class="muted text-xs">性格互补，值得认识</span>
        </div>
      </div>
      <div class="score-ring" :style="{ '--p': item.score }">
        <span>{{ item.score }}</span>
      </div>
    </div>

    <p class="reason">{{ item.reason }}</p>

    <div class="topics">
      <button
        v-for="(topic, i) in item.topics"
        :key="i"
        class="topic"
        type="button"
        @click="copyTopic(topic)"
      >
        <span class="topic-index">{{ i + 1 }}</span>
        <span class="topic-text">{{ topic }}</span>
        <span class="topic-copy">复制</span>
      </button>
    </div>

    <div class="foot">
      <span class="hint">不敢开口？点话题就能复制</span>
      <button class="btn btn-primary btn-sm" type="button" @click="emit('greet', item.target_user_id)">
        打个招呼
      </button>
    </div>
  </article>
</template>

<style scoped>
.match-card {
  position: relative;
  overflow: hidden;
}

.match-card::before {
  content: "";
  position: absolute;
  right: -40px;
  top: -50px;
  width: 130px;
  height: 130px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(46, 211, 183, 0.16), transparent 70%);
  pointer-events: none;
}

.head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 46px;
  height: 46px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #6fa8ff, #2ed3b7);
  flex: none;
}

.who {
  flex: 1;
  min-width: 0;
}

.name {
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.badge {
  font-size: 11px;
  font-weight: 500;
  color: #119c86;
  background: var(--mint-soft);
  padding: 3px 8px;
  border-radius: 999px;
}

.tags {
  margin-top: 5px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.mini-tag {
  font-size: 11px;

  color: #5b6474;
  background: #f2f4f7;
  padding: 3px 8px;
  border-radius: 999px;
}

.score-ring {
  --p: 0;
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: conic-gradient(from -90deg, #2ed3b7 calc(var(--p) * 1%), #eef1f5 0);
  display: grid;
  place-items: center;
  position: relative;
  flex: none;
}

.score-ring::after {
  content: "";
  position: absolute;
  inset: 5px;
  background: #fff;
  border-radius: 50%;
}

.score-ring span {
  position: relative;
  z-index: 1;
  font-weight: 700;
  font-size: 15px;
}

.reason {
  margin-top: 14px;
  font-size: 14px;
  line-height: 1.65;
  color: #3a3a3d;
  background: #fafbfc;
  border-radius: 14px;
  padding: 12px 14px;
}

.topics {
  margin-top: 12px;
  display: grid;
  gap: 8px;
}

.topic {
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
  border: 1px dashed rgba(61, 123, 255, 0.28);
  background: rgba(61, 123, 255, 0.05);
  border-radius: 14px;
  padding: 10px 12px;
  cursor: pointer;
  font-size: 13px;
  color: #33547f;
  transition: background 0.18s ease, border 0.18s ease;
}

.topic:hover {
  background: rgba(61, 123, 255, 0.09);
}

.topic-index {
  width: 20px;
  height: 20px;
  border-radius: 7px;
  background: #fff;
  color: var(--brand);
  font-size: 11px;
  font-weight: 700;
  display: grid;
  place-items: center;
  flex: none;
}

.topic-text {
  flex: 1;
  line-height: 1.5;
}

.topic-copy {
  font-size: 11px;
  color: var(--brand);
  opacity: 0.8;
  flex: none;
}

.foot {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.hint {
  font-size: 11px;
  color: var(--muted);
}
</style>