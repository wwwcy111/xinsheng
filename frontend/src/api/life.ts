import http from "./http";
import type { Activity, LostFound, PageResult, SecondhandItem } from "../types";

// ------------------------- 二手闲置 -------------------------

export function fetchItems(params: { keyword?: string; category?: string; page?: number; page_size?: number } = {}) {
  return http.get<any, PageResult<SecondhandItem>>("/market/items", { params });
}

export function createItem(payload: {
  title: string;
  description?: string;
  price: number;
  original_price?: number | null;
  condition_level: string;
  category: string;
  trade_place: string;
  image_urls?: string[];
}) {
  return http.post<any, SecondhandItem>("/market/items", payload);
}

// ------------------------- 失物招领 -------------------------

export function fetchLostFound(params: { type?: string; status?: string; page?: number; page_size?: number } = {}) {
  return http.get<any, PageResult<LostFound>>("/lostfound", { params });
}

export function createLostFound(payload: {
  type: "lost" | "found";
  title: string;
  item_desc: string;
  category: string;
  event_time?: string | null;
  event_place: string;
  contact: string;
  images?: string[];
}) {
  return http.post<any, LostFound>("/lostfound", payload);
}

// ------------------------- 活动 -------------------------

export function fetchActivities(params: { type?: string; page?: number; page_size?: number } = {}) {
  return http.get<any, PageResult<Activity>>("/activities", { params });
}

export function createActivity(payload: {
  title: string;
  type: string;
  host: string;
  description?: string;
  start_time: string;
  end_time: string;
  place: string;
  quota: number;
}) {
  return http.post<any, Activity>("/activities", payload);
}

export function signupActivity(activityId: number) {
  return http.post<any, { activity_id: number; status: string; remaining: number }>(
    `/activities/${activityId}/signup`,
  );
}