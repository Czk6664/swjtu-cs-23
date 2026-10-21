// Shared admin workspace layout: keeps the backend sidebar consistent across admin pages.
import { ROUTES } from "./constants.js";
import { state } from "./session.js";
import { escapeHtml } from "./ui.js";

const LINKS = [
  { id: "overview", href: ROUTES.admin, label: "\u603b\u89c8", index: "01" },
  { id: "moderation", href: ROUTES.moderation, label: "\u5185\u5bb9\u6cbb\u7406", index: "02" },
  { id: "users", href: ROUTES.users, label: "\u7528\u6237\u7ba1\u7406", index: "03" },
  { id: "recommendation", href: ROUTES.recommendation, label: "\u63a8\u8350\u7b56\u7565", index: "04" },
  { id: "rewards", href: ROUTES.adminRewards, label: "\u79ef\u5206\u5956\u52b1", index: "05" }
];

export function adminSidebar(active = "overview") {
  return `
    <aside class="admin-dense-sidebar" aria-label="\u7ba1\u7406\u540e\u53f0\u5bfc\u822a">
      <div class="admin-dense-sidebar__head">
        <span class="admin-dense-sidebar__mark">SW</span>
        <div>
          <strong>\u540e\u53f0\u63a7\u5236\u53f0</strong>
          <small>${escapeHtml(state.user?.username || "admin")}</small>
        </div>
      </div>
      <nav class="admin-dense-nav">
        ${LINKS.map((link) => `
          <a class="${link.id === active ? "is-active" : ""}" href="${link.href}" data-admin-route="${link.id}">
            <span>${link.index}</span>
            <strong>${link.label}</strong>
          </a>
        `).join("")}
      </nav>
      <a class="admin-dense-back" href="${ROUTES.admin}" data-admin-route="overview">\u8fd4\u56de\u7ba1\u7406\u603b\u89c8</a>
      <a class="admin-dense-back admin-dense-back--muted" href="${ROUTES.home}">\u8fd4\u56de\u8bba\u575b\u9996\u9875</a>
      <div class="admin-dense-sidebar__note">
        <span class="admin-status-dot"></span>
        <strong>\u6743\u9650\u72b6\u6001</strong>
        <small>${escapeHtml(state.user?.role || "ADMIN")}</small>
      </div>
    </aside>
  `;
}

export function adminShell(content, active = "overview") {
  injectAdminLayoutCss();
  document.body.classList.add("admin-dense-body");
  return `
    <div class="admin-dense-shell">
      ${adminSidebar(active)}
      <main class="admin-dense-main">
        ${content}
      </main>
    </div>
  `;
}

export function adminPageShell(active, label, title, intro, body, aside = "", actions = "") {
  return adminShell(`
    <header class="admin-subpage-head">
      <div>
        ${label ? `<span class="admin-subpage-head__kicker">${escapeHtml(label)}</span>` : ""}
        <h1>${escapeHtml(title)}</h1>
        ${intro ? `<p>${escapeHtml(intro)}</p>` : ""}
      </div>
      <div class="admin-subpage-head__actions">
        <a class="admin-subpage-head__back" href="${ROUTES.admin}">\u7ba1\u7406\u603b\u89c8</a>
        ${actions || ""}
      </div>
    </header>
    ${body}
    ${aside}
  `, active);
}

