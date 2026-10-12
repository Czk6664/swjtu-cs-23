// Admin dashboard: data-dense operations console for the dedicated admin page.
import { apiRequest, pageContent } from "../api.js";
import { adminShell } from "../admin-layout.js";
import { ROUTES } from "../constants.js";
import { countUpNumbers, heatBarsEnter } from "../motion.js";
import { escapeHtml, formatDate, requireAdmin, setMain, toast } from "../ui.js";

const COPY = {
  title: "\u7ba1\u7406\u5458\u5de5\u4f5c\u53f0",
  lead: "\u96c6\u4e2d\u5904\u7406\u8bba\u575b\u5ba1\u6838\u3001\u4e3e\u62a5\u3001\u5151\u6362\u4e0e\u8fd0\u8425\u6570\u636e\u3002",
  updated: "\u5df2\u8fde\u63a5\u5b9e\u65f6\u540e\u53f0\u6570\u636e",
  noRows: "\u6682\u65e0\u5f85\u5904\u7406\u4e8b\u9879\u3002",
  retry: "\u91cd\u8bd5\u52a0\u8f7d",
  home: "\u8fd4\u56de\u8bba\u575b\u9996\u9875"
};

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function number(value) {
  return Number(value) || 0;
}

function fmt(value) {
  return number(value).toLocaleString("zh-CN");
}

function percent(value, total) {
  if (!total) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round((number(value) / total) * 100)));
}

function safeTitle(value, fallback = "\u672a\u547d\u540d") {
  return escapeHtml(value || fallback);
}

async function safePage(path, fallback = []) {
  try {
    return pageContent(await apiRequest(path));
  } catch (error) {
    return { error, fallback };
  }
}

async function safeData(path, fallback = null) {
  try {
    return await apiRequest(path);
  } catch (error) {
    return { error, fallback };
  }
}

function unwrap(result, moduleName, errors) {
  if (result && result.error) {
    errors.push({ moduleName, message: result.error.message });
    return result.fallback;
  }
  return result;
}

function dashboardHeader(totals, activeUsers, pendingTotal, errors) {
  const hasRisk = pendingTotal > 0 || errors.length > 0;
  const monthlyActive = totals.monthlyActiveUsers ?? activeUsers.monthly;
  return `
    <header class="admin-dense-header">
      <div>
        <div class="admin-dense-kicker">\u897f\u5357\u4ea4\u5927\u8bba\u575b \u00b7 Admin Ops</div>
        <h1>${COPY.title}</h1>
        <p>${COPY.lead}</p>
      </div>
      <div class="admin-dense-status">
        <span class="admin-status-dot ${hasRisk ? "is-warning" : ""}"></span>
        <div>
          <strong>${hasRisk ? "\u6709\u5f85\u5904\u7406\u4e8b\u9879" : "\u8fd0\u884c\u6b63\u5e38"}</strong>
          <small>${COPY.updated}</small>
        </div>
        <button class="admin-dense-refresh" type="button" data-admin-refresh>\u5237\u65b0</button>
      </div>
    </header>
    ${errors.length ? errorStrip(errors) : ""}
    <section class="admin-dense-summary">
      <div><span>\u603b\u7528\u6237</span><strong>${fmt(totals.users)}</strong></div>
      <div><span>\u603b\u5e16\u5b50</span><strong>${fmt(totals.posts)}</strong></div>
      <div><span>\u5f85\u5904\u7406</span><strong>${fmt(pendingTotal)}</strong></div>
      <div><span>\u6708\u6d3b</span><strong>${fmt(monthlyActive)}</strong></div>
    </section>
  `;
}

function errorStrip(errors) {
  return `
    <section class="admin-dense-alert" role="alert">
      <strong>\u90e8\u5206\u540e\u53f0\u6570\u636e\u52a0\u8f7d\u5931\u8d25</strong>
      <span>${errors.map((item) => `${escapeHtml(item.moduleName)}: ${escapeHtml(item.message)}`).join(" / ")}</span>
      <button type="button" data-admin-refresh>${COPY.retry}</button>
      <a href="${ROUTES.home}">${COPY.home}</a>
    </section>
  `;
}

function kpiCard(label, value, delta, tone = "blue") {
  const deltaText = delta === undefined || delta === null ? "\u5f53\u524d\u6570\u636e" : delta;
  return `
    <article class="admin-kpi admin-kpi--${tone}">
      <span>${escapeHtml(label)}</span>
      <strong data-count-up="${escapeHtml(String(number(value)))}">${fmt(value)}</strong>
      <small>${escapeHtml(deltaText)}</small>
    </article>
  `;
}

