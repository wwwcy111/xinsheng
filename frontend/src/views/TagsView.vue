<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { fetchTags, updateProfile } from "../api/auth";
import { useToast } from "../composables/useToast";
import { useAuthStore } from "../stores/auth";
import type { Tag } from "../types";

const router = useRouter();
const auth = useAuthStore();
const { show } = useToast();

const tags = ref<Tag[]>([]);
const selected = ref<number[]>([]);
const personality = ref<"introvert" | "neutral" | "extrovert">("neutral");
const socialPref = ref<"one_to_one" | "small_group" | "random">("random");
const loading = ref(true);
const saving = ref(false);

const CATEGORY_LABEL: Record<string, string> = {
  sports: "运动",
  arts: "艺术",
  game: "游戏",
  study: "学习",
  life: "生活",
};

const PERSONALITIES = [
  { value: "introvert", label: "慢热内向", desc: "先观察，再靠近", icon: "🌙" },
  { value: "neutral", label: "自在切换", desc: "看场合，也看人", icon: "🌤️" },
  { value: "extrovert", label: "外向主动", desc: "先开口，再熟悉", icon: "☀️" },
] as const;

const SOCIAL_PREFS = [
  { value: "one_to_one", label: "一对一深聊" },
  { value: "small_group", label: "小群体一起" },
  { value: "random", label: "随缘就好" },
] as const;

const groups = computed(() => {
  const map = new Map<string, Tag[]>();
  for (const tag of tags.value) {
    const list = map.get(tag.category) || [];
    list.push(tag);
    map.set(tag.category, list);
  }
  return Array.from(map.entries()).map(([category, items]) => ({
    category,
    label: CATEGORY_LABEL[category] || category,
    items,
  }));
});

onMounted(async () => {
  if (!auth.user) {
    await auth.loadMe();
  }
  personality.value = auth.user?.personality || "neutral";
  socialPref.value = auth.user?.social_pref || "random";
  selected.value = (auth.user?.tags || []).map((tag) => tag.id);
  tags.value = await fetchTags();
  loading.value = false;
});

function toggleTag(id: number) {
  if (selected.value.includes(id)) {
    selected.value = selected.value.filter((item) => item !== id);
    return;
  }
  if (selected.value.length >= 10) {
    show("最多选择 10 个兴趣标签");
    return;
  }
  selected.value = [...selected.value, id];
}

async function save() {
  if (selected.value.length < 3) {
    show("至少选择 3 个兴趣标签");
    return;
  }
  saving.value = true;
  try {
    const user = await updateProfile({
      tag_ids: selected.value,
      personality: personality.value,
      social_pref: socialPref.value,
    });
    auth.user = user;
    show("画像已保存，去看看你的搭子");
    router.replace("/home");
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="app-frame">
    <header class="topbar">
      <div class="brand">
        <span class="brand-mark">声</span>
        完善画像
      </div>
      <span class="count">{{ selected.length }}/10</span>
    </header>

    <div class="page">
      <div class="intro rise">
        <h1>先让我们认识一下你</h1>
        <p class="sub">选择 3-10 个兴趣标签，AI 会据此寻找同频搭子</p>
      </div>

      <div v-if="loading" class="empty">正在加载兴趣标签…</div>

      <template v-else>
        <section v-for="group in groups" :key="group.category" class="card group rise">
          <h3>{{ group.label }}</h3>
          <div class="chip-row mt-12">
            <button
              v-for="tag in group.items"
              :key="tag.id"
              type="button"
              class="chip"
              :class="{ active: selected.includes(tag.id) }"
              @click="toggleTag(tag.id)"
            >
              <span v-if="tag.icon">{{ tag.icon }}</span>
              {{ tag.tag_name }}
            </button>
          </div>
        </section>

        <section class="card rise">
          <h3>你的性格</h3>
          <div class="persona-row mt-12">
            <button
              v-for="item in PERSONALITIES"
              :key="item.value"
              type="button"
              class="persona"
              :class="{ active: personality === item.value }"
              @click="personality = item.value"
            >
              <span class="persona-icon">{{ item.icon }}</span>
              <strong>{{ item.label }}</strong>
              <small>{{ item.desc }}</small>
            </button>
          </div>
        </section>

        <section class="card rise">
          <h3>你更喜欢的社交方式</h3>
          <div class="chip-row mt-12">
            <button
              v-for="item in SOCIAL_PREFS"
              :key="item.value"
              type="button"
              class="chip mint"
              :class="{ active: socialPref === item.value }"
              @click="socialPref = item.value"
            >
              {{ item.label }}
            </button>
          </div>
        </section>

        <button class="btn btn-primary btn-block mt-20" :disabled="saving" type="button" @click="save">
          {{ saving ? "保存中…" : "保存画像" }}
        </button>
      </template>
    </div>
  </div>
</template>

<style scoped>
.count {
  font-size: 12px;
  color: var(--brand);
  background: var(--brand-soft);
  padding: 5px 10px;
  border-radius: 999px;
  font-weight: 600;
}

.intro h1 {
  font-size: 25px;
  font-weight: 700;
  letter-spacing: -0.4px;
}

.intro .sub {
  margin-top: 6px;
  font-size: 13px;
  color: var(--muted);
}

.group h3,
.card h3 {
  font-size: 14px;
  font-weight: 700;
}

.persona-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.persona {
  border: 1px solid var(--line);
  background: #fafbfc;
  border-radius: 16px;
  padding: 12px 8px;
  display: grid;
  gap: 4px;
  justify-items: center;
  cursor: pointer;
  transition: border 0.18s ease, background 0.18s ease;
}

.persona-icon {
  font-size: 20px;
}

.persona strong {
  font-size: 13px;
  color: var(--ink);
}

.persona small {
  font-size: 10px;
  color: var(--muted);
  line-height: 1.4;
  text-align: center;
}

.persona.active {
  border-color: rgba(61, 123, 255, 0.4);
  background: var(--brand-soft);
}
</style>