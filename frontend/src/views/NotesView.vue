<script setup lang="ts">
import { onMounted, ref } from "vue";

import { fetchNotes, parseNote, saveOcrText, uploadNote } from "../api/study";
import AppShell from "../components/AppShell.vue";
import MindMapTree from "../components/MindMapTree.vue";
import { useToast } from "../composables/useToast";
import type { Note } from "../types";

const DEMO_TEXT = `第一章 函数与极限
1. 函数的概念：设 x 和 y 是两个变量，D 是实数集的子集。
2. 极限的定义：当 x 无限趋近于 x0 时，函数值无限趋近于 A。
3. 重要极限：lim(x→0) sinx/x = 1；lim(x→∞) (1+1/x)^x = e。
4. 连续的定义：函数在一点的极限等于该点函数值。
易错点：判断极限存在需要左右极限都存在且相等。
复习建议：先掌握定义，再练习夹逼准则与等价无穷小替换。`;

const note = ref<Note | null>(null);
const ocrText = ref(DEMO_TEXT);
const uploading = ref(false);
const parsing = ref(false);
const history = ref<Note[]>([]);
const { show } = useToast();

onMounted(loadHistory);

async function loadHistory() {
  try {
    const page = await fetchNotes(1, 5);
    history.value = page.items;
  } catch {
    history.value = [];
  }
}

async function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  uploading.value = true;
  try {
    note.value = await uploadNote(file);
    ocrText.value = DEMO_TEXT;
    show("上传成功，可以开始解析");
  } finally {
    uploading.value = false;
    input.value = "";
  }
}

async function parseCurrent() {
  if (!note.value) return;
  parsing.value = true;
  try {
    if (ocrText.value.trim()) {
      note.value = await saveOcrText(note.value.id, ocrText.value);
    }
    note.value = await parseNote(note.value.id);
    show("导图、摘要和练习题已生成");
    await loadHistory();
  } finally {
    parsing.value = false;
  }
}

function openHistory(item: Note) {
  note.value = item;
  ocrText.value = item.char_count ? "" : DEMO_TEXT;
}
</script>

<template>
  <AppShell>
    <div class="page">
      <div class="hero rise">
        <span class="eyebrow">AI 笔记助手</span>
        <h1>笔记拍下来，<br />变成能复习的样子。</h1>
        <p class="sub">OCR 识别后自动生成思维导图、知识点摘要与练习题</p>
      </div>

      <label class="upload-box rise-1" :class="{ busy: uploading }">
        <input type="file" accept=".jpg,.jpeg,.png,.webp,.pdf" hidden @change="onFileChange" />
        <span class="upload-icon">{{ uploading ? "⏳" : "📄" }}</span>
        <strong>{{ uploading ? "正在上传…" : "上传笔记图片或 PDF" }}</strong>
        <small>支持 jpg / png / webp / pdf，20MB 以内</small>
      </label>

      <section v-if="note && note.status !== 'completed'" class="card rise-2">
        <div class="between">
          <h3>识别文本</h3>
          <span class="file-name">{{ note.file_name }}</span>
        </div>
        <p class="muted text-xs mt-8">
          演示模式：可直接使用下方示例文本，跳过真实 OCR；也可替换为你自己的笔记内容。
        </p>
        <textarea v-model="ocrText" class="input mt-12" rows="7" placeholder="OCR 文本或手动粘贴的笔记内容" />
        <button class="btn btn-primary btn-block mt-12" :disabled="parsing" type="button" @click="parseCurrent">
          {{ parsing ? "AI 正在整理笔记…" : "生成导图 · 摘要 · 练习题" }}
        </button>
      </section>

      <section v-if="parsing" class="card rise">
        <div class="progress"><span /></div>
        <p class="muted text-xs mt-12">正在提取知识点、搭建导图并生成练习题…</p>
      </section>

      <template v-if="note?.status === 'completed'">
        <section class="card rise">
          <div class="between">
            <h3>思维导图</h3>
            <span class="mini-tag">{{ note.file_name }}</span>
          </div>
          <div class="mt-12">
            <MindMapTree v-if="note.mind_map" :node="note.mind_map" />
          </div>
        </section>

        <section class="card rise-1">
          <h3>知识点摘要</h3>
          <ol class="summary-list mt-12">
            <li v-for="(item, index) in note.summaries || []" :key="index">{{ item }}</li>
          </ol>
        </section>

        <section class="card rise-2">
          <h3>复习练习题</h3>
          <div class="exercise-list mt-12">
            <details v-for="(item, index) in note.exercises || []" :key="index" class="exercise">
              <summary>
                <span class="ex-index">{{ index + 1 }}</span>
                {{ item.question }}
              </summary>
              <div class="ex-body">
                <p><strong>答案：</strong>{{ item.answer }}</p>
                <p class="analysis"><strong>解析：</strong>{{ item.analysis }}</p>
              </div>
            </details>
          </div>
        </section>

        <button class="btn btn-ghost btn-block mt-16" type="button" @click="note = null">
          再传一份笔记
        </button>
      </template>

      <section v-if="history.length && note?.status !== 'completed'" class="card rise-3">
        <h3>我的笔记</h3>
        <div class="history mt-12">
          <button v-for="item in history" :key="item.id" class="history-item" type="button" @click="openHistory(item)">
            <span class="history-icon">{{ item.status === "completed" ? "✅" : "⏳" }}</span>
            <span class="history-name">{{ item.file_name }}</span>
            <span class="history-status">{{ item.status === "completed" ? "已完成" : "待解析" }}</span>
          </button>
        </div>
      </section>
    </div>
  </AppShell>
