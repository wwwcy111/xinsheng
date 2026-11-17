import http from "./http";
import type { Note, PageResult } from "../types";

// 上传笔记：multipart，支持 jpg/png/webp/pdf
export function uploadNote(file: File) {
  const form = new FormData();
  form.append("file", file);
  return http.post<any, Note>("/study/notes", form);
}

// 演示用：写入 OCR 文本，跳过真实 OCR
export function saveOcrText(noteId: number, text: string) {
  return http.post<any, Note>(`/study/notes/${noteId}/ocr-text`, { text });
}

// 触发解析：生成导图、摘要、练习题
export function parseNote(noteId: number) {
  return http.post<any, Note>(`/study/notes/${noteId}/parse`);
}

export function fetchNoteStatus(noteId: number) {
  return http.get<any, { note_id: number; status: string; progress: number; error_message?: string | null }>(
    `/study/notes/${noteId}/status`,
  );
}

export function fetchNotes(page = 1, pageSize = 10) {
  return http.get<any, PageResult<Note>>("/study/notes", {
    params: { page, page_size: pageSize },
  });
}