// Rendering primitives, DOM shell helpers, and shared card builders.
import { DATE_FORMATTER, ROUTES } from "./constants.js";
import { clearSession, state } from "./session.js";
import { injectNotificationCss, mountNotifications } from "./notifications.js";
import { applyChromeMotion, applyPageMotion } from "./motion.js";

const forumLogo = new URL("../generated/brand/swjtu-forum-logo-transparent.png", import.meta.url).href;

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function formValues(form) {
  const values = {};
  form?.querySelectorAll("input, textarea, select").forEach((field) => {
    if (!field.name || field.disabled) {
      return;
    }
    if (field.type === "checkbox") {
      values[field.name] = field.checked ? (field.value || "on") : "";
      return;
    }
    if (field.type === "radio" && !field.checked) {
      return;
    }
    values[field.name] = field.value ?? "";
  });
  return values;
}

export function formatDate(value) {
  if (!value) {
    return "暂无时间";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return DATE_FORMATTER.format(date);
}

export function main() {
  return document.querySelector("main");
}

export function setMain(html) {
  main().innerHTML = html;
  bindGlobalActions(main());
  applyPageMotion(main());
}

export function toast(message, type = "info") {
  let host = document.querySelector("[data-toast-host]");
  if (!host) {
    host = document.createElement("div");
    host.dataset.toastHost = "true";
    host.className = "stitch-toast-host";
    document.body.appendChild(host);
  }

  const text = String(message || "");
  const duplicate = Array.from(host.querySelectorAll(".stitch-toast"))
    .find((node) => node.dataset.message === text);
  if (duplicate) {
    duplicate.classList.remove("leaving");
    duplicate.dataset.leaving = "0";
    duplicate.classList.remove("show");
    requestAnimationFrame(() => requestAnimationFrame(() => duplicate.classList.add("show")));
    return;
  }

  while (host.children.length >= 2) {
    dismissToast(host.firstElementChild, 260);
  }

  const item = document.createElement("div");
  item.className = `stitch-toast ${type}`;
  item.dataset.message = text;
  const content = document.createElement("span");
  content.textContent = text;
  const close = document.createElement("button");
  close.type = "button";
  close.className = "stitch-toast__close";
  close.setAttribute("aria-label", "关闭提示");
  close.textContent = "×";
  item.append(content, close);
  host.appendChild(item);
  const dismiss = () => dismissToast(item, 320);
  close.addEventListener("click", dismiss);
  requestAnimationFrame(() => requestAnimationFrame(() => item.classList.add("show")));
  setTimeout(dismiss, type === "warning" ? 3000 : 2400);
}

function dismissToast(item, delay = 320) {
  if (!item || item.dataset.leaving === "1") {
    return;
  }
  item.dataset.leaving = "1";
  item.classList.remove("show");
  item.classList.add("leaving");
  setTimeout(() => item.remove(), delay);
}

export function injectRuntimeCss() {
  if (document.querySelector("[data-runtime-style]")) {
    return;
  }
  const style = document.createElement("style");
  style.dataset.runtimeStyle = "true";
  style.textContent = `
    .stitch-toast-host { position: fixed; top: 14px; right: 14px; z-index: 90; display: grid; gap: 8px; pointer-events: none; }
    .stitch-toast { pointer-events: auto; display: flex; align-items: flex-start; gap: 10px; min-width: 220px; max-width: min(340px, calc(100vw - 28px)); padding: 11px 12px 11px 14px; border-radius: 14px; color: #fff; font-weight: 600; line-height: 1.45; box-shadow: 0 16px 34px rgba(20, 61, 92, 0.18); opacity: 0; transform: translate3d(18px, -8px, 0) scale(.96); filter: blur(2px); transition: opacity .32s ease, transform .32s cubic-bezier(.22,1,.36,1), filter .32s ease; background: var(--brand); will-change: opacity, transform, filter; }
    .stitch-toast__close { flex: 0 0 auto; width: 22px; height: 22px; border: none; border-radius: 999px; background: rgba(255,255,255,.18); color: inherit; cursor: pointer; font-size: 16px; line-height: 20px; }
    .stitch-toast__close:hover { background: rgba(255,255,255,.28); }
    .stitch-toast.success { background: var(--success); }
    .stitch-toast.warning { background: var(--warning); }
    .nav a.is-active-link { color: var(--brand) !important; }
    .stitch-toast.show { opacity: 1; transform: translate3d(0, 0, 0) scale(1); filter: blur(0); }
    .stitch-toast.leaving { opacity: 0; transform: translate3d(12px, -6px, 0) scale(.97); filter: blur(2px); pointer-events: none; }
    @media (max-width: 640px) {
      .stitch-toast-host { top: 10px; left: 10px; right: 10px; justify-items: stretch; }
      .stitch-toast { width: 100%; min-width: 0; max-width: none; transform: translate3d(0, -10px, 0) scale(.98); }
      .stitch-toast.leaving { transform: translate3d(0, -8px, 0) scale(.98); }
    }
    input.input, textarea.textarea, select.select { display: block; width: 100%; font: inherit; color: var(--ink); }
    input.input:focus, textarea.textarea:focus, select.select:focus { outline: none; border-color: var(--brand); box-shadow: 0 0 0 4px var(--brand-ring); }
    textarea.textarea { min-height: 180px; resize: vertical; }
    .live-empty { align-items: flex-start; }
    .button:disabled { opacity: .55; cursor: not-allowed; }
    .post-card__title a { color: inherit; text-decoration: none; }
    .quick-form { display: grid; gap: 14px; }
    .interest-tag-picker { display: flex; flex-wrap: wrap; gap: 9px; }
    .interest-tag-option { position: relative; display: inline-flex; align-items: center; cursor: pointer; }
    .interest-tag-option input { position: absolute; opacity: 0; pointer-events: none; }
    .interest-tag-option span { display: inline-flex; align-items: center; min-height: 34px; padding: 7px 12px; border-radius: 999px; border: 1px solid rgba(0, 117, 184, .18); background: rgba(0, 117, 184, .06); color: var(--brand); font-size: 13px; font-weight: 700; transition: transform .18s ease, box-shadow .18s ease, background .18s ease; }
    .interest-tag-option input:checked + span { background: var(--brand); color: #fff; box-shadow: 0 10px 22px rgba(0, 117, 184, .18); }
    .interest-tag-option:hover span { transform: translateY(-1px); }
    .status-pill { display: inline-flex; align-items: center; width: fit-content; padding: 6px 10px; border-radius: 999px; border: 1px solid var(--border-strong); color: var(--muted); font-size: 12px; font-weight: 600; }
    .status-pill--ok { color: var(--success); border-color: rgba(47, 158, 111, .28); background: rgba(47, 158, 111, .08); }
    .status-pill--warn { color: var(--warning); border-color: rgba(208, 132, 0, .3); background: rgba(208, 132, 0, .08); }
    .status-pill--danger { color: var(--danger); border-color: rgba(210, 71, 63, .28); background: rgba(210, 71, 63, .08); }
    .status-pill--solved { color: var(--brand); border-color: rgba(0, 117, 184, .28); background: rgba(0, 117, 184, .09); }
    .badge-chip-list { display: inline-flex; align-items: center; gap: 6px; flex-wrap: wrap; }
    .badge-chip { display: inline-flex; align-items: center; gap: 5px; padding: 5px 9px; border-radius: 999px; border: 1px solid rgba(0, 117, 184, .22); background: rgba(0, 117, 184, .08); color: var(--brand); font-size: 12px; font-weight: 700; }
    .badge-chip__icon { display: inline-grid; place-items: center; width: 18px; height: 18px; border-radius: 50%; background: rgba(255, 255, 255, .74); font-size: 11px; }
    .badge-chip__icon img { width: 18px; height: 18px; object-fit: contain; display: block; }
    .campus-badge-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 12px; margin-top: 12px; }
    .campus-badge-card { display: grid; grid-template-columns: auto 1fr; gap: 12px; align-items: center; padding: 14px; border-radius: var(--radius-md); border: 1px solid rgba(0, 117, 184, .18); background: linear-gradient(135deg, rgba(0, 117, 184, .08), rgba(255, 255, 255, .92)); box-shadow: 0 10px 28px rgba(0, 117, 184, .08); }
    .campus-badge-card__icon { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 16px; background: var(--brand); color: #fff; font-weight: 800; box-shadow: 0 10px 22px rgba(0, 117, 184, .2); }
    .campus-badge-card__icon img { width: 38px; height: 38px; object-fit: contain; display: block; }
    .campus-badge-card strong { display: block; color: var(--ink); }
    .campus-badge-card p { margin: 2px 0 4px; color: var(--muted); font-size: 12px; line-height: 1.5; }
    .campus-badge-card span { color: var(--ink-soft); font-size: 12px; }
    .badge-empty { margin-top: 12px; padding: 14px; border-radius: var(--radius-md); border: 1px dashed var(--border-strong); color: var(--muted); background: var(--surface-quiet); }
    .badge-empty--visual { display: grid; grid-template-columns: auto 1fr; gap: 12px; align-items: center; }
    .badge-empty--visual img { width: 74px; height: 74px; object-fit: contain; display: block; }
    .empty-state__emoji img { width: min(150px, 46vw); height: auto; object-fit: contain; display: block; margin: 0 auto 4px; filter: drop-shadow(0 10px 20px rgba(0, 117, 184, .08)); }
    .section-chips:has(.section-tile) { display: grid; grid-template-columns: repeat(auto-fit, minmax(112px, 1fr)); gap: 10px; }
    .section-tile { min-height: 92px; display: grid; place-items: center; gap: 6px; padding: 10px; border-radius: 18px; border: 1px solid rgba(0, 117, 184, .12); background: linear-gradient(180deg, rgba(255,255,255,.92), rgba(238,248,253,.78)); color: var(--ink); text-decoration: none; text-align: center; font-size: 13px; font-weight: 750; transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease; }
    .section-tile:hover { transform: translateY(-2px); border-color: rgba(0, 117, 184, .28); box-shadow: 0 12px 26px rgba(0, 117, 184, .1); }
    .section-tile img { width: 46px; height: 46px; object-fit: contain; display: block; }
    .swjtu-cloud-card { overflow: hidden; background: radial-gradient(circle at 16% 8%, rgba(0, 117, 184, .13), transparent 34%), linear-gradient(145deg, #ffffff 0%, #f6fbff 100%); }
    .heart-word-cloud { display: block; width: 100%; height: auto; margin-top: 6px; border-radius: 18px; background: radial-gradient(circle at 50% 44%, rgba(255,255,255,.96), rgba(236,248,254,.78) 72%, rgba(255,255,255,.94)); overflow: hidden; }
    .heart-word-cloud__shape { fill: rgba(0, 117, 184, .07); stroke: rgba(0, 117, 184, .18); stroke-width: 2.2; }
    .heart-word-cloud__link { text-decoration: none; }
    .heart-word-cloud__word { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-weight: 850; fill: #0075b8; paint-order: stroke; stroke: rgba(255,255,255,.82); stroke-width: 2.4px; stroke-linejoin: round; animation: wordFloatSvg 5.6s ease-in-out var(--delay) infinite alternate; }
    .heart-word-cloud__word--core { font-weight: 900; letter-spacing: -.03em; fill: #0075b8; stroke-width: 3.2px; filter: drop-shadow(0 6px 10px rgba(0, 117, 184, .12)); }
    .heart-word-cloud__word--hot { font-weight: 900; fill: #168f54; stroke-width: 3px; filter: drop-shadow(0 5px 9px rgba(22, 143, 84, .11)); }
    .heart-word-cloud__word--1 { fill: #0075b8; }
    .heart-word-cloud__word--2 { fill: #168f54; }
    .heart-word-cloud__word--3 { fill: #0a6aa1; }
    .heart-word-cloud__word--4 { fill: #6b8f00; }
    .heart-word-cloud__link:hover .heart-word-cloud__word { fill: var(--brand-deep); filter: drop-shadow(0 4px 8px rgba(0, 117, 184, .18)); }
    @keyframes wordFloatSvg { from { translate: 0 -.8px; } to { translate: 0 1.2px; } }
    @media (prefers-reduced-motion: reduce) { .heart-word-cloud__word { animation: none; } }
    .detail-author { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
    .detail-author__name { font-weight: 700; color: var(--ink); }
    .detail-author__followers { color: var(--muted); font-size: 13px; }
    .detail-badges { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .solved-prefix { display: inline-flex; align-items: center; margin-right: 6px; color: var(--brand); font-size: .82em; font-weight: 800; }
    .comment-card__meta { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
    .comment-card--accepted { border-color: rgba(0, 117, 184, .34); background: linear-gradient(135deg, rgba(0, 117, 184, .12), rgba(255, 255, 255, .92)); box-shadow: 0 16px 40px rgba(0, 117, 184, .12); }
    .comment-card__top { display: flex; justify-content: space-between; gap: 12px; align-items: center; flex-wrap: wrap; }
    .comment-reply-btn { border: none; background: none; color: var(--brand); font-weight: 600; font-size: 13px; cursor: pointer; padding: 2px 6px; border-radius: 8px; }
    .comment-reply-btn:hover { background: var(--brand-soft); }
    .comment-replies { margin-top: 10px; padding-left: 14px; border-left: 2px solid var(--border); display: grid; gap: 8px; }
    .comment-card--reply { background: var(--surface-quiet); border-radius: var(--radius-sm); padding: 8px 12px; }
    .comment-reply-form { margin-top: 10px; }
    .comment-reply-form .textarea { min-height: 70px; }
    .brand__mark { overflow: visible; background: transparent; box-shadow: none; }
    .brand__mark img { width: 100%; height: 100%; object-fit: contain; display: block; filter: drop-shadow(0 10px 16px rgba(0, 117, 184, 0.22)); }
  `;
  document.head.appendChild(style);
}

export function bindGlobalActions(root = document) {
  root.querySelectorAll("[data-logout]").forEach((button) => {
    button.addEventListener("click", () => {
      clearSession();
      toast("已退出登录", "success");
      location.href = ROUTES.home;
    });
  });
}

export function initials(name) {
  const text = String(name || "").trim();
  if (!text) {
    return "友";
  }
  // For CJK names take the first char; for latin take up to 2 leading letters.
  if (/[A-Za-z]/.test(text[0])) {
    return text.slice(0, 2).toUpperCase();
  }
  return text.slice(0, 1);
}

export function uploadUrl(value) {
  const raw = String(value || "").trim();
  if (!raw) {
    return "";
  }
  if (/^(https?:|data:|blob:)/i.test(raw)) {
    return raw;
  }
  if (raw.startsWith("/api/uploads/")) {
    return raw;
  }
  if (raw.startsWith("/uploads/")) {
    return `/api${raw}`;
  }
  return raw;
}

export function avatarUrl(value) {
  return uploadUrl(value);
}

export function avatarHtml(user, alt = "") {
  const src = avatarUrl(user?.avatar);
  if (src) {
    return `<img src="${escapeHtml(src)}" alt="${escapeHtml(alt)}" />`;
  }
  return escapeHtml(initials(user?.username || alt));
}

export function postImageUrls(post) {
  const rawImages = Array.isArray(post?.imageUrls) && post.imageUrls.length
    ? post.imageUrls
    : [post?.coverImage];
  return rawImages.map(uploadUrl).filter(Boolean).slice(0, 9);
}

export function userProfileHref(user) {
  return user?.id ? `${ROUTES.profile}?userId=${encodeURIComponent(user.id)}` : "";
}

// Render the shared product header into `.topbar` (creating it when missing),
// so every page gets a consistent app bar regardless of its static HTML.
export function mountChrome() {
  let bar = document.querySelector(".topbar");
  if (!bar) {
    bar = document.createElement("header");
    bar.className = "topbar";
    const shell = document.querySelector(".page-shell") || document.body;
    shell.insertBefore(bar, shell.firstChild);
  }

  const keyword = new URLSearchParams(location.search).get("keyword") || "";
  const navLinks = [
    { href: ROUTES.home, text: "首页" },
    { href: ROUTES.circles, text: "圈子" },
    { href: ROUTES.growth, text: "成长" },
    { href: ROUTES.rewards, text: "积分商城" }
  ];
  if (state.user?.role === "ADMIN") {
    navLinks.push({ href: ROUTES.admin, text: "管理后台" });
  }
  const nav = navLinks
    .map((item) => `<a href="${item.href}">${escapeHtml(item.text)}</a>`)
    .join("");

  const userArea = state.user
    ? `
      <a class="user-chip" href="${ROUTES.profile}" title="我的主页">
        <span class="avatar">${avatarHtml(state.user)}</span>
        <span>
          <span class="user-chip__name">${escapeHtml(state.user.username)}</span>
          <span class="user-chip__lv"> Lv.${escapeHtml(String(state.user.level || 1))}</span>
        </span>
      </a>
      <button class="icon-btn" data-logout title="退出登录">⎋</button>
    `
    : `<a class="button button--solid button--sm" href="${ROUTES.auth}">登录 / 注册</a>`;

  bar.innerHTML = `
    <div class="container">
      <div class="appbar">
        <a class="brand appbar__brand" href="${ROUTES.home}">
          <span class="brand__mark"><img src="${forumLogo}" alt="" /></span>
          <span class="brand__text">交大论坛</span>
        </a>
        <form class="appbar__search" data-chrome-search role="search">
          <input name="keyword" value="${escapeHtml(keyword)}" placeholder="搜索帖子、版块、话题" aria-label="搜索" />
        </form>
        <nav class="appbar__nav">${nav}</nav>
        <div class="appbar__actions">
          <a class="button button--ghost button--sm" href="${ROUTES.create}">＋ 发帖</a>
          ${userArea}
        </div>
      </div>
    </div>
  `;

  bar.querySelector("[data-chrome-search]")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const value = String(formValues(event.currentTarget).keyword || "").trim();
    location.href = value ? `${ROUTES.home}?keyword=${encodeURIComponent(value)}` : ROUTES.home;
  });
  bindGlobalActions(bar);

  // Notification bell lives in the actions cluster, but only for logged-in users.
  if (state.user) {
    injectNotificationCss();
    mountNotifications(bar.querySelector(".appbar__actions"));
  }
  applyChromeMotion(bar);
}

