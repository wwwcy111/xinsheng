import http from "./http";
import type { Recommendation } from "../types";

export function fetchRecommendations() {
  return http.get<any, Recommendation>("/match/recommendations");
}

export function refreshRecommendations() {
  return http.post<any, Recommendation>("/match/recommendations/refresh");
}

export function sendGreeting(targetUserId: number, message: string) {
  return http.post<any, { target_user_id: number; status: string }>("/match/greetings", {
    target_user_id: targetUserId,
    message,
  });
}