</template>

<style scoped>
.hero h1 {
  margin-top: 10px;
  font-size: 25px;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: -0.4px;
}

.hero .sub {
  margin-top: 6px;
  font-size: 13px;
  color: var(--muted);
}

.upload-box {
  margin-top: 16px;
  display: grid;
  justify-items: center;
  gap: 4px;
  padding: 26px 16px;
  border-radius: 20px;
  border: 1.5px dashed rgba(61, 123, 255, 0.35);
  background: linear-gradient(180deg, rgba(61, 123, 255, 0.05), rgba(46, 211, 183, 0.05));
  cursor: pointer;
  transition: border 0.2s ease, background 0.2s ease;
}

.upload-box strong {
  font-size: 15px;
}

.upload-box small {
  font-size: 11px;
  color: var(--muted);
}

.upload-icon {
  font-size: 30px;
}

.upload-box.busy {
  opacity: 0.7;
}

.card h3 {
  font-size: 14px;
  font-weight: 700;
}

.file-name,
.mini-tag {
  font-size: 11px;
  color: var(--muted);
  background: #f2f4f7;
  padding: 3px 8px;
  border-radius: 999px;
  max-width: 190px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress {
  height: 6px;
  border-radius: 999px;
  background: #eef1f5;
  overflow: hidden;
}

.progress span {
  display: block;
  width: 46%;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #4c8bff, #2ed3b7);
  animation: slide 1.2s ease-in-out infinite alternate;
}

@keyframes slide {
  from { transform: translateX(-20%); }
  to { transform: translateX(150%); }
}

.summary-list {
  padding-left: 18px;
  display: grid;
  gap: 8px;
  font-size: 13px;
  line-height: 1.6;
  color: #3a3a3d;
}

.exercise-list {
  display: grid;
  gap: 8px;
}

.exercise {
  border: 1px solid var(--line);
  border-radius: 13px;
  background: #fafbfc;
  overflow: hidden;
}

.exercise summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  list-style: none;
}

.exercise summary::-webkit-details-marker {
  display: none;
}

.ex-index {
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

.ex-body {
  padding: 0 12px 12px 40px;
  font-size: 12px;
  line-height: 1.7;
  color: #4a4a4f;
  display: grid;
  gap: 4px;
}

.analysis {
  color: var(--muted);
}

.history {
  display: grid;
  gap: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 13px;
  cursor: pointer;
  text-align: left;
}

.history-icon {
  flex: none;
}

.history-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-status {
  font-size: 11px;
  color: var(--muted);
  flex: none;
}
</style>