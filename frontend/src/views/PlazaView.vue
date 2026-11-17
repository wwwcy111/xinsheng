<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";

import {
  createActivity,
  createItem,
  createLostFound,
  fetchActivities,
  fetchItems,
  fetchLostFound,
  signupActivity,
} from "../api/life";
import AppShell from "../components/AppShell.vue";
import { useToast } from "../composables/useToast";
import type { Activity, LostFound, SecondhandItem } from "../types";

type TabKey = "market" | "lost" | "activity";

const tab = ref<TabKey>("market");
const loading = ref(false);
const formOpen = ref(false);
const submitting = ref(false);
const { show } = useToast();

const marketItems = ref<SecondhandItem[]>([]);
const lostItems = ref<LostFound[]>([]);
const activityItems = ref<Activity[]>([]);

const TABS: { key: TabKey; label: string; icon: string }[] = [
  { key: "market", label: "二手闲置", icon: "🛍️" },
  { key: "lost", label: "失物招领", icon: "🔎" },
  { key: "activity", label: "社团活动", icon: "🎉" },
];

const CONDITION_LABEL: Record<string, string> = {
  new: "全新",
  nine: "九成新",
  seven: "七成新",
  usable: "可用",
};

const ACTIVITY_TYPE_LABEL: Record<string, string> = {
  lecture: "讲座",
  club_recruit: "社团招新",
  sports: "文体活动",
  other: "其他",
};

const marketForm = reactive({
  title: "",
  price: 0,
  original_price: 0,
  condition_level: "nine",
  category: "textbook",
  trade_place: "",
  description: "",
});

const lostForm = reactive({
  type: "lost" as "lost" | "found",
  title: "",
  item_desc: "",
  category: "other",
  event_place: "",
  contact: "",
});

const activityForm = reactive({
  title: "",
  type: "lecture",
  host: "",
  start_time: "",
  end_time: "",
  place: "",
  quota: 20,
});

onMounted(loadTab);
watch(tab, loadTab);

async function loadTab() {
  loading.value = true;
  try {
    if (tab.value === "market") {
      marketItems.value = (await fetchItems({ page: 1, page_size: 20 })).items;
    } else if (tab.value === "lost") {
      lostItems.value = (await fetchLostFound({ status: "ongoing", page: 1, page_size: 20 })).items;
    } else {
      activityItems.value = (await fetchActivities({ page: 1, page_size: 20 })).items;
    }
  } finally {
    loading.value = false;
  }
}

function openForm() {
  formOpen.value = true;
}

function closeForm() {
  formOpen.value = false;
}

async function submitForm() {
  submitting.value = true;
  try {
    if (tab.value === "market") {
      if (!marketForm.title || !marketForm.trade_place) {
        show("请填写商品标题与交易地点");
        return;
      }
      await createItem({
        title: marketForm.title,
        description: marketForm.description || undefined,
        price: Number(marketForm.price) || 0,
        original_price: marketForm.original_price ? Number(marketForm.original_price) : null,
        condition_level: marketForm.condition_level,
        category: marketForm.category,
        trade_place: marketForm.trade_place,
        image_urls: [],
      });
      show("商品已发布");
    } else if (tab.value === "lost") {
      if (!lostForm.title || !lostForm.item_desc || !lostForm.event_place || !lostForm.contact) {
        show("请把信息填写完整");
        return;
      }
      await createLostFound({
        type: lostForm.type,
        title: lostForm.title,
        item_desc: lostForm.item_desc,
        category: lostForm.category,
        event_place: lostForm.event_place,
        contact: lostForm.contact,
        images: [],
      });
      show("信息已发布");
    } else {
      if (!activityForm.title || !activityForm.host || !activityForm.place) {
        show("请把活动信息填写完整");
        return;
      }
      if (!activityForm.start_time || !activityForm.end_time) {
        show("请选择开始与结束时间");
        return;
      }
      await createActivity({
        title: activityForm.title,
        type: activityForm.type,
        host: activityForm.host,
        place: activityForm.place,
        start_time: activityForm.start_time,
        end_time: activityForm.end_time,
        quota: Number(activityForm.quota) || 1,
      });
      show("活动已创建");
    }
    closeForm();
    await loadTab();
  } finally {
    submitting.value = false;
  }
}

async function joinActivity(activity: Activity) {
  await signupActivity(activity.id);
  show("报名成功");
  await loadTab();
}

