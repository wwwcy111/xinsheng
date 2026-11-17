import http from "./http";
import type { Tag, TokenResult, User } from "../types";

export interface RegisterPayload {
  nickname: string;
  student_no_tail4: string;
  password: string;
  tag_ids: number[];
  personality: "introvert" | "neutral" | "extrovert";
  social_pref?: "one_to_one" | "small_group" | "random";
  college?: string;
  major?: string;
  contact?: string;
  bio?: string;
}

export interface LoginPayload {
  nickname: string;
  password: string;
}

export function register(payload: RegisterPayload) {
  return http.post<any, TokenResult>("/auth/register", payload);
}

export function login(payload: LoginPayload) {
  return http.post<any, TokenResult>("/auth/login", payload);
}

export function fetchMe() {
  return http.get<any, User>("/users/me");
}

export function updateProfile(payload: Partial<RegisterPayload>) {
  return http.put<any, User>("/users/me/profile", payload);
}

export function fetchTags() {
  return http.get<any, Tag[]>("/tags");
}