function kpiGrid(totals, pending, reports, redemptions, users, posts, rangeDays) {
  const published = totals.publishedPosts ?? posts.filter((post) => Number(post.status) === 1).length;
  return `
    <section class="admin-kpi-grid" aria-label="\u6838\u5fc3\u6307\u6807">
      ${kpiCard("\u7528\u6237\u603b\u6570", totals.users ?? users.length, `\u8fd1 ${rangeDays} \u65e5 +${number(totals.newUsersInRange ?? totals.newUsers7d)}`, "blue")}
      ${kpiCard("\u5e16\u5b50\u603b\u6570", totals.posts ?? posts.length, `\u5df2\u53d1\u5e03 ${fmt(published)}`, "blue")}
      ${kpiCard("\u5f85\u5ba1\u5e16\u5b50", totals.pendingPosts ?? pending.length, "\u9700\u4eca\u65e5\u5904\u7406", pending.length ? "amber" : "green")}
      ${kpiCard("\u5f85\u5904\u7406\u4e3e\u62a5", totals.pendingReports ?? reports.length, "\u5185\u5bb9\u98ce\u9669", reports.length ? "red" : "green")}
      ${kpiCard("\u5f85\u5ba1\u5151\u6362", totals.pendingRedemptions ?? redemptions.length, "\u79ef\u5206\u5546\u57ce", redemptions.length ? "amber" : "green")}
      ${kpiCard("\u8bc4\u8bba\u603b\u6570", totals.comments, `\u8fd1 ${rangeDays} \u65e5 +${number(totals.newCommentsInRange ?? totals.newComments7d)}`, "blue")}
    </section>
  `;
}

