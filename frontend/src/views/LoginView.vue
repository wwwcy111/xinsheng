<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { login, register } from "../api/auth";
import { useToast } from "../composables/useToast";
import { useAuthStore } from "../stores/auth";

const mode = ref<"login" | "register">("register");
const loading = ref(false);

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const { show } = useToast();

const form = reactive({
  nickname: "",
  password: "",
  student_no_tail4: "",
  college: "",
  personality: "neutral" as "introvert" | "neutral" | "extrovert",
  social_pref: "random" as "one_to_one" | "small_group" | "random",
});

const PERSONALITIES = [
  { value: "introvert", label: "慢热内向", icon: "🌙" },
  { value: "neutral", label: "自在切换", icon: "🌤️" },
  { value: "extrovert", label: "外向主动", icon: "☀️" },
] as const;

async function submit() {
  if (!form.nickname.trim()) {
    show("先给自己起个昵称吧");
    return;
  }
  if (!form.password) {
    show("请填写口令");
    return;
  }
  if (mode.value === "register") {
    if (!/^\d{4}$/.test(form.student_no_tail4)) {
      show("学号后四位需为 4 位数字");
      return;
    }
    if (form.password.length < 6) {
      show("口令至少 6 位");
      return;
    }
  }

  loading.value = true;
  try {
    const result =
      mode.value === "register"
        ? await register({
            nickname: form.nickname.trim(),
            password: form.password,
            student_no_tail4: form.student_no_tail4,
            college: form.college || undefined,
            personality: form.personality,
            social_pref: form.social_pref,
            tag_ids: [],
          })
        : await login({ nickname: form.nickname.trim(), password: form.password });

    auth.setToken(result.token);
    auth.user = result.user;
    show(mode.value === "register" ? "注册成功，先选几个兴趣吧" : "欢迎回来");

    if (!result.user.profile_complete) {
      router.replace("/tags");
    } else {
      router.replace((route.query.redirect as string) || "/home");
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <div class="hero">
      <div class="brand-row">
        <span class="brand-mark">声</span>
        <span class="brand-name">新声</span>
      </div>
      <h1>大学第一站，<br />先找到一个同频的人。</h1>
      <p class="hero-sub">破冰交友 · 学霸互助 · 校园生活，一站搞定</p>
      <div class="hero-tags">
        <span>✨ AI 搭子匹配</span>
        <span>📝 笔记变导图</span>
        <span>🛍️ 闲置与活动</span>
      </div>
    </div>

    <div class="form-card rise">
      <div class="mode-switch">
        <button :class="{ active: mode === 'register' }" type="button" @click="mode = 'register'">
          注册
        </button>
        <button :class="{ active: mode === 'login' }" type="button" @click="mode = 'login'">
          登录
        </button>
      </div>

      <div class="field">
        <label>昵称</label>
        <input v-model="form.nickname" class="input" maxlength="20" placeholder="比如：爱吃食堂二楼的小林" />
      </div>

      <div v-if="mode === 'register'" class="field">
        <label>学号后四位</label>
        <input v-model="form.student_no_tail4" class="input" maxlength="4" inputmode="numeric" placeholder="仅用于校内身份标识" />
      </div>

      <div class="field">
        <label>口令</label>
        <input v-model="form.password" class="input" type="password" maxlength="32" placeholder="至少 6 位" />
      </div>

      <template v-if="mode === 'register'">
        <div class="field">
          <label>学院（可选）</label>
          <input v-model="form.college" class="input" maxlength="50" placeholder="比如：计算机学院" />
        </div>

        <div class="field">
          <label>你的性格</label>
          <div class="choice-row">
            <button
              v-for="item in PERSONALITIES"
              :key="item.value"
              type="button"
              class="choice"
              :class="{ active: form.personality === item.value }"
              @click="form.personality = item.value"
            >
              <span class="choice-icon">{{ item.icon }}</span>
              {{ item.label }}
            </button>
          </div>
        </div>
      </template>

      <button class="btn btn-primary btn-block mt-8" :disabled="loading" type="button" @click="submit">
        {{ loading ? "稍等一下…" : mode === "register" ? "创建我的新声账号" : "进入新声" }}
      </button>

      <p class="tip">注册即代表你愿意友善交流，平台不采集身份证等敏感信息。</p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  width: min(520px, 100%);
  min-height: 100vh;
  margin: 0 auto;
  background: var(--surface);
  box-shadow: 0 0 80px rgba(29, 29, 31, 0.1);
  padding-bottom: 40px;
}

.hero {
  padding: 36px 24px 30px;
  color: #fff;
  background:
    radial-gradient(circle at 82% 8%, rgba(255, 255, 255, 0.36), transparent 40%),
    linear-gradient(135deg, #4c8bff 0%, #2ed3b7 100%);
  border-radius: 0 0 32px 32px;
  position: relative;
  overflow: hidden;
}

.hero::after {
  content: "";
  position: absolute;
  right: -30px;
  bottom: -60px;
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
}

.brand-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.brand-row .brand-mark {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
  font-size: 15px;
}

.hero h1 {
  margin-top: 22px;
  font-size: 27px;
  line-height: 1.35;
  letter-spacing: -0.4px;
  font-weight: 700;
}

.hero-sub {
  margin-top: 10px;
  font-size: 13px;
  opacity: 0.86;
}

.hero-tags {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hero-tags span {
  font-size: 11px;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(6px);
}

.form-card {
  margin: -14px 16px 0;
  position: relative;
  background: #fff;
  border-radius: 26px;
  padding: 18px;
  box-shadow: 0 16px 44px rgba(29, 29, 31, 0.1);
}

.mode-switch {
  display: grid;
  grid-template-columns: 1fr 1fr;
  background: #f2f4f7;
  border-radius: 14px;
  padding: 4px;
  margin-bottom: 16px;
}

.mode-switch button {
  border: none;
  background: transparent;
  padding: 9px 0;
  border-radius: 11px;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
}

.mode-switch button.active {
  background: #fff;
  color: var(--ink);
  box-shadow: 0 2px 8px rgba(29, 29, 31, 0.08);
}

.choice-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.choice {
  border: 1px solid var(--line);
  background: #fafbfc;
  border-radius: 13px;
  padding: 10px 6px;
  font-size: 12px;
  color: #4a4a4f;
  cursor: pointer;
  display: grid;
  gap: 4px;
  justify-items: center;
  transition: border 0.18s ease, background 0.18s ease, color 0.18s ease;
}

.choice-icon {
  font-size: 17px;
}

.choice.active {
  border-color: rgba(61, 123, 255, 0.4);
  background: var(--brand-soft);
  color: var(--brand);
}

.tip {
  margin-top: 12px;
  font-size: 11px;
  color: var(--muted);
  line-height: 1.6;
  text-align: center;
}
</style>