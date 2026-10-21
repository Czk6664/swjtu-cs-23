// Rewards mall: redeemable points store and personal redemption history.
import { apiRequest, pageContent } from "../api.js";
import { adminPageShell } from "../admin-layout.js";
import { state } from "../session.js";
import { escapeHtml, formValues, pageShell, requireAdmin, requireLogin, setMain, toast } from "../ui.js";
import { emptyAsset, rewardAsset } from "../visual-assets.js";

function displayRewardName(name = "") {
  return String(name).replace(/^【演示】\s*/, "").trim() || "校园奖励";
}

export async function renderRewards() {
  if (!requireLogin()) {
    return;
  }
  const adminMode = document.body?.dataset.page === "admin-rewards"
    || new URLSearchParams(location.search).get("admin") === "1";
  if (adminMode && !requireAdmin()) {
    return;
  }
  if (adminMode) {
    await renderAdminRewards();
    return;
  }
  const [rewards, redemptions] = await Promise.all([
    apiRequest("/growth/rewards"),
    apiRequest("/growth/redemptions").then(pageContent)
  ]);
  setMain(pageShell(
    "积分商城",
    "用积分兑好礼",
    "签到、发帖、参与讨论都能攒积分，在这里换成校园周边和福利。",
    `
      <section class="section">
        <div class="container split-layout">
          <div class="card-grid">
            ${rewards.map((item) => `<article class="card reward-card"><img class="reward-card__image" src="${rewardAsset(item.name)}" alt="" loading="lazy" /><div class="toolbar-space"><h3 class="post-card__title">${escapeHtml(displayRewardName(item.name))}</h3><span class="tag tag--brand">${item.costPoints} 积分</span></div><p class="muted">${escapeHtml(item.description || "")}</p><button class="button button--solid button--sm" data-redeem="${item.id}">申请兑换</button></article>`).join("") || `<article class="card empty-inline"><img src="${emptyAsset("rewards")}" alt="" /><p class="muted">商城还没有上架奖品。</p></article>`}
          </div>
          <aside class="card"><h3 class="widget__title">我的兑换</h3><div class="comment-list">${redemptions.map((item) => `<article class="comment-card"><strong>${escapeHtml(displayRewardName(item.reward?.name || "奖励"))}</strong><p class="muted">状态：${escapeHtml(String(item.status))}</p></article>`).join("") || '<p class="muted">还没有兑换记录。</p>'}</div></aside>
        </div>
      </section>
    `
  ));
  document.querySelectorAll("[data-redeem]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await apiRequest(`/growth/rewards/${button.dataset.redeem}/redeem`, { method: "POST" });
        toast("兑换申请已提交", "success");
        button.textContent = "已提交申请";
        button.disabled = true;
      } catch (error) {
        toast(error.message, "warning");
      }
    });
  });
  injectRewardCss();
}