function postTrendChart(trend = [], rangeDays = 7) {
  const data = asArray(trend).slice(-rangeDays);
  if (!data.length) {
    return `<p class="admin-empty">\u6682\u65e0\u53d1\u5e16\u8d8b\u52bf\u6570\u636e\u3002</p>`;
  }
  const max = Math.max(1, ...data.map((item) => number(item.posts)));
  const minColumnWidth = data.length > 14 ? 16 : 34;
  return `
    <section class="admin-panel admin-panel--wide">
      <div class="admin-panel__head">
        <div>
          <h2>\u8fd1 ${rangeDays} \u65e5\u53d1\u5e16\u8d8b\u52bf</h2>
          <p>\u6309\u65e5\u7edf\u8ba1\u65b0\u53d1\u5e16\u91cf</p>
        </div>
        <div class="admin-segmented">
          <button class="${rangeDays === 7 ? "is-active" : ""}" type="button" data-admin-range="7">7D</button>
          <button class="${rangeDays === 30 ? "is-active" : ""}" type="button" data-admin-range="30">30D</button>
        </div>
      </div>
      <div class="admin-bar-chart" data-admin-chart style="grid-template-columns: repeat(${data.length}, minmax(${minColumnWidth}px, 1fr));">
        ${data.map((item) => {
          const value = number(item.posts);
          const h = Math.max(8, percent(value, max));
          return `
            <div class="admin-bar" title="${escapeHtml(String(item.date || ""))}: ${value}">
              <span style="height:${h}%"></span>
              <strong>${value}</strong>
              <small>${escapeHtml(String(item.date || "").slice(5))}</small>
            </div>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function riskPanel(reports, pending, redemptions, totals = {}) {
  const reportCount = number(totals.pendingReports ?? reports.length);
  const pendingCount = number(totals.pendingPosts ?? pending.length);
  const redemptionCount = number(totals.pendingRedemptions ?? redemptions.length);
  const total = Math.max(1, reportCount + pendingCount + redemptionCount);
  const reportPct = percent(reportCount, total);
  const pendingPct = percent(pendingCount, total);
  const redeemPct = Math.max(0, 100 - reportPct - pendingPct);
  return `
    <section class="admin-panel">
      <div class="admin-panel__head">
        <div>
          <h2>\u98ce\u9669\u7ec4\u6210</h2>
          <p>\u5f85\u5904\u7406\u4e8b\u9879\u5360\u6bd4</p>
        </div>
      </div>
      <div class="admin-risk">
        <div class="admin-risk__ring" style="--report:${reportPct};--pending:${pendingPct};--redeem:${redeemPct}">
          <strong>${fmt(reportCount + pendingCount + redemptionCount)}</strong>
          <span>\u5f85\u529e</span>
        </div>
        <div class="admin-risk__legend">
          <span><i class="is-red"></i>\u4e3e\u62a5 <strong>${fmt(reportCount)}</strong></span>
          <span><i class="is-blue"></i>\u5f85\u5ba1 <strong>${fmt(pendingCount)}</strong></span>
          <span><i class="is-amber"></i>\u5151\u6362 <strong>${fmt(redemptionCount)}</strong></span>
        </div>
      </div>
    </section>
  `;
}

function workloadRows(pending, reports, redemptions) {
  const rows = [
    ...pending.slice(0, 8).map((post) => ({
      type: "\u5e16\u5b50",
      tone: "blue",
      id: post.id,
      title: post.title,
      user: post.author?.username,
      area: post.section?.name,
      risk: "\u5f85\u5ba1",
      time: post.createdAt,
      actions: `
        <button type="button" data-admin-post="${post.id}" data-status="1">\u901a\u8fc7</button>
        <button type="button" data-admin-post="${post.id}" data-status="3">\u9a73\u56de</button>
      `
    })),
    ...reports.slice(0, 8).map((report) => ({
      type: "\u4e3e\u62a5",
      tone: "red",
      id: report.id,
      title: report.reason || report.post?.title,
      user: report.reporter?.username || report.user?.username,
      area: report.post?.section?.name || "\u5185\u5bb9\u98ce\u9669",
      risk: "\u9700\u6838\u67e5",
      time: report.createdAt,
      actions: `
        <button type="button" data-admin-report="${report.id}" data-accept="true">\u91c7\u7eb3</button>
        <button type="button" data-admin-report="${report.id}" data-accept="false">\u9a73\u56de</button>
      `
    })),
    ...redemptions.slice(0, 8).map((item) => ({
      type: "\u5151\u6362",
      tone: "amber",
      id: item.id,
      title: item.reward?.name,
      user: item.username,
      area: `${number(item.pointsCost)} \u79ef\u5206`,
      risk: "\u5f85\u786e\u8ba4",
      time: item.createdAt,
      actions: `
        <button type="button" data-admin-redemption="${item.id}" data-approve="true">\u901a\u8fc7</button>
        <button type="button" data-admin-redemption="${item.id}" data-approve="false">\u9a73\u56de</button>
      `
    }))
  ];

  if (!rows.length) {
    return `<tr><td colspan="7"><p class="admin-empty">${COPY.noRows}</p></td></tr>`;
  }

  return rows.slice(0, 14).map((row) => `
    <tr class="admin-work-row">
      <td><span class="admin-type admin-type--${row.tone}">${escapeHtml(row.type)}</span></td>
      <td><strong>${safeTitle(row.title)}</strong><small>#${escapeHtml(row.id)}</small></td>
      <td>${escapeHtml(row.user || "\u672a\u77e5\u7528\u6237")}</td>
      <td>${escapeHtml(row.area || "\u672a\u5206\u7c7b")}</td>
      <td><span class="admin-risk-tag admin-risk-tag--${row.tone}">${escapeHtml(row.risk)}</span></td>
      <td>${formatDate(row.time)}</td>
      <td><div class="admin-row-actions">${row.actions}</div></td>
    </tr>
  `).join("");
}

function workloadTable(pending, reports, redemptions) {
  return `
    <section class="admin-panel admin-panel--wide">
      <div class="admin-panel__head">
        <div>
          <h2>\u4eca\u65e5\u5f85\u529e</h2>
          <p>\u5e16\u5b50\u5ba1\u6838\u3001\u4e3e\u62a5\u5904\u7406\u548c\u5151\u6362\u5ba1\u6838</p>
        </div>
        <div class="admin-filter-tabs">
          <button class="is-active" type="button">\u5168\u90e8</button>
          <button type="button">\u5f85\u5ba1</button>
          <button type="button">\u4e3e\u62a5</button>
          <button type="button">\u5151\u6362</button>
        </div>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>\u7c7b\u578b</th>
              <th>\u6807\u9898/\u5bf9\u8c61</th>
              <th>\u7528\u6237</th>
              <th>\u677f\u5757</th>
              <th>\u98ce\u9669</th>
              <th>\u65f6\u95f4</th>
              <th>\u64cd\u4f5c</th>
            </tr>
          </thead>
          <tbody>${workloadRows(pending, reports, redemptions)}</tbody>
        </table>
      </div>
    </section>
  `;
}

function sectionRank(distribution = []) {
  const rows = asArray(distribution).slice(0, 7);
  const max = Math.max(1, ...rows.map((item) => number(item.posts)));
  return `
    <section class="admin-panel">
      <div class="admin-panel__head">
        <div>
          <h2>\u677f\u5757\u6d3b\u8dc3</h2>
          <p>\u6309\u53d1\u5e16\u91cf\u6392\u5e8f</p>
        </div>
      </div>
      <div class="admin-rank-list">
        ${rows.length ? rows.map((item, index) => {
          const value = number(item.posts);
          return `
            <div class="admin-rank-row">
              <span>${index + 1}</span>
              <strong>${escapeHtml(item.section || "\u672a\u5206\u7c7b")}</strong>
              <div><i style="width:${percent(value, max)}%"></i></div>
              <em>${value}</em>
            </div>
          `;
        }).join("") : `<p class="admin-empty">\u6682\u65e0\u677f\u5757\u6570\u636e\u3002</p>`}
      </div>
    </section>
  `;
}

function hotPostsTable(posts = []) {
  const rows = asArray(posts).slice(0, 6);
  return `
    <section class="admin-panel">
      <div class="admin-panel__head">
        <div>
          <h2>\u70ed\u95e8\u5e16\u5b50</h2>
          <p>\u6309\u70ed\u5ea6\u6392\u5e8f</p>
        </div>
      </div>
      <div class="admin-mini-list">
        ${rows.length ? rows.map((post, index) => `
          <a href="${ROUTES.detail}?id=${encodeURIComponent(String(post.id))}">
            <span>${index + 1}</span>
            <strong>${safeTitle(post.title, "\u65e0\u6807\u9898")}</strong>
            <small>\u70ed\u5ea6 ${fmt(post.heatScore)} / \u8bc4\u8bba ${fmt(post.commentCount)}</small>
          </a>
        `).join("") : `<p class="admin-empty">\u6682\u65e0\u70ed\u95e8\u5e16\u5b50\u3002</p>`}
      </div>
    </section>
  `;
}

function logPanel(logs = []) {
  const rows = asArray(logs).slice(0, 8);
  return `
    <section class="admin-panel admin-panel--wide" id="admin-logs">
      <div class="admin-panel__head">
        <div>
          <h2>\u6700\u8fd1\u64cd\u4f5c\u65e5\u5fd7</h2>
          <p>\u540e\u53f0\u5ba1\u6838\u3001\u7528\u6237\u548c\u914d\u7f6e\u53d8\u66f4\u8bb0\u5f55</p>
        </div>
      </div>
      <div class="admin-log-table">
        ${rows.length ? rows.map((log) => `
          <article>
            <time>${formatDate(log.createdAt)}</time>
            <strong>${escapeHtml(actionLabel(log.action))}</strong>
            <span>${escapeHtml(log.actor?.username || "\u7cfb\u7edf")}</span>
            <p>${escapeHtml(log.detail || `${log.targetType || "\u5bf9\u8c61"} #${log.targetId || "-"}`)}</p>
          </article>
        `).join("") : `<p class="admin-empty">\u6682\u65e0\u64cd\u4f5c\u65e5\u5fd7\u3002</p>`}
      </div>
    </section>
  `;
}

function quickLinks() {
  const links = [
    [ROUTES.moderation, "\u5185\u5bb9\u6cbb\u7406", "\u5904\u7406\u5f85\u5ba1\u3001\u4e3e\u62a5\u548c\u9690\u85cf\u5e16"],
    [ROUTES.users, "\u7528\u6237\u7ba1\u7406", "\u67e5\u770b\u7528\u6237\u3001\u5c01\u7981\u548c\u89d2\u8272\u72b6\u6001"],
    [ROUTES.recommendation, "\u63a8\u8350\u7b56\u7565", "\u8c03\u6574\u9996\u9875\u66dd\u5149\u6743\u91cd"],
    [ROUTES.adminRewards, "\u79ef\u5206\u5956\u52b1", "\u67e5\u770b\u5956\u52b1\u548c\u5151\u6362\u8bb0\u5f55"]
  ];
  return `
    <section class="admin-panel">
      <div class="admin-panel__head">
        <div>
          <h2>\u5feb\u6377\u5165\u53e3</h2>
          <p>\u5e38\u7528\u540e\u53f0\u6a21\u5757</p>
        </div>
      </div>
      <div class="admin-quick-links">
        ${links.map(([href, title, text]) => `
          <a href="${href}">
            <strong>${title}</strong>
            <span>${text}</span>
          </a>
        `).join("")}
      </div>
    </section>
  `;
}

function actionLabel(action) {
  const labels = {
    REVIEW_POST: "\u5185\u5bb9\u5ba1\u6838",
    BAN_USER: "\u5c01\u7981\u7528\u6237",
    UNBAN_USER: "\u89e3\u9664\u5c01\u7981",
    CREATE_SECTION: "\u65b0\u589e\u677f\u5757",
    UPDATE_SECTION: "\u66f4\u65b0\u677f\u5757",
    DELETE_SECTION: "\u5220\u9664\u677f\u5757",
    REVIEW_REPORT: "\u5904\u7406\u4e3e\u62a5"
  };
  return labels[action] || action || "\u540e\u53f0\u64cd\u4f5c";
}

function bindAdminActions(rangeDays = 7) {
  document.querySelectorAll("[data-admin-refresh]").forEach((button) => {
    button.addEventListener("click", () => renderAdmin(rangeDays));
  });
  document.querySelectorAll("[data-admin-range]").forEach((button) => {
    button.addEventListener("click", () => renderAdmin(Number(button.dataset.adminRange) || 7));
  });
  document.querySelectorAll("[data-admin-post]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        await apiRequest(`/admin/posts/${button.dataset.adminPost}/status`, {
          method: "PATCH",
          body: { status: Number(button.dataset.status) }
        });
        toast("\u5e16\u5b50\u5ba1\u6838\u72b6\u6001\u5df2\u66f4\u65b0", "success");
        button.closest(".admin-work-row")?.classList.add("is-removing");
        setTimeout(() => renderAdmin(rangeDays), 180);
      } catch (error) {
        button.disabled = false;
        toast(error.message, "warning");
      }
    });
  });
  document.querySelectorAll("[data-admin-report]").forEach((button) => {
    button.addEventListener("click", async () => {
      const accept = button.dataset.accept === "true";
      button.disabled = true;
      try {
        await apiRequest(`/admin/reports/${button.dataset.adminReport}/review`, {
          method: "PATCH",
          body: {
            accept,
            reviewNote: accept ? "\u540e\u53f0\u603b\u89c8\u5feb\u901f\u91c7\u7eb3" : "\u540e\u53f0\u603b\u89c8\u5feb\u901f\u9a73\u56de"
          }
        });
        toast(accept ? "\u4e3e\u62a5\u5df2\u91c7\u7eb3" : "\u4e3e\u62a5\u5df2\u9a73\u56de", "success");
        button.closest(".admin-work-row")?.classList.add("is-removing");
        setTimeout(() => renderAdmin(rangeDays), 180);
      } catch (error) {
        button.disabled = false;
        toast(error.message, "warning");
      }
    });
  });
  document.querySelectorAll("[data-admin-redemption]").forEach((button) => {
    button.addEventListener("click", async () => {
      const approve = button.dataset.approve === "true";
      button.disabled = true;
      try {
        await apiRequest(`/admin/redemptions/${button.dataset.adminRedemption}/review`, {
          method: "PATCH",
          body: {
            approve,
            note: approve ? "\u540e\u53f0\u603b\u89c8\u5feb\u901f\u901a\u8fc7" : "\u540e\u53f0\u603b\u89c8\u5feb\u901f\u9a73\u56de"
          }
        });
        toast(approve ? "\u5151\u6362\u7533\u8bf7\u5df2\u901a\u8fc7" : "\u5151\u6362\u7533\u8bf7\u5df2\u9a73\u56de", "success");
        button.closest(".admin-work-row")?.classList.add("is-removing");
        setTimeout(() => renderAdmin(rangeDays), 180);
      } catch (error) {
        button.disabled = false;
        toast(error.message, "warning");
      }
    });
  });
}