function formatTime(value: string) {
  const date = new Date(value);
  return `${date.getMonth() + 1}月${date.getDate()}日 ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}
</script>

<template>
  <AppShell>
    <div class="page">
      <div class="hero rise">
        <span class="eyebrow">校园生活百宝箱</span>
        <h1>把闲置、失物和活动，<br />都装进一个广场。</h1>
      </div>

      <div class="tabs rise-1">
        <button
          v-for="item in TABS"
          :key="item.key"
          type="button"
          :class="{ active: tab === item.key }"
          @click="tab = item.key"
        >
          <span>{{ item.icon }}</span>{{ item.label }}
        </button>
      </div>

      <div v-if="loading" class="empty">正在加载…</div>

      <template v-else>
        <!-- 二手 -->
        <div v-if="tab === 'market'" class="list">
          <div v-if="!marketItems.length" class="empty">
            <span class="empty-icon">📦</span>还没有闲置，发布第一件吧
          </div>
          <article v-for="item in marketItems" :key="item.id" class="card item-card rise">
            <div class="between">
              <h3>{{ item.title }}</h3>
              <span class="price">¥{{ item.price }}</span>
            </div>
            <p v-if="item.description" class="desc">{{ item.description }}</p>
            <div class="meta">
              <span class="mini-tag">{{ CONDITION_LABEL[item.condition_level] || item.condition_level }}</span>
              <span class="mini-tag">{{ item.trade_place }}</span>
              <span class="mini-tag">{{ item.view_count }} 次浏览</span>
            </div>
          </article>
        </div>

        <!-- 失物招领 -->
        <div v-if="tab === 'lost'" class="list">
          <div v-if="!lostItems.length" class="empty">
            <span class="empty-icon">🔎</span>暂时没有进行中的失物招领
          </div>
          <article v-for="item in lostItems" :key="item.id" class="card item-card rise">
            <div class="between">
              <h3>
                <span class="type-dot" :class="item.type" />
                {{ item.title }}
              </h3>
              <span class="mini-tag">{{ item.type === "lost" ? "失物" : "招领" }}</span>
            </div>
            <p class="desc">{{ item.item_desc }}</p>
            <div class="meta">
              <span class="mini-tag">{{ item.event_place }}</span>
              <span class="mini-tag">{{ item.contact }}</span>
            </div>
          </article>
        </div>

        <!-- 活动 -->
        <div v-if="tab === 'activity'" class="list">
          <div v-if="!activityItems.length" class="empty">
            <span class="empty-icon">🎉</span>还没有活动，创建第一场吧
          </div>
          <article v-for="item in activityItems" :key="item.id" class="card item-card rise">
            <div class="between">
              <h3>{{ item.title }}</h3>
              <span class="mini-tag">{{ ACTIVITY_TYPE_LABEL[item.type] || item.type }}</span>
            </div>
            <p class="desc">{{ item.host }} · {{ item.place }}</p>
            <div class="meta">
              <span class="mini-tag">{{ formatTime(item.start_time) }}</span>
              <span class="mini-tag">剩余 {{ item.remaining }} 个名额</span>
            </div>
            <button
              class="btn btn-primary btn-sm mt-12"
              type="button"
              :disabled="item.remaining <= 0"
              @click="joinActivity(item)"
            >
              {{ item.remaining > 0 ? "立即报名" : "名额已满" }}
            </button>
          </article>
        </div>
      </template>

      <button class="fab" type="button" @click="openForm">＋ 发布</button>
    </div>

    <!-- 发布表单 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="formOpen" class="sheet-mask" @click.self="closeForm">
          <div class="sheet">
            <div class="sheet-head">
              <h3>{{ tab === "market" ? "发布闲置" : tab === "lost" ? "发布失物 / 招领" : "创建活动" }}</h3>
              <button type="button" @click="closeForm">✕</button>
            </div>

            <div class="sheet-body">
              <template v-if="tab === 'market'">
                <div class="field"><label>商品标题</label><input v-model="marketForm.title" class="input" maxlength="50" /></div>
                <div class="field-row">
                  <div class="field"><label>售价（元）</label><input v-model.number="marketForm.price" class="input" type="number" min="0" /></div>
                  <div class="field"><label>原价（可选）</label><input v-model.number="marketForm.original_price" class="input" type="number" min="0" /></div>
                </div>
                <div class="field">
                  <label>成色</label>
                  <select v-model="marketForm.condition_level" class="input">
                    <option value="new">全新</option>
                    <option value="nine">九成新</option>
                    <option value="seven">七成新</option>
                    <option value="usable">可用</option>
                  </select>
                </div>
                <div class="field"><label>交易地点</label><input v-model="marketForm.trade_place" class="input" maxlength="100" placeholder="比如：一食堂门口" /></div>
                <div class="field"><label>描述（可选）</label><textarea v-model="marketForm.description" class="input" maxlength="500" /></div>
              </template>

              <template v-if="tab === 'lost'">
                <div class="field">
                  <label>类型</label>
                  <div class="chip-row">
                    <button class="chip" :class="{ active: lostForm.type === 'lost' }" type="button" @click="lostForm.type = 'lost'">我丢了东西</button>
                    <button class="chip mint" :class="{ active: lostForm.type === 'found' }" type="button" @click="lostForm.type = 'found'">我捡到东西</button>
                  </div>
                </div>
                <div class="field"><label>标题</label><input v-model="lostForm.title" class="input" maxlength="50" placeholder="比如：丢失一张校园卡" /></div>
                <div class="field"><label>物品描述</label><textarea v-model="lostForm.item_desc" class="input" maxlength="500" /></div>
                <div class="field"><label>地点</label><input v-model="lostForm.event_place" class="input" maxlength="100" /></div>
                <div class="field"><label>联系方式</label><input v-model="lostForm.contact" class="input" maxlength="50" /></div>
              </template>

              <template v-if="tab === 'activity'">
                <div class="field"><label>活动标题</label><input v-model="activityForm.title" class="input" maxlength="100" /></div>
                <div class="field"><label>主办方</label><input v-model="activityForm.host" class="input" maxlength="100" placeholder="社团或学院名称" /></div>
                <div class="field-row">
                  <div class="field"><label>开始时间</label><input v-model="activityForm.start_time" class="input" type="datetime-local" /></div>
                  <div class="field"><label>结束时间</label><input v-model="activityForm.end_time" class="input" type="datetime-local" /></div>
                </div>
                <div class="field"><label>地点</label><input v-model="activityForm.place" class="input" maxlength="100" /></div>
                <div class="field"><label>名额</label><input v-model.number="activityForm.quota" class="input" type="number" min="1" /></div>
              </template>
            </div>

            <div class="sheet-foot">
              <button class="btn btn-primary btn-block" :disabled="submitting" type="button" @click="submitForm">
                {{ submitting ? "发布中…" : "确认发布" }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </AppShell>
</template>

<style scoped>
.hero h1 {
  margin-top: 10px;
  font-size: 24px;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: -0.4px;
}

.tabs {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  background: #f2f4f7;
  padding: 4px;
  border-radius: 15px;
}

.tabs button {
  border: none;
  background: transparent;
  border-radius: 11px;
  padding: 9px 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: background 0.2s ease, color 0.2s ease;
}

.tabs button.active {
  background: #fff;
  color: var(--ink);
  box-shadow: 0 2px 8px rgba(29, 29, 31, 0.08);
}

.list {
  margin-top: 14px;
  display: grid;
  gap: 12px;
}

.item-card {
  padding: 16px;
}

.item-card h3 {
  font-size: 15px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 6px;
}

.price {
  font-size: 16px;
  font-weight: 700;
  color: var(--coral);
  flex: none;
}

.desc {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.6;
  color: #4a4a4f;
}

.meta {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.mini-tag {
  font-size: 11px;
  color: #5b6474;
  background: #f2f4f7;
  padding: 3px 8px;
  border-radius: 999px;
}

.type-dot {
  width: 8px;
  height: 8px;
  border-radius: 3px;
}

.type-dot.lost { background: var(--coral); }
.type-dot.found { background: var(--mint); }

.fab {
  position: fixed;
  right: calc(50% - 232px);
  bottom: 104px;
  width: 52px;
  height: 52px;
  border-radius: 18px;
  border: none;
  background: linear-gradient(135deg, #4c8bff, #2ed3b7);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  box-shadow: 0 12px 26px rgba(61, 123, 255, 0.32);
  cursor: pointer;
  z-index: 40;
  display: grid;
  place-items: center;
}

@media (max-width: 560px) {
  .fab {
    right: 18px;
  }
}

.sheet-mask {
  position: fixed;
  inset: 0;
  background: rgba(29, 29, 31, 0.42);
  backdrop-filter: blur(3px);
  z-index: 80;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.sheet {
  width: min(520px, 100%);
  max-height: 86vh;
  background: #fff;
  border-radius: 24px 24px 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-bottom: 1px solid var(--line);
}

.sheet-head h3 {
  font-size: 16px;
  font-weight: 700;
}

.sheet-head button {
  border: none;
  background: #f2f4f7;
  width: 30px;
  height: 30px;
  border-radius: 10px;
  cursor: pointer;
  color: var(--muted);
}

.sheet-body {
  padding: 16px 18px;
  overflow-y: auto;
}

.sheet-foot {
  padding: 12px 18px calc(16px + env(safe-area-inset-bottom));
  border-top: 1px solid var(--line);
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.22s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>