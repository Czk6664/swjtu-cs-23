// Growth center: check-in, points history, and achievement badges.
import { apiRequest, pageContent } from "../api.js";
import { badgePanel } from "../badges.js";
import { buttonLoading, buttonReset, floatPoints } from "../motion.js";
import { escapeHtml, formatDate, pageShell, requireLogin, setMain, toast } from "../ui.js";

function badgeCard(badge) {
  const achieved = Boolean(badge.achieved);
  const progress = Math.max(0, Math.min(100, Number(badge.progress) || 0));
  return `
    <article class="badge-card${achieved ? " badge-card--earned" : ""}">
      <div class="badge-card__icon">${escapeHtml(badge.icon || (achieved ? "已" : "锁"))}</div>
      <div class="badge-card__name">${escapeHtml(badge.name || "徽章")}</div>
      <p class="badge-card__desc">${escapeHtml(badge.description || "")}</p>
      ${achieved
        ? '<span class="badge-card__tag">已获得</span>'
        : `
          <div class="progress"><span style="width:${progress}%"></span></div>
          <span class="badge-card__progress">${escapeHtml(String(badge.current ?? 0))} / ${escapeHtml(String(badge.target ?? 0))}</span>
        `}
    </article>
  `;
}

function achievementsSection(achievements) {
  const badges = Array.isArray(achievements?.badges) ? achievements.badges : [];
  const earned = achievements?.earned ?? badges.filter((b) => b.achieved).length;
  const total = achievements?.total ?? badges.length;
  return `
    <section class="card">
      <h3 class="widget__title">成就徽章 (${earned}/${total})</h3>
      <div class="badge-grid">
        ${badges.map(badgeCard).join("") || '<p class="muted">暂无可展示的成就。</p>'}
      </div>
    </section>
  `;
}

function localDateKey(value = new Date()) {
  if (!value) {
    return "";
  }
  const text = String(value);
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    return text.slice(0, 10);
  }
  const date = value instanceof Date ? value : new Date(text);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function hasCheckedInToday(checkIns) {
  const today = localDateKey();
  return checkIns.some((item) => localDateKey(item.checkDate || item.createdAt) === today);
}

export async function renderGrowth() {
  if (!requireLogin()) {
    return;
  }
  const [me, checkIns, points, achievements] = await Promise.all([
    apiRequest("/auth/me"),
    apiRequest("/growth/check-ins").then(pageContent),
    apiRequest("/growth/points-history").then(pageContent),
    apiRequest("/growth/achievements").catch(() => ({ earned: 0, total: 0, badges: [] }))
  ]);
  const userBadges = await apiRequest(`/users/${me.id}/badges`).catch(() => []);
  const checkedToday = hasCheckedInToday(checkIns);
  setMain(pageShell(
    "成长中心",
    "签到成长",
    "每天签到攒积分、升等级，积分可以在积分商城兑换好礼。",
    `
      <section class="section">
        <div class="container split-layout">
          <section class="surface-section stack">
            <div class="duo-grid">
              <article class="card card--quiet"><div class="label">我的积分</div><div class="metric-card__value">${me.points || 0}</div></article>
              <article class="card card--quiet"><div class="label">当前等级</div><div class="metric-card__value">Lv.${me.level || 1}</div></article>
            </div>
            <button class="button button--solid" data-check-in ${checkedToday ? 'disabled aria-disabled="true"' : ""}>${checkedToday ? "今日已签到" : "今日签到"}</button>
            <div class="label">签到记录</div>
            <div class="comment-list">${checkIns.map((item) => `<article class="comment-card"><strong>${formatDate(item.checkDate || item.createdAt)}</strong><p class="muted">积分 +${item.pointsEarned || 0}</p></article>`).join("") || '<p class="muted">还没有签到记录，点上方按钮开始吧。</p>'}</div>
          </section>
          <aside class="card"><h3 class="widget__title">积分流水</h3><div class="comment-list">${points.map((item) => `<article class="comment-card"><strong>${escapeHtml(item.changeType)}</strong><p class="muted">${item.pointsDelta || 0} 积分 · ${formatDate(item.createdAt)}</p></article>`).join("") || '<p class="muted">暂无积分流水。</p>'}</div></aside>
        </div>
      </section>
      <section class="section">
        <div class="container">
          ${achievementsSection(achievements)}
          <section class="card" style="margin-top:16px">
            <h3 class="widget__title">真实校园徽章</h3>
            ${badgePanel(userBadges, "还没有解锁真实徽章。连续签到、发帖、评论和被采纳都会触发徽章检查。")}
          </section>
        </div>
      </section>
    `
  ));
  injectGrowthCss();
  document.querySelector("[data-check-in]")?.addEventListener("click", async () => {
    const button = document.querySelector("[data-check-in]");
    if (!button || button.disabled) {
      return;
    }
    try {
      buttonLoading(button, "Loading");
      await apiRequest("/growth/check-in", { method: "POST" });
      await apiRequest("/badges/check", { method: "POST" }).catch(() => []);
      floatPoints(button, "+2");
      toast("签到成功", "success");
      button.textContent = "今日已签到";
      button.setAttribute("aria-disabled", "true");
      button.disabled = true;
    } catch (error) {
      buttonReset(button);
      toast(error.message, "warning");
    }
  });
}

function injectGrowthCss() {
  if (document.querySelector("[data-growth-style]")) {
    return;
  }
  const style = document.createElement("style");
  style.dataset.growthStyle = "true";
  style.textContent = `
    .badge-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 14px; margin-top: 14px; }
    .badge-card { display: grid; gap: 6px; padding: 16px; border-radius: var(--radius-md); border: 1px solid var(--border); background: var(--surface-quiet); text-align: center; opacity: .62; transition: transform .16s ease, box-shadow .16s ease; }
    .badge-card--earned { opacity: 1; background: var(--surface); border-color: var(--accent); box-shadow: 0 6px 18px var(--accent-soft); }
    .badge-card--earned:hover { transform: translateY(-2px); box-shadow: var(--shadow-hover); }
    .badge-card__icon { font-size: 30px; line-height: 1; }
    .badge-card__name { font-weight: 700; color: var(--ink); }
    .badge-card__desc { margin: 0; font-size: 12px; color: var(--muted); }
    .badge-card__tag { font-size: 12px; font-weight: 700; color: var(--success); }
    .badge-card__progress { font-size: 12px; color: var(--ink-soft); }
  `;
  document.head.appendChild(style);
}