export async function renderAdmin(rangeDays = 7) {
  if (!requireAdmin()) {
    return;
  }
  const safeRangeDays = rangeDays === 30 ? 30 : 7;

  const results = await Promise.all([
    safePage("/admin/posts", []),
    safePage("/admin/users", []),
    safePage("/admin/posts/pending", []),
    safePage("/admin/reports?status=0", []),
    safeData("/admin/reports/summary", {}),
    safeData(`/admin/analytics?days=${safeRangeDays}`, null),
    safePage("/admin/redemptions/pending", []),
    safePage("/admin/logs", [])
  ]);

  const errors = [];
  const posts = unwrap(results[0], "\u5e16\u5b50\u5217\u8868", errors);
  const users = unwrap(results[1], "\u7528\u6237\u5217\u8868", errors);
  const pending = unwrap(results[2], "\u5f85\u5ba1\u5e16\u5b50", errors);
  const reports = unwrap(results[3], "\u4e3e\u62a5\u961f\u5217", errors);
  const summary = unwrap(results[4], "\u4e3e\u62a5\u6c47\u603b", errors) || {};
  const analytics = unwrap(results[5], "\u6570\u636e\u770b\u677f", errors) || {};
  const redemptions = unwrap(results[6], "\u5151\u6362\u5ba1\u6838", errors);
  const logs = unwrap(results[7], "\u64cd\u4f5c\u65e5\u5fd7", errors);
  const totals = analytics.totals || {};
  const activeUsers = analytics.activeUsers || {};
  const actualRangeDays = number(analytics.rangeDays) || safeRangeDays;
  const pendingTotal = (totals.pendingPosts ?? pending.length)
    + (totals.pendingReports ?? summary.pending ?? reports.length)
    + (totals.pendingRedemptions ?? redemptions.length);

  setMain(adminShell(`
    ${dashboardHeader(totals, activeUsers, pendingTotal, errors)}
    ${kpiGrid(totals, pending, reports, redemptions, users, posts, actualRangeDays)}
    <div class="admin-dense-grid">
      ${postTrendChart(analytics.postTrend, actualRangeDays)}
      ${riskPanel(reports, pending, redemptions, totals)}
      ${workloadTable(pending, reports, redemptions)}
      ${sectionRank(analytics.sectionDistribution)}
      ${logPanel(logs)}
      <div class="admin-dense-side-stack">
        ${hotPostsTable(analytics.hotPosts)}
        ${quickLinks()}
      </div>
    </div>
  `, "overview"));

  bindAdminActions(actualRangeDays);
  injectAdminCss();
  countUpNumbers(document);
  heatBarsEnter(document);
}

