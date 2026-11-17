import { reactive } from "vue";

// 全局轻提示（单例），任意页面调用 useToast().show(...)
const state = reactive({
  visible: false,
  message: "",
  timer: 0,
});

export function useToast() {
  function show(message: string, duration = 2200) {
    state.message = message;
    state.visible = true;
    window.clearTimeout(state.timer);
    state.timer = window.setTimeout(() => {
      state.visible = false;
    }, duration);
  }

  return { toast: state, show };
}