<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { fetchRecommendations, refreshRecommendations, sendGreeting } from "../api/match";
import AppShell from "../components/AppShell.vue";
import MatchCard from "../components/MatchCard.vue";
import { useToast } from "../composables/useToast";
import { useAuthStore } from "../stores/auth";
import type { Recommendation } from "../types";

const auth = useAuthStore();
const router = useRouter();
const { show } = useToast();

const recommendation = ref<Recommendation | null>(null);
const loading = ref(true);
const refreshing = ref(false);

const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 6) return "夜深了";
  if (hour < 11) return "早上好";
  if (hour < 14) return "中午好";
  if (hour < 18) return "下午好";
  return "晚上好";
});

const dateText = computed(() => {
  const now = new Date();
  return `${now.getMonth() + 1} 月 ${now.getDate()} 日`;
});

onMounted(async () => {
  if (!auth.user) {
    await auth.loadMe();
  }
  if (!auth.user?.profile_complete) {
    loading.value = false;
    return;
  }
  await load();
});

async function load() {
  loading.value = true;
  try {
    recommendation.value = await fetchRecommendations();
  } catch {
    recommendation.value = null;
  } finally {
    loading.value = false;
  }
}

async function refresh() {
  refreshing.value = true;
  try {
    recommendation.value = await refreshRecommendations();
    show("已换一批搭子");
  } finally {
    refreshing.value = false;
  }
}

async function greet(targetUserId: number) {
  await sendGreeting(targetUserId, "嗨，看到我们兴趣挺合的，认识一下？");
  show("招呼已发送");
}

function onCopied() {
  show("话题已复制，去聊天窗口粘贴吧");
}

function logout() {
  auth.clear();
  router.replace("/login");
}
</script>

<template>
  <AppShell>
    <template #actions>
      <button class="btn btn-plain btn-sm" type="button" @click="logout">退出</button>
    </template>

    <div class="page">
      <div class="hero rise">
        <span class="eyebrow">今日搭子</span>
        <h1>{{ greeting }}，{{ auth.user?.nickname || "同学" }}</h1>
        <p class="sub">
          {{ dateText }} · 为你找到
          <strong>{{ recommendation?.items.length || 0 }}</strong>
          位同频同学
        </p>
      </div>

      <div v-if="!auth.user?.profile_complete" class="card rise">
        <h3>还差一点点</h3>
        <p class="muted text-sm mt-8">完善兴趣标签和性格后，才能为你推荐合适搭子。</p>
        <button class="btn btn-primary btn-block mt-12" type="button" @click="router.push('/tags')">
          去完善画像
        </button>
      </div>

      <div v-else-if="loading" class="card rise">
        <div class="skeleton" />
        <div class="skeleton short" />
        <div class="skeleton" />
        <p class="muted text-xs mt-12">正在为你寻找同频的人…</p>
      </div>

      <div v-else-if="!recommendation?.items.length" class="empty">
        <span class="empty-icon">🌱</span>
        今天还没有合适的搭子<br />
        邀请同学注册并完善标签，匹配会更准
      </div>

      <template v-else>
        <MatchCard
          v-for="(item, index) in recommendation.items"
          :key="item.match_id"
          :item="item"
          :index="index"
          @greet="greet"
          @copied="onCopied"
        />
        <button
          class="btn btn-ghost btn-block mt-16"
          :disabled="refreshing"
          type="button"
          @click="refresh"
        >
          {{ refreshing ? "正在换一批…" : "换一批搭子" }}
        </button>
      </template>
    </div>
  </AppShell>
</template>

<style scoped>
.hero h1 {
  margin-top: 10px;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.hero .sub {
  margin-top: 6px;
  font-size: 13px;
  color: var(--muted);
}

.hero .sub strong {
  color: var(--brand);
}

.card h3 {
  font-size: 15px;
  font-weight: 700;
}

.skeleton {
  height: 14px;
  border-radius: 8px;
  background: linear-gradient(90deg, #f1f3f6 25%, #e9edf2 37%, #f1f3f6 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
}

.skeleton.short {
  width: 62%;
  margin-top: 10px;
}

.skeleton + .skeleton {
  margin-top: 10px;
}

@keyframes shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: 0 0; }
}
</style>