function injectAdminCss() {
  if (document.querySelector("[data-admin-style]")) {
    return;
  }
  const style = document.createElement("style");
  style.dataset.adminStyle = "true";
  style.textContent = `
    body:has(.admin-dense-shell) { background: #f5f9fc; }
    .admin-dense-shell { display: grid; grid-template-columns: 236px minmax(0, 1fr); min-height: calc(100vh - 74px); border-top: 1px solid var(--border); }
    .admin-dense-sidebar { position: sticky; top: 74px; align-self: start; height: calc(100vh - 74px); padding: 18px 14px; border-right: 1px solid #d8e8f3; background: linear-gradient(180deg, #ffffff, #eef6fb); overflow: auto; }
    .admin-dense-sidebar__head { display: flex; align-items: center; gap: 10px; padding: 8px 8px 16px; border-bottom: 1px solid #d8e8f3; }
    .admin-dense-sidebar__mark { width: 36px; height: 36px; display: grid; place-items: center; border-radius: 12px; background: var(--brand); color: #fff; font-weight: 800; font-size: 13px; box-shadow: 0 4px 10px rgba(0,117,184,.18); }
    .admin-dense-sidebar__head strong, .admin-dense-sidebar__note strong { display: block; color: #162636; font-size: 14px; }
    .admin-dense-sidebar__head small, .admin-dense-sidebar__note small { display: block; color: #6b7a8c; font-size: 12px; margin-top: 2px; }
    .admin-dense-nav { display: grid; gap: 5px; padding: 14px 0; }
    .admin-dense-nav a { display: grid; grid-template-columns: 32px 1fr; align-items: center; gap: 8px; min-height: 40px; padding: 0 10px; border-radius: 10px; color: #3d5168; transition: background-color .16s ease, color .16s ease, transform .16s ease; }
    .admin-dense-nav a:hover { background: rgba(0,117,184,.08); color: var(--brand); transform: translateX(1px); }
    .admin-dense-nav a.is-active { background: var(--brand); color: #fff; }
    .admin-dense-nav span { font-family: var(--font-mono); font-size: 11px; opacity: .72; }
    .admin-dense-nav strong { font-size: 14px; font-weight: 700; }
    .admin-dense-sidebar__note { display: grid; grid-template-columns: 10px 1fr; gap: 9px; align-items: start; margin-top: 10px; padding: 12px; border-radius: 12px; border: 1px solid #d8e8f3; background: #fff; }
    .admin-status-dot { width: 9px; height: 9px; margin-top: 4px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 4px rgba(34,197,94,.12); }
    .admin-status-dot.is-warning { background: #f59e0b; box-shadow: 0 0 0 4px rgba(245,158,11,.14); }
    .admin-dense-main { min-width: 0; padding: 18px 20px 28px; }
    .admin-dense-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; margin-bottom: 12px; }
    .admin-dense-kicker { color: var(--brand); font-weight: 800; font-size: 13px; margin-bottom: 6px; }
    .admin-dense-header h1 { margin: 0; color: #162636; font-size: 28px; line-height: 1.18; letter-spacing: -.02em; }
    .admin-dense-header p { margin: 7px 0 0; max-width: 680px; color: #3d5168; line-height: 1.55; }
    .admin-dense-status { display: grid; grid-template-columns: 12px 1fr auto; align-items: center; gap: 10px; min-width: 330px; padding: 12px; border: 1px solid #d8e8f3; border-radius: 14px; background: #fff; }
    .admin-dense-status strong { color: #162636; font-size: 14px; }
    .admin-dense-status small { display: block; color: #6b7a8c; font-size: 12px; margin-top: 2px; }
    .admin-dense-refresh, .admin-dense-alert button { border: 1px solid #b8d8eb; background: #eef7fc; color: var(--brand); border-radius: 10px; padding: 7px 10px; font-weight: 700; cursor: pointer; }
    .admin-dense-alert { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; padding: 10px 12px; border: 1px solid rgba(245,158,11,.28); border-radius: 12px; background: #fff8eb; color: #7a4f00; }
    .admin-dense-alert strong { color: #543500; }
    .admin-dense-alert span { flex: 1 1 320px; font-size: 13px; }
    .admin-dense-alert a { color: var(--brand); font-weight: 700; }
    .admin-dense-summary, .admin-kpi-grid { display: grid; gap: 10px; }
    .admin-dense-summary { grid-template-columns: repeat(4, minmax(0, 1fr)); margin-bottom: 12px; }
    .admin-dense-summary div { padding: 10px 12px; border: 1px solid #d8e8f3; border-radius: 12px; background: #fff; }
    .admin-dense-summary span, .admin-kpi span, .admin-kpi small { display: block; color: #6b7a8c; font-size: 12px; }
    .admin-dense-summary strong { display: block; margin-top: 4px; color: #162636; font: 800 22px/1 var(--font-mono); }
    .admin-kpi-grid { grid-template-columns: repeat(6, minmax(135px, 1fr)); margin-bottom: 12px; }
    .admin-kpi { min-height: 112px; padding: 14px; border: 1px solid #d8e8f3; border-radius: 14px; background: #fff; }
    .admin-kpi strong { display: block; margin: 10px 0 8px; color: #162636; font: 800 28px/1 var(--font-mono); letter-spacing: -.03em; }
    .admin-kpi--blue { box-shadow: inset 0 3px 0 var(--brand); }
    .admin-kpi--green { box-shadow: inset 0 3px 0 #22c55e; }
    .admin-kpi--amber { box-shadow: inset 0 3px 0 #f59e0b; }
    .admin-kpi--red { box-shadow: inset 0 3px 0 #ef4444; }
    .admin-dense-grid { display: grid; grid-template-columns: minmax(0, 2fr) minmax(310px, .9fr); gap: 12px; align-items: start; }
    .admin-dense-side-stack { display: grid; gap: 12px; }
    .admin-panel { min-width: 0; border: 1px solid #d8e8f3; border-radius: 14px; background: #fff; overflow: hidden; }
    .admin-panel--wide { grid-column: span 1; }
    .admin-panel__head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; padding: 14px 16px 10px; border-bottom: 1px solid #edf3f8; }
    .admin-panel__head h2 { margin: 0; color: #162636; font-size: 17px; line-height: 1.25; }
    .admin-panel__head p { margin: 4px 0 0; color: #6b7a8c; font-size: 12px; }
    .admin-segmented, .admin-filter-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
    .admin-segmented button, .admin-filter-tabs button { border: 1px solid #d8e8f3; border-radius: 9px; background: #f5f9fc; color: #3d5168; padding: 6px 9px; font-weight: 700; font-size: 12px; cursor: pointer; }
    .admin-segmented .is-active, .admin-filter-tabs .is-active { background: var(--brand); color: #fff; border-color: var(--brand); }
    .admin-bar-chart { height: 260px; display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; align-items: end; padding: 18px 18px 16px; }
    .admin-bar { height: 100%; display: grid; grid-template-rows: 1fr auto auto; align-items: end; gap: 5px; color: #6b7a8c; text-align: center; }
    .admin-bar span { display: block; min-height: 8px; border-radius: 8px 8px 3px 3px; background: linear-gradient(180deg, #0b8ed8, #0075b8); transition: height .22s ease; }
    .admin-bar:hover span { filter: brightness(1.08); }
    .admin-bar strong { color: #162636; font: 700 12px/1 var(--font-mono); }
    .admin-bar small { font-size: 11px; }
    .admin-risk { display: grid; place-items: center; gap: 16px; padding: 20px; }
    .admin-risk__ring { width: 170px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 50%; background: conic-gradient(#ef4444 0 calc(var(--report) * 1%), #0075b8 0 calc((var(--report) + var(--pending)) * 1%), #f59e0b 0 100%); position: relative; }
    .admin-risk__ring:after { content: ""; position: absolute; inset: 17px; border-radius: 50%; background: #fff; }
    .admin-risk__ring strong, .admin-risk__ring span { position: relative; z-index: 1; }
    .admin-risk__ring strong { align-self: end; font: 800 34px/1 var(--font-mono); color: #162636; }
    .admin-risk__ring span { align-self: start; color: #6b7a8c; font-size: 12px; }
    .admin-risk__legend { width: 100%; display: grid; gap: 8px; }
    .admin-risk__legend span { display: grid; grid-template-columns: 12px 1fr auto; gap: 8px; align-items: center; color: #3d5168; }
    .admin-risk__legend i { width: 9px; height: 9px; border-radius: 50%; }
    .is-red { background: #ef4444; } .is-blue { background: #0075b8; } .is-amber { background: #f59e0b; }
    .admin-table-wrap { overflow: auto; }
    .admin-table { width: 100%; border-collapse: collapse; min-width: 760px; }
    .admin-table th { padding: 10px 12px; background: #f1f7fb; color: #607486; text-align: left; font-size: 12px; font-weight: 800; }
    .admin-table td { padding: 10px 12px; border-top: 1px solid #edf3f8; color: #3d5168; font-size: 13px; vertical-align: middle; }
    .admin-table tr { transition: background-color .14s ease, opacity .18s ease, transform .18s ease; }
    .admin-table tbody tr:hover { background: #f8fbfd; }
    .admin-table tr.is-removing { opacity: 0; transform: translateX(10px); }
    .admin-table td strong { display: block; color: #162636; max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .admin-table td small { display: block; color: #8a9aaa; margin-top: 2px; font-family: var(--font-mono); }
    .admin-type, .admin-risk-tag { display: inline-flex; align-items: center; min-height: 24px; padding: 0 8px; border-radius: 999px; font-size: 12px; font-weight: 800; }
    .admin-type--blue, .admin-risk-tag--blue { color: #00639d; background: rgba(0,117,184,.1); }
    .admin-type--red, .admin-risk-tag--red { color: #b42323; background: rgba(239,68,68,.1); }
    .admin-type--amber, .admin-risk-tag--amber { color: #9a5d00; background: rgba(245,158,11,.14); }
    .admin-row-actions { display: flex; gap: 6px; }
    .admin-row-actions button { border: 1px solid #c8ddeb; background: #fff; color: var(--brand); border-radius: 8px; padding: 6px 8px; cursor: pointer; font-weight: 800; font-size: 12px; }
    .admin-row-actions button:first-child { background: var(--brand); border-color: var(--brand); color: #fff; }
    .admin-row-actions button:disabled { opacity: .5; cursor: progress; }
    .admin-rank-list, .admin-mini-list, .admin-quick-links, .admin-log-table { padding: 12px 14px 14px; }
    .admin-rank-list { display: grid; gap: 10px; }
    .admin-rank-row { display: grid; grid-template-columns: 24px minmax(74px, 1fr) 1.4fr 36px; align-items: center; gap: 8px; color: #3d5168; font-size: 13px; }
    .admin-rank-row span { font-family: var(--font-mono); color: #6b7a8c; }
    .admin-rank-row strong { color: #162636; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .admin-rank-row div { height: 8px; border-radius: 999px; background: #edf5fb; overflow: hidden; }
    .admin-rank-row i { display: block; height: 100%; border-radius: inherit; background: var(--brand); }
    .admin-rank-row em { font-style: normal; text-align: right; font-family: var(--font-mono); }
    .admin-mini-list, .admin-quick-links { display: grid; gap: 8px; }
    .admin-mini-list a, .admin-quick-links a { display: grid; grid-template-columns: 24px 1fr; gap: 3px 8px; padding: 10px; border-radius: 10px; background: #f8fbfd; transition: background-color .14s ease; }
    .admin-mini-list a:hover, .admin-quick-links a:hover { background: #eef7fc; }
    .admin-mini-list span { grid-row: span 2; width: 22px; height: 22px; display: grid; place-items: center; border-radius: 50%; background: #e0f1fb; color: var(--brand); font-weight: 800; font-size: 12px; }
    .admin-mini-list strong, .admin-quick-links strong { color: #162636; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .admin-mini-list small, .admin-quick-links span { color: #6b7a8c; font-size: 12px; }
    .admin-quick-links a { grid-template-columns: 1fr; border: 1px solid #edf3f8; }
    .admin-log-table { display: grid; gap: 0; }
    .admin-log-table article { display: grid; grid-template-columns: 92px 120px 92px 1fr; gap: 10px; padding: 10px 0; border-top: 1px solid #edf3f8; align-items: center; color: #3d5168; font-size: 13px; }
    .admin-log-table article:first-child { border-top: 0; }
    .admin-log-table time { font-family: var(--font-mono); color: #6b7a8c; }
    .admin-log-table strong { color: #162636; }
    .admin-log-table p { margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .admin-empty { margin: 0; padding: 18px; color: #6b7a8c; font-size: 13px; }
    @media (max-width: 1120px) {
      .admin-dense-shell { grid-template-columns: 72px minmax(0, 1fr); }
      .admin-dense-sidebar__head div, .admin-dense-sidebar__note, .admin-dense-nav strong { display: none; }
      .admin-dense-nav a { grid-template-columns: 1fr; justify-items: center; }
      .admin-kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .admin-dense-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 760px) {
      .admin-dense-shell { display: block; }
      .admin-dense-sidebar { position: static; height: auto; display: flex; gap: 10px; overflow-x: auto; border-right: 0; border-bottom: 1px solid #d8e8f3; }
      .admin-dense-sidebar__head, .admin-dense-sidebar__note { display: none; }
      .admin-dense-nav { display: flex; padding: 0; }
      .admin-dense-nav a { min-width: 58px; }
      .admin-dense-main { padding: 14px 12px 22px; }
      .admin-dense-header, .admin-dense-status { display: grid; min-width: 0; }
      .admin-dense-summary, .admin-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .admin-log-table article { grid-template-columns: 1fr; gap: 4px; }
    }
    @media (prefers-reduced-motion: reduce) {
      .admin-dense-nav a, .admin-table tr, .admin-row-actions button, .admin-mini-list a, .admin-quick-links a { transition: none; }
    }
  `;
  document.head.appendChild(style);
}
