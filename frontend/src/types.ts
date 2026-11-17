// 与后端接口对应的类型定义

export interface Tag {
  id: number;
  tag_name: string;
  category: string;
  icon?: string | null;
}

export interface User {
  id: number;
  nickname: string;
  student_no_tail4: string;
  personality: "introvert" | "neutral" | "extrovert";
  social_pref: "one_to_one" | "small_group" | "random";
  college?: string | null;
  major?: string | null;
  class_name?: string | null;
  contact?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
  status: number;
  created_at: string;
  tags: Tag[];
  profile_complete: boolean;
}

export interface TokenResult {
  token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface MatchItem {
  match_id: number;
  target_user_id: number;
  nickname: string;
  score: number;
  common_tags: string[];
  reason: string;
  topics: string[];
}

export interface Recommendation {
  batch_date: string;
  items: MatchItem[];
}

export interface MindNode {
  title: string;
  children?: MindNode[];
}

export interface Exercise {
  question: string;
  answer: string;
  analysis: string;
}

export interface Note {
  id: number;
  file_name: string;
  file_url: string;
  file_type: string;
  file_size: number;
  status: "ocr_pending" | "generating" | "completed" | "failed";
  char_count: number;
  mind_map?: MindNode | null;
  summaries?: string[] | null;
  exercises?: Exercise[] | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface SecondhandItem {
  id: number;
  seller_id: number;
  title: string;
  description?: string | null;
  price: number;
  original_price?: number | null;
  condition_level: "new" | "nine" | "seven" | "usable";
  category: string;
  trade_place: string;
  image_urls?: string[] | null;
  status: "on_sale" | "intended" | "sold" | "off_shelf";
  view_count: number;
  created_at: string;
}

export interface LostFound {
  id: number;
  publisher_id: number;
  type: "lost" | "found";
  title: string;
  item_desc: string;
  category: string;
  event_time?: string | null;
  event_place: string;
  contact: string;
  images?: string[] | null;
  status: "ongoing" | "returned" | "closed";
  claim_count: number;
  created_at: string;
}

export interface Activity {
  id: number;
  title: string;
  type: "lecture" | "club_recruit" | "sports" | "other";
  host: string;
  cover_url?: string | null;
  description?: string | null;
  start_time: string;
  end_time: string;
  place: string;
  quota: number;
  remaining: number;
  signup_deadline?: string | null;
  status: string;
  created_at: string;
}