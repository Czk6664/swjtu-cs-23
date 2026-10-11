// Shared badge rendering helpers for profile, post detail, and growth center.
import { escapeHtml, formatDate } from "./ui.js";
import { badgeAsset, emptyAsset } from "./visual-assets.js";

export function normalizeUserBadges(userBadges = []) {
  return (Array.isArray(userBadges) ? userBadges : [])
    .map((item) => ({
      id: item.id,
      earnedAt: item.earnedAt,
      ...(item.badge || item)
    }))
    .filter((badge) => badge?.code || badge?.name);
}

export function badgeChips(userBadges = [], limit = 4) {
  const badges = normalizeUserBadges(userBadges).slice(0, limit);
  if (!badges.length) {
    return "";
  }
  return `
    <div class="badge-chip-list">
      ${badges.map((badge) => `
        <span class="badge-chip" title="${escapeHtml(badge.description || badge.name || "校园徽章")}">
          <span class="badge-chip__icon"><img src="${badgeAsset(badge.name || badge.code)}" alt="" loading="lazy" /></span>
          ${escapeHtml(badge.name || "校园徽章")}
        </span>
      `).join("")}
    </div>
  `;
}

export function badgePanel(userBadges = [], emptyText = "还没有获得徽章，去发帖、评论、签到试试吧。") {
  const badges = normalizeUserBadges(userBadges);
  if (!badges.length) {
    return `<article class="badge-empty badge-empty--visual"><img src="${emptyAsset("badges")}" alt="" loading="lazy" /><span>${escapeHtml(emptyText)}</span></article>`;
  }
  return `
    <div class="campus-badge-grid">
      ${badges.map((badge) => `
        <article class="campus-badge-card">
          <div class="campus-badge-card__icon"><img src="${badgeAsset(badge.name || badge.code)}" alt="" loading="lazy" /></div>
          <div>
            <strong>${escapeHtml(badge.name || "校园徽章")}</strong>
            <p>${escapeHtml(badge.description || "")}</p>
            <span>${badge.earnedAt ? `${formatDate(badge.earnedAt)} 获得` : "已获得"}</span>
          </div>
        </article>
      `).join("")}
    </div>
  `;
}