async function renderAdminRewards() {
  let rewards = [];
  try {
    rewards = await apiRequest("/admin/rewards");
  } catch (error) {
    setMain(adminPageShell(
      "rewards",
      "积分奖励",
      "积分商品管理",
      "维护积分商城商品，上架后会展示给普通用户；下架后用户不可兑换。",
      `
        <section class="admin-reward-panel">
          <h2>积分奖励数据加载失败</h2>
          <p class="muted">${escapeHtml(error.message || "请检查后端服务是否已启动。")}</p>
          <button class="button button--solid" type="button" data-admin-reward-retry>重新加载</button>
        </section>
      `
    ));
    document.querySelector("[data-admin-reward-retry]")?.addEventListener("click", () => renderAdminRewards());
    injectRewardCss();
    return;
  }
  const activeCount = rewards.filter((item) => Number(item.status) === 1).length;
  const stockTotal = rewards.reduce((sum, item) => sum + (Number(item.stock) || 0), 0);
  setMain(adminPageShell(
    "rewards",
    "积分奖励",
    "积分商品管理",
    "维护积分商城商品，上架后会展示给普通用户；下架后用户不可兑换。",
    `
      <section class="admin-reward-grid">
        <section class="admin-reward-panel">
          <div class="admin-reward-metrics">
            <article><span>商品总数</span><strong>${rewards.length}</strong></article>
            <article><span>已上架</span><strong>${activeCount}</strong></article>
            <article><span>总库存</span><strong>${stockTotal}</strong></article>
          </div>
          <div class="admin-reward-table-wrap">
            <table class="admin-reward-table">
              <thead>
                <tr>
                  <th>商品</th>
                  <th>积分</th>
                  <th>库存</th>
                  <th>状态</th>
                  <th>更新时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                ${rewards.map(adminRewardRow).join("") || '<tr><td colspan="6"><p class="muted">还没有积分商品。</p></td></tr>'}
              </tbody>
            </table>
          </div>
        </section>
        <aside class="admin-reward-panel">
          <h2>新增积分商品</h2>
          <form class="quick-form" data-admin-reward-form>
            <div class="field">
              <label>商品名称</label>
              <input class="input" name="name" required maxlength="100" placeholder="例如：校园咖啡兑换券" />
            </div>
            <div class="field">
              <label>商品说明</label>
              <textarea class="textarea" name="description" maxlength="500" placeholder="说明兑换内容、使用地点或领取方式"></textarea>
            </div>
            <div class="duo-grid">
              <div class="field">
                <label>所需积分</label>
                <input class="input" name="costPoints" type="number" min="1" value="100" />
              </div>
              <div class="field">
                <label>库存</label>
                <input class="input" name="stock" type="number" min="0" value="10" />
              </div>
            </div>
            <label class="admin-reward-check"><input type="checkbox" name="active" checked /> 创建后立即上架</label>
            <button class="button button--solid" type="submit">创建商品</button>
          </form>
        </aside>
      </section>
    `
  ));
  bindAdminRewardActions();
  injectRewardCss();
}

function adminRewardRow(item) {
  const active = Number(item.status) === 1;
  return `
    <tr>
      <td>
        <div class="admin-reward-item">
          <img src="${rewardAsset(item.name)}" alt="" loading="lazy" />
          <div>
            <strong>${escapeHtml(displayRewardName(item.name))}</strong>
            <small>${escapeHtml(item.description || "暂无说明")}</small>
          </div>
        </div>
      </td>
      <td>${Number(item.costPoints) || 0}</td>
      <td>${Number(item.stock) || 0}</td>
      <td><span class="status-pill ${active ? "status-pill--ok" : "status-pill--muted"}">${active ? "已上架" : "已下架"}</span></td>
      <td>${escapeHtml(String(item.updatedAt || item.createdAt || "").slice(0, 10) || "-")}</td>
      <td>
        <div class="admin-reward-actions">
          <button type="button" data-edit-reward="${item.id}" data-name="${escapeHtml(item.name || "")}" data-description="${escapeHtml(item.description || "")}" data-cost="${Number(item.costPoints) || 0}" data-stock="${Number(item.stock) || 0}" data-status="${Number(item.status) || 0}">编辑</button>
          <button type="button" data-toggle-reward="${item.id}" data-next-status="${active ? 0 : 1}">${active ? "下架" : "上架"}</button>
        </div>
      </td>
    </tr>
  `;
}

