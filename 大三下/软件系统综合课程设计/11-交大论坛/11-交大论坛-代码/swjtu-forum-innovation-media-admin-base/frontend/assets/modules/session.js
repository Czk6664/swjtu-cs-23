// Local session source of truth: token/user/draft state backed by localStorage.
import { STORAGE_KEYS } from "./constants.js";

// In the browser this is always the real Web Storage. Under non-DOM test
// runners (no `localStorage` global) it degrades to a no-op so the rendering
// primitives can be imported in isolation; browser behavior is unchanged.
const storage = typeof localStorage !== "undefined"
  ? localStorage
  : { getItem: () => null, setItem: () => {}, removeItem: () => {} };

export function safeJson(value) {
  try {
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}

export const state = {
  token: storage.getItem(STORAGE_KEYS.token) || "",
  user: safeJson(storage.getItem(STORAGE_KEYS.user)),
  draft: safeJson(storage.getItem(STORAGE_KEYS.draft)) || {}
};

export function persistSession(result) {
  state.token = result.token || "";
  state.user = result.user || null;
  storage.setItem(STORAGE_KEYS.token, state.token);
  storage.setItem(STORAGE_KEYS.user, JSON.stringify(state.user));
}

export function clearSession() {
  state.token = "";
  state.user = null;
  storage.removeItem(STORAGE_KEYS.token);
  storage.removeItem(STORAGE_KEYS.user);
}
