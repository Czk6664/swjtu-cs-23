// Notification center: app-bar bell with unread badge + dropdown panel.
// Lightweight and accessible — list recent notifications, mark read (one/all),
// and navigate to the related post when targetType === "POST".
import { apiRequest, pageContent } from "./api.js";
import { ROUTES } from "./constants.js";
import { state } from "./session.js";
import { escapeHtml, toast } from "./ui.js";

// Relative "time ago" formatter tuned for the forum's zh-CN copy.
function relativeTime(value) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  const diffMs = Date.now() - date.getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) {
    return "刚刚";
  }
  if (minutes < 60) {
    return `${minutes} 分钟前`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} 小时前`;
  }
  const days = Math.floor(hours / 24);
  if (days < 30) {
    return `${days} 天前`;
  }
  return date.toLocaleDateString("zh-CN");
}

function notificationItem(item) {
  const unreadClass = item.isRead ? "" : " is-unread";
  const navAttrs = item.targetType === "POST" && item.targetId
    ? ` data-notif-target="${escapeHtml(String(item.targetId))}"`
    : "";
  return `
    <button type="button" class="notif-item${unreadClass}" role="menuitem" data-notif-id="${escapeHtml(String(item.id))}"${navAttrs}>
      <span class="notif-item__dot" aria-hidden="true"></span>
      <span class="notif-item__body">
        <span class="notif-item__title">${escapeHtml(item.title || "通知")}</span>
        ${item.content ? `<span class="notif-item__text">${escapeHtml(item.content)}</span>` : ""}
        <span class="notif-item__time">${escapeHtml(relativeTime(item.createdAt))}</span>
      </span>
    </button>
  `;
}

async function loadList(panel) {
  const body = panel.querySelector("[data-notif-list]");
  body.innerHTML = '<p class="notif-empty">加载中…</p>';
  try {
    const items = pageContent(await apiRequest("/notifications?page=0&size=20&unreadOnly=false"));
    body.innerHTML = items.length
      ? items.map(notificationItem).join("")
      : '<p class="notif-empty">暂无通知，安静得很。</p>';
  } catch (error) {
    body.innerHTML = `<p class="notif-empty">${escapeHtml(error.message || "加载失败")}</p>`;
  }
}

function setBadge(host, unread) {
  const badge = host.querySelector("[data-notif-badge]");
  if (!badge) {
    return;
  }
  const count = Number(unread) || 0;
  if (count > 0) {
    badge.textContent = count > 99 ? "99+" : String(count);
    badge.hidden = false;
  } else {
    badge.hidden = true;
  }
}

async function refreshUnread(host) {
  try {
    const data = await apiRequest("/notifications/unread-count");
    setBadge(host, data?.unread);
  } catch {
    // Badge stays at its current value on a transient failure.
  }
}

async function markRead(id) {
  await apiRequest(`/notifications/${id}/read`, { method: "PATCH" });
}

// Build and wire the bell + dropdown. Only invoked when a user is logged in.
export function mountNotifications(actionsHost) {
  if (!actionsHost || actionsHost.querySelector("[data-notif-root]")) {
    return;
  }

  const root = document.createElement("div");
  root.className = "notif-root";
  root.dataset.notifRoot = "true";
  root.innerHTML = `
    <button type="button" class="icon-btn notif-bell" data-notif-toggle aria-haspopup="true" aria-expanded="false" aria-label="通知中心" title="通知中心">
      通知
      <span class="notif-badge" data-notif-badge hidden></span>
    </button>
    <div class="notif-panel" data-notif-panel role="menu" aria-label="通知列表" hidden>
      <div class="notif-panel__head">
        <span class="notif-panel__title">通知</span>
        <button type="button" class="notif-readall" data-notif-readall>全部已读</button>
      </div>
      <div class="notif-panel__list" data-notif-list>
        <p class="notif-empty">加载中…</p>
      </div>
    </div>
  `;
  // Insert the bell before the user chip / login button for a natural reading order.
  actionsHost.insertBefore(root, actionsHost.firstChild);

  const toggle = root.querySelector("[data-notif-toggle]");
  const panel = root.querySelector("[data-notif-panel]");
  let idleCloseTimer = 0;

  function clearIdleClose() {
    if (idleCloseTimer) {
      window.clearTimeout(idleCloseTimer);
      idleCloseTimer = 0;
    }
  }

  function scheduleIdleClose() {
    clearIdleClose();
    idleCloseTimer = window.setTimeout(closePanel, 8000);
  }

  function closePanel() {
    clearIdleClose();
    panel.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
    document.removeEventListener("click", onOutsideClick);
    document.removeEventListener("keydown", onKeydown);
    window.removeEventListener("pagehide", closePanel);
  }

  function onOutsideClick(event) {
    if (!root.contains(event.target)) {
      closePanel();
    }
  }

  function onKeydown(event) {
    if (event.key === "Escape") {
      closePanel();
      toggle.focus();
    }
  }

  function openPanel() {
    panel.hidden = false;
    toggle.setAttribute("aria-expanded", "true");
    loadList(panel);
    document.addEventListener("click", onOutsideClick);
    document.addEventListener("keydown", onKeydown);
    window.addEventListener("pagehide", closePanel);
    scheduleIdleClose();
  }

  panel.addEventListener("pointerenter", clearIdleClose);
  panel.addEventListener("pointerleave", scheduleIdleClose);
  panel.addEventListener("focusin", clearIdleClose);
  panel.addEventListener("focusout", scheduleIdleClose);

  toggle.addEventListener("click", (event) => {
    event.stopPropagation();
    if (panel.hidden) {
      openPanel();
    } else {
      closePanel();
    }
  });

  root.querySelector("[data-notif-readall]").addEventListener("click", async (event) => {
    event.stopPropagation();
    try {
      await apiRequest("/notifications/read-all", { method: "PATCH" });
      panel.querySelectorAll(".notif-item.is-unread").forEach((node) => node.classList.remove("is-unread"));
      setBadge(root, 0);
      toast("已全部标记为已读", "success");
    } catch (error) {
      toast(error.message, "warning");
    }
  });

  panel.querySelector("[data-notif-list]").addEventListener("click", async (event) => {
    const item = event.target.closest("[data-notif-id]");
    if (!item) {
      return;
    }
    const { notifId, notifTarget } = item.dataset;
    if (item.classList.contains("is-unread")) {
      item.classList.remove("is-unread");
      try {
        await markRead(notifId);
        refreshUnread(root);
      } catch {
        // Best-effort: keep navigating even if marking fails.
      }
    }
    if (notifTarget) {
      closePanel();
      location.href = `${ROUTES.detail}?id=${encodeURIComponent(notifTarget)}`;
    }
  });

  refreshUnread(root);
}

export function injectNotificationCss() {
  if (!state.user || document.querySelector("[data-notif-style]")) {
    return;
  }
  const style = document.createElement("style");
  style.dataset.notifStyle = "true";
  style.textContent = `
    .notif-root { position: relative; display: inline-flex; }
    .notif-bell { position: relative; width: auto; min-width: 46px; padding: 0 10px; border-radius: var(--radius-pill); font-size: 13px; font-weight: 700; }
    .notif-badge { position: absolute; top: -4px; right: -4px; min-width: 18px; height: 18px; padding: 0 5px; border-radius: 999px; background: var(--brand); color: #fff; font-size: 11px; font-weight: 700; line-height: 18px; text-align: center; box-shadow: 0 2px 6px rgba(0, 117, 184, 0.34); }
    .notif-panel { position: absolute; top: calc(100% + 10px); right: 0; width: 340px; max-width: calc(100vw - 32px); max-height: min(520px, 62vh); overflow: hidden; flex-direction: column; background: var(--surface); border: 1px solid var(--border-strong); border-radius: var(--radius-md); box-shadow: 0 18px 44px rgba(20, 61, 92, .16); z-index: 70; }
    .notif-panel[hidden] { display: none !important; }
    .notif-panel:not([hidden]) { display: flex; }
    .notif-panel__head { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid var(--border); }
    .notif-panel__title { font-weight: 700; color: var(--ink); }
    .notif-readall { border: none; background: none; color: var(--brand); font-weight: 600; cursor: pointer; padding: 4px 6px; border-radius: 8px; }
    .notif-readall:hover { background: var(--brand-soft); }
    .notif-panel__list { overflow-y: auto; padding: 6px; display: grid; gap: 4px; }
    .notif-empty { padding: 22px 16px; text-align: center; color: var(--muted); margin: 0; }
    .notif-item { display: flex; gap: 10px; width: 100%; text-align: left; padding: 10px 12px; border: none; background: none; border-radius: var(--radius-sm); cursor: pointer; transition: background 0.16s ease; }
    .notif-item:hover { background: var(--surface-quiet); }
    .notif-item__dot { flex-shrink: 0; width: 8px; height: 8px; margin-top: 6px; border-radius: 50%; background: transparent; }
    .notif-item.is-unread { background: var(--brand-soft); }
    .notif-item.is-unread .notif-item__dot { background: var(--brand); }
    .notif-item__body { display: grid; gap: 3px; min-width: 0; }
    .notif-item__title { font-weight: 600; color: var(--ink); font-size: 14px; }
    .notif-item__text { color: var(--ink-soft); font-size: 13px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
    .notif-item__time { color: var(--muted); font-size: 12px; }
    @media (max-width: 640px) {
      .notif-root { position: static; }
      .notif-bell { min-width: 56px; }
      .notif-panel {
        position: fixed;
        top: 76px;
        left: 12px;
        right: 12px;
        width: auto;
        max-width: none;
        max-height: min(520px, calc(100vh - 96px));
        border-radius: 16px;
        z-index: 95;
      }
    }
  `;
  document.head.appendChild(style);
}