function bindAdminRewardActions() {
  document.querySelector("[data-admin-reward-form]")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = formValues(event.currentTarget);
    try {
      await apiRequest("/admin/rewards", {
        method: "POST",
        body: rewardPayload(data)
      });
      toast("积分商品已创建", "success");
      await renderAdminRewards();
    } catch (error) {
      toast(error.message, "warning");
    }
  });
  document.querySelectorAll("[data-toggle-reward]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        await apiRequest(`/admin/rewards/${button.dataset.toggleReward}/status?status=${button.dataset.nextStatus}`, {
          method: "PATCH"
        });
        toast(button.dataset.nextStatus === "1" ? "商品已上架" : "商品已下架", "success");
        await renderAdminRewards();
      } catch (error) {
        button.disabled = false;
        toast(error.message, "warning");
      }
    });
  });
  document.querySelectorAll("[data-edit-reward]").forEach((button) => {
    button.addEventListener("click", async () => {
      const name = window.prompt("商品名称", button.dataset.name || "");
      if (!name) {
        return;
      }
      const description = window.prompt("商品说明", button.dataset.description || "") || "";
      const costPoints = window.prompt("所需积分", button.dataset.cost || "100");
      if (!costPoints) {
        return;
      }
      const stock = window.prompt("库存", button.dataset.stock || "0");
      if (stock === null) {
        return;
      }
      try {
        await apiRequest(`/admin/rewards/${button.dataset.editReward}`, {
          method: "PUT",
          body: {
            name: name.trim(),
            description: description.trim(),
            costPoints: Number(costPoints),
            stock: Number(stock),
            status: Number(button.dataset.status || 0)
          }
        });
        toast("积分商品已更新", "success");
        await renderAdminRewards();
      } catch (error) {
        toast(error.message, "warning");
      }
    });
  });
}

function rewardPayload(data) {
  return {
    name: String(data.name || "").trim(),
    description: String(data.description || "").trim(),
    costPoints: Number(data.costPoints || 0),
    stock: Number(data.stock || 0),
    status: data.active === "on" ? 1 : 0
  };
}

function injectRewardCss() {
  if (document.querySelector("[data-reward-style]")) {
    return;
  }
  const style = document.createElement("style");
  style.dataset.rewardStyle = "true";
  style.textContent = `
    .reward-card { display: grid; gap: 12px; align-content: start; }
    .reward-card__image { width: 100%; max-width: 152px; height: 118px; object-fit: contain; justify-self: center; padding: 10px; border-radius: 22px; background: linear-gradient(180deg, rgba(0,117,184,.06), rgba(255,255,255,.8)); }
    .admin-reward-grid { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 14px; align-items: start; }
    .admin-reward-panel { border: 1px solid #d8e8f3; border-radius: 14px; background: #fff; padding: 14px; }
    .admin-reward-panel h2 { margin: 0 0 12px; color: #162636; font-size: 18px; }
    .admin-reward-metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 12px; }
    .admin-reward-metrics article { padding: 12px; border: 1px solid #edf3f8; border-radius: 12px; background: #f8fbfd; }
    .admin-reward-metrics span { display: block; color: #6b7a8c; font-size: 12px; }
    .admin-reward-metrics strong { display: block; margin-top: 4px; color: #162636; font: 800 24px/1 var(--font-mono); }
    .admin-reward-table-wrap { overflow: auto; }
    .admin-reward-table { width: 100%; min-width: 760px; border-collapse: collapse; }
    .admin-reward-table th { padding: 10px 12px; background: #f1f7fb; color: #607486; text-align: left; font-size: 12px; font-weight: 800; }
    .admin-reward-table td { padding: 10px 12px; border-top: 1px solid #edf3f8; color: #3d5168; font-size: 13px; vertical-align: middle; }
    .admin-reward-item { display: grid; grid-template-columns: 52px 1fr; gap: 10px; align-items: center; min-width: 260px; }
    .admin-reward-item img { width: 52px; height: 42px; object-fit: contain; border-radius: 10px; background: #eef7fc; }
    .admin-reward-item strong { display: block; color: #162636; }
    .admin-reward-item small { display: block; max-width: 360px; margin-top: 3px; color: #6b7a8c; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .status-pill--muted { color: #607486; background: #edf3f8; }
    .admin-reward-actions { display: flex; gap: 6px; }
    .admin-reward-actions button { border: 1px solid #c8ddeb; background: #fff; color: var(--brand); border-radius: 8px; padding: 6px 8px; cursor: pointer; font-weight: 800; font-size: 12px; }
    .admin-reward-actions button:last-child { background: #eef7fc; }
    .admin-reward-actions button:disabled { opacity: .5; cursor: progress; }
    .admin-reward-check { display: flex; align-items: center; gap: 8px; color: #3d5168; font-weight: 700; }
    @media (max-width: 980px) {
      .admin-reward-grid { grid-template-columns: 1fr; }
    }
  `;
  document.head.appendChild(style);
}