export function highlightNav() {
  const path = location.pathname.replace(/\\/g, "/");
  document.querySelectorAll("a[href]").forEach((link) => {
    const href = link.getAttribute("href") || "";
    if (href.startsWith("javascript:") || href.startsWith("http")) {
      return;
    }
    const resolved = new URL(href, location.href).pathname.replace(/\\/g, "/");
    link.classList.toggle("is-active-link", resolved === path);
  });
}

export function currentPath() {
  return `${location.pathname}${location.search}`;
}

export function loginHref(next = currentPath()) {
  return `${ROUTES.auth}?next=${encodeURIComponent(next)}`;
}

export function requireLogin() {
  if (state.token && state.user) {
    return true;
  }
  location.href = loginHref();
  return false;
}

export function requireAdmin() {
  if (state.user?.role === "ADMIN") {
    return true;
  }
  toast("后台功能仅管理员可访问，普通用户已返回论坛首页。", "warning");
  location.href = ROUTES.home;
  return false;
}

export function isAdminRoute(path = location.pathname) {
  return [
    ROUTES.admin,
    ROUTES.moderation,
    ROUTES.users,
    "/user_management/code.html",
    ROUTES.recommendation,
    "/recommendation_strategy/code.html",
    ROUTES.adminRewards
  ].some((route) => path.endsWith(route));
}

