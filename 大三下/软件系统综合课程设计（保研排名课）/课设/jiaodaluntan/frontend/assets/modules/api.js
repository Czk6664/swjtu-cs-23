// API runtime: one fetch wrapper, ApiResponse handling, auth header, timeout.
import { REQUEST_TIMEOUT_MS, STORAGE_KEYS } from "./constants.js";
import { clearSession, state } from "./session.js";

export async function apiRequest(path, options = {}) {
  const { method = "GET", body, auth = true, timeoutMs = REQUEST_TIMEOUT_MS } = options;
  const headers = new Headers(options.headers || {});
  if (body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  if (auth && state.token) {
    headers.set("Authorization", `Bearer ${state.token}`);
  }

  const controller = new AbortController();
  const timer = timeoutMs > 0 ? setTimeout(() => controller.abort(), timeoutMs) : null;
  let response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers,
      signal: controller.signal,
      body: body === undefined ? undefined : JSON.stringify(body)
    });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("请求超时，请检查后端服务是否正常运行");
    }
    throw error;
  } finally {
    if (timer) {
      clearTimeout(timer);
    }
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok || payload?.code !== 200) {
    if (response.status === 401) {
      clearSession();
    }
    const message = response.status === 403
      ? "权限不足：当前账号不能访问后台管理功能。普通用户可以继续进入论坛首页浏览、发帖和评论。"
      : payload?.message || `请求失败 (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return payload.data;
}

let sectionsCache = null;

export function fetchSections() {
  if (!sectionsCache) {
    sectionsCache = apiRequest("/sections", { auth: false }).catch((error) => {
      sectionsCache = null;
      throw error;
    });
  }
  return sectionsCache;
}

export function invalidateSectionsCache() {
  sectionsCache = null;
}

export async function restoreSession() {
  if (!state.token) {
    return;
  }
  try {
    state.user = await apiRequest("/auth/me");
    localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(state.user));
  } catch {
    clearSession();
  }
}

export function pageContent(items) {
  return (items || []).content || items || [];
}