export function injectAdminLayoutCss() {
  if (document.querySelector("[data-admin-layout-style]")) {
    return;
  }
  const style = document.createElement("style");
  style.dataset.adminLayoutStyle = "true";
  style.textContent = `
    body.admin-dense-body { background: #f5f9fc; }
    .admin-dense-shell { display: grid; grid-template-columns: 236px minmax(0, 1fr); min-height: calc(100vh - 74px); border-top: 1px solid var(--border); background: #f5f9fc; }
    .admin-dense-sidebar { position: sticky; top: 74px; align-self: start; height: calc(100vh - 74px); padding: 18px 14px; border-right: 1px solid #d8e8f3; background: linear-gradient(180deg, #ffffff, #eef6fb); overflow: auto; }
    .admin-dense-sidebar__head { display: flex; align-items: center; gap: 10px; padding: 8px 8px 16px; border-bottom: 1px solid #d8e8f3; }
    .admin-dense-sidebar__mark { width: 36px; height: 36px; display: grid; place-items: center; border-radius: 12px; background: var(--brand); color: #fff; font-weight: 800; font-size: 13px; box-shadow: 0 4px 10px rgba(0,117,184,.18); }
    .admin-dense-sidebar__head strong, .admin-dense-sidebar__note strong { display: block; color: #162636; font-size: 14px; }
    .admin-dense-sidebar__head small, .admin-dense-sidebar__note small { display: block; color: #6b7a8c; font-size: 12px; margin-top: 2px; }
    .admin-dense-nav { display: grid; gap: 5px; padding: 14px 0 10px; }
    .admin-dense-nav a { display: grid; grid-template-columns: 32px 1fr; align-items: center; gap: 8px; min-height: 40px; padding: 0 10px; border-radius: 10px; color: #3d5168; transition: background-color .16s ease, color .16s ease, transform .16s ease; }
    .admin-dense-nav a:hover { background: rgba(0,117,184,.08); color: var(--brand); transform: translateX(1px); }
    .admin-dense-nav a.is-active { background: var(--brand); color: #fff; }
    .admin-dense-nav span { font-family: var(--font-mono); font-size: 11px; opacity: .72; }
    .admin-dense-nav strong { font-size: 14px; font-weight: 700; }
    .admin-dense-back { display: block; margin: 5px 0; padding: 9px 10px; border: 1px solid #c8ddeb; border-radius: 10px; background: #fff; color: var(--brand); font-size: 13px; font-weight: 800; text-align: center; }
    .admin-dense-back--muted { color: #3d5168; background: #f8fbfd; }
    .admin-dense-sidebar__note { display: grid; grid-template-columns: 10px 1fr; gap: 9px; align-items: start; margin-top: 12px; padding: 12px; border-radius: 12px; border: 1px solid #d8e8f3; background: #fff; }
    .admin-status-dot { width: 9px; height: 9px; margin-top: 4px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 4px rgba(34,197,94,.12); }
    .admin-status-dot.is-warning { background: #f59e0b; box-shadow: 0 0 0 4px rgba(245,158,11,.14); }
    .admin-dense-main { min-width: 0; padding: 18px 20px 28px; }
    .admin-subpage-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; margin-bottom: 14px; padding: 14px 16px; border: 1px solid #d8e8f3; border-radius: 14px; background: #fff; }
    .admin-subpage-head__kicker { display: inline-flex; margin-bottom: 6px; color: var(--brand); font-weight: 800; font-size: 13px; }
    .admin-subpage-head h1 { margin: 0; color: #162636; font-size: 26px; line-height: 1.2; letter-spacing: -.02em; }
    .admin-subpage-head p { margin: 7px 0 0; max-width: 720px; color: #3d5168; line-height: 1.55; }
    .admin-subpage-head__actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
    .admin-subpage-head__back { display: inline-flex; align-items: center; min-height: 34px; padding: 0 12px; border: 1px solid #b8d8eb; border-radius: 10px; background: #eef7fc; color: var(--brand); font-weight: 800; }
    .admin-dense-main .section { padding: 0; }
    .admin-dense-main .container { width: 100%; max-width: none; padding: 0; }
    @media (max-width: 1120px) {
      .admin-dense-shell { grid-template-columns: 72px minmax(0, 1fr); }
      .admin-dense-sidebar__head div, .admin-dense-sidebar__note, .admin-dense-nav strong, .admin-dense-back { display: none; }
      .admin-dense-nav a { grid-template-columns: 1fr; justify-items: center; }
    }
    @media (max-width: 760px) {
      .admin-dense-shell { display: block; }
      .admin-dense-sidebar { position: static; height: auto; display: flex; gap: 10px; overflow-x: auto; border-right: 0; border-bottom: 1px solid #d8e8f3; }
      .admin-dense-sidebar__head, .admin-dense-sidebar__note { display: none; }
      .admin-dense-nav { display: flex; padding: 0; }
      .admin-dense-nav a { min-width: 58px; }
      .admin-dense-main { padding: 14px 12px 22px; }
      .admin-subpage-head { display: grid; }
    }
    @media (prefers-reduced-motion: reduce) {
      .admin-dense-nav a { transition: none; }
    }
  `;
  document.head.appendChild(style);
}