// Compact page header. `label` renders as a small kicker chip, `intro` as a lead.
// `actions` (optional HTML) sits on the right; defaults to none since the app bar
// already carries primary navigation.
export function pageShell(label, title, intro, body, aside = "", actions = "") {
  return `
    <header class="page-head">
      <div class="container page-head__inner">
        <div>
          ${label ? `<span class="page-head__kicker">${escapeHtml(label)}</span>` : ""}
          <h1 class="page-head__title">${escapeHtml(title)}</h1>
          ${intro ? `<p class="page-head__lead">${escapeHtml(intro)}</p>` : ""}
        </div>
        ${actions ? `<div class="page-head__actions">${actions}</div>` : ""}
      </div>
    </header>
    ${body}
    ${aside}
  `;
}

export function stateCard(title, message, actionLabel = "", href = "", marker = "i") {
  const markerHtml = String(marker).startsWith("<img ") ? marker : escapeHtml(marker);
  return `
    <section class="section">
      <div class="container">
        <article class="card empty-state">
          <div class="empty-state__emoji">${markerHtml}</div>
          <h2 class="empty-state__title">${escapeHtml(title)}</h2>
          <p class="empty-state__msg">${escapeHtml(message)}</p>
          ${href ? `<a class="button button--solid" href="${href}">${escapeHtml(actionLabel || "继续")}</a>` : ""}
        </article>
      </div>
    </section>
  `;
}

// Compatibility export for the runtime XSS test, which imports `buildStateCard`.
// The 4th argument is rendered as an href, matching the original `stateCard` contract.
export const buildStateCard = stateCard;

export function isOwnPost(post) {
  return Boolean(state.user?.id && post?.author?.id && state.user.id === post.author.id);
}

export function postStatusLabel(status) {
  return ({
    0: "待审核",
    1: "已发布",
    2: "已隐藏",
    3: "已驳回"
  })[Number(status)] || "未知状态";
}

export function postStatusClass(status) {
  if (Number(status) === 1) {
    return "status-pill status-pill--ok";
  }
  if (Number(status) === 0) {
    return "status-pill status-pill--warn";
  }
  return "status-pill status-pill--danger";
}

export function postCard(post) {
  const author = post.author?.username || "匿名用户";
  const authorHref = userProfileHref(post.author);
  const authorAvatar = authorHref
    ? `<a class="avatar avatar-link" href="${authorHref}" title="查看 ${escapeHtml(author)} 的主页">${avatarHtml(post.author, author)}</a>`
    : `<span class="avatar">${avatarHtml(post.author, author)}</span>`;
  const authorName = authorHref
    ? `<a class="post-card__author author-link" href="${authorHref}">${escapeHtml(author)}</a>`
    : `<span class="post-card__author">${escapeHtml(author)}</span>`;
  const solved = Boolean(post.acceptedCommentId);
  const tags = (post.tags || []).slice(0, 3)
    .map((tag) => `<span class="tag">#${escapeHtml(tag.name || tag)}</span>`)
    .join("");
  const pending = Number(post.status) !== 1
    ? `<span class="${postStatusClass(post.status)}">${postStatusLabel(post.status)}</span>`
    : "";
  const images = postImageUrls(post);
  const previewImages = images.slice(0, 3);
  const imageGridClass = previewImages.length === 1 ? "post-card__media--single" : "post-card__media--grid";
  const cover = "";
  const favorited = Boolean(post.favoritedByCurrentUser);
  return `
    <article class="card post-card">
      <div class="post-card__head">
        ${authorAvatar}
        <span class="post-card__byline">
          ${authorName}
          <span class="post-card__sub">${escapeHtml(post.section?.name || "校园论坛")} · ${formatDate(post.createdAt)}</span>
        </span>
        ${solved ? '<span class="status-pill status-pill--solved">已解决</span>' : ""}
        <span class="tag tag--brand">${escapeHtml(post.section?.name || "校园论坛")}</span>
      </div>
      <h3 class="post-card__title"><a href="${ROUTES.detail}?id=${post.id}">${solved ? '<span class="solved-prefix">[已解决]</span>' : ""}${escapeHtml(post.title)}</a></h3>
      <p class="post-card__excerpt">${escapeHtml((post.content || "").slice(0, 140))}</p>
      ${cover ? `<a class="post-card__media" href="${ROUTES.detail}?id=${post.id}" aria-label="查看帖子图片"><img src="${escapeHtml(cover)}" alt="" loading="lazy" /></a>` : ""}
      ${previewImages.length ? `<a class="post-card__media ${imageGridClass}" href="${ROUTES.detail}?id=${post.id}" aria-label="查看帖子图片">${previewImages.map((url, index) => `<span class="post-card__media-item"><img src="${escapeHtml(url)}" alt="" loading="lazy" />${index === 2 && images.length > 3 ? `<span class="post-card__media-more">+${images.length - 3}</span>` : ""}</span>`).join("")}</a>` : ""}
      ${tags ? `<div class="inline-tags">${tags}</div>` : ""}
      <div class="post-actions">
        <div class="post-stats">
          <span class="stat-chip"><span class="stat-chip__icon">浏览</span>${post.viewCount || 0}</span>
          <span class="stat-chip"><span class="stat-chip__icon">回复</span>${post.commentCount || 0}</span>
          <span class="stat-chip"><span class="stat-chip__icon">赞</span>${post.likeCount || 0}</span>
          <button class="stat-chip stat-chip--like ${favorited ? "is-active" : ""}" data-favorite="${post.id}" title="${favorited ? "取消收藏" : "收藏"}" aria-pressed="${favorited ? "true" : "false"}"><span class="stat-chip__icon">收藏</span><span class="stat-chip__count">${post.collectCount || 0}</span></button>
        </div>
        ${pending}
        ${isOwnPost(post) ? `<a class="button button--outline button--sm" href="${ROUTES.create}?edit=${post.id}">编辑</a>` : ""}
        <a class="button button--ghost button--sm" href="${ROUTES.detail}?id=${post.id}">阅读全文</a>
      </div>
    </article>
  `;
}

export function sectionTags(sections) {
  return sections.map((section) => `<a class="tag" href="${ROUTES.home}?sectionId=${section.id}">${escapeHtml(section.name)}</a>`).join("");
}
