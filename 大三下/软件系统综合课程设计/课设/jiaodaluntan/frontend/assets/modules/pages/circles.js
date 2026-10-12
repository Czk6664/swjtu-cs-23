// Campus circles: browse, create, join/leave, and read circle posts.
import { apiRequest, pageContent } from "../api.js";
import { ROUTES } from "../constants.js";
import { state } from "../session.js";
import {
  escapeHtml,
  formValues,
  loginHref,
  pageShell,
  postCard,
  setMain,
  toast
} from "../ui.js";
import { circleAsset, emptyAsset } from "../visual-assets.js";

function circleCard(circle, activeId = "") {
  const id = String(circle.id);
  const active = id === String(activeId);
  return `
    <article class="circle-card ${active ? "circle-card--active" : ""}" data-circle-card="${escapeHtml(id)}">
      <a href="${ROUTES.circles}?id=${encodeURIComponent(id)}" class="circle-card__main" data-circle-link="${escapeHtml(id)}">
        <span class="circle-card__icon"><img src="${circleAsset(circle.name)}" alt="" loading="lazy" /></span>
        <span>
          <strong>${escapeHtml(circle.name)}</strong>
          <small>${escapeHtml(circle.description || "")}</small>
        </span>
      </a>
      <div class="circle-card__meta">
        <span><span data-circle-card-members="${escapeHtml(id)}">${Number(circle.memberCount) || 0}</span> 成员</span>
        <span>${Number(circle.postCount) || 0} 帖子</span>
        ${circle.joined ? '<span class="status-pill status-pill--ok" data-circle-joined-pill>已加入</span>' : ""}
      </div>
    </article>
  `;
}

function createCircleAction() {
  if (!state.user) {
    return `<a class="button button--outline button--sm" href="${loginHref(ROUTES.circles)}">登录后创建</a>`;
  }
  return `<button class="button button--solid button--sm" type="button" data-circle-modal-open>+ 创建圈子</button>`;
}

function createCircleForm() {
  if (!state.user) {
    return `
      <section class="card card--quiet">
        <div class="label">创建圈子</div>
        <p class="muted">登录后可以创建新的校园兴趣圈子。</p>
        <a class="button button--solid button--sm" href="${loginHref(ROUTES.circles)}">登录后创建</a>
      </section>
    `;
  }
  return `
    <section class="card card--quiet">
      <div class="label">创建圈子</div>
      <form class="quick-form" data-circle-create-form>
        <div class="field"><label>圈子名称</label><input class="input" name="name" maxlength="80" required placeholder="例如：土木考研互助圈" /></div>
        <div class="field"><label>图标字</label><input class="input" name="icon" maxlength="4" placeholder="研" /></div>
        <div class="field"><label>简介</label><textarea class="textarea" name="description" maxlength="500" required placeholder="说明这个圈子适合哪些同学、讨论什么内容。"></textarea></div>
        <button class="button button--solid" type="submit">创建圈子</button>
      </form>
    </section>
  `;
}

function createCircleModal() {
  if (!state.user) {
    return "";
  }
  return `
    <div class="circle-modal" data-circle-modal hidden>
      <button class="circle-modal__backdrop" type="button" data-circle-modal-close aria-label="关闭创建圈子弹窗"></button>
      <section class="circle-modal__panel" role="dialog" aria-modal="true" aria-labelledby="circle-create-title">
        <div class="toolbar-space">
          <div>
            <div class="label">创建圈子</div>
            <h3 class="widget__title" id="circle-create-title">发起一个新的校园圈子</h3>
          </div>
          <button class="icon-btn" type="button" data-circle-modal-close aria-label="关闭">×</button>
        </div>
        <p class="muted">圈子适合承载课程互助、考研资料、犀浦生活、社团招新等长期话题。</p>
        <form class="quick-form" data-circle-create-form>
          <div class="field"><label>圈子名称</label><input class="input" name="name" maxlength="80" required placeholder="例如：土木考研互助圈" /></div>
          <div class="field"><label>图标字</label><input class="input" name="icon" maxlength="4" placeholder="研" /></div>
          <div class="field"><label>简介</label><textarea class="textarea" name="description" maxlength="500" required placeholder="说明这个圈子适合哪些同学、讨论什么内容。"></textarea></div>
          <div class="post-actions">
            <button class="button button--solid" type="submit">创建圈子</button>
            <button class="button button--outline" type="button" data-circle-modal-close>取消</button>
          </div>
        </form>
      </section>
    </div>
  `;
}

export async function renderCircles() {
  const params = new URLSearchParams(location.search);
  const activeId = params.get("id");
  const [circles, detail, posts] = await Promise.all([
    apiRequest("/circles", { auth: false }),
    activeId ? apiRequest(`/circles/${activeId}`, { auth: false }) : Promise.resolve(null),
    activeId ? apiRequest(`/circles/${activeId}/posts`, { auth: false }).then(pageContent) : Promise.resolve([])
  ]);

  const selected = detail || circles[0] || null;
  const selectedId = selected?.id ? String(selected.id) : "";
  const body = `
    <section class="section">
      <div class="container split-layout">
        <aside class="stack">
          <section class="card">
            <div class="label">校园圈子</div>
            <div class="circle-action-row">${createCircleAction()}</div>
            <div class="circle-list">${circles.map((circle) => circleCard(circle, selectedId)).join("")}</div>
          </section>
          ${createCircleModal()}
        </aside>
        <section class="surface-section stack">
          ${selected ? `
            <div class="toolbar-space">
              <div class="circle-hero">
                <span class="circle-card__icon circle-card__icon--xl"><img src="${circleAsset(selected.name)}" alt="" /></span>
                <div>
                  <div class="label">圈子详情</div>
                  <h2 class="post-card__title">${escapeHtml(selected.name)}</h2>
                  <p class="muted">${escapeHtml(selected.description || "")}</p>
                </div>
              </div>
              ${state.user
                ? `<button class="button ${selected.joined ? "button--outline" : "button--solid"}" data-circle-toggle="${selectedId}" data-joined="${selected.joined ? "1" : "0"}">${selected.joined ? "退出圈子" : "加入圈子"}</button>`
                : `<a class="button button--solid" href="${loginHref(`${ROUTES.circles}?id=${selectedId}`)}">登录后加入</a>`}
            </div>
            <div class="post-actions">
              <a class="button button--outline button--sm" href="${ROUTES.create}?circleId=${selectedId}">在圈子发帖</a>
              <span class="muted"><span data-circle-member-count>${Number(selected.memberCount) || 0}</span> 成员 · ${Number(selected.postCount) || 0} 帖子</span>
            </div>
            <div class="stack">
              ${posts.length ? posts.map(postCard).join("") : `<article class="comment-card empty-inline"><img src="${emptyAsset("posts")}" alt="" /><p class="muted">这个圈子还没有公开帖子，来发第一帖吧。</p></article>`}
            </div>
          ` : '<article class="comment-card"><p class="muted">暂无圈子。</p></article>'}
        </section>
      </div>
    </section>
  `;

  setMain(pageShell(
    "校园圈子",
    "按兴趣聚在一起",
    "课程、考研、犀浦生活、就业和二手失物都可以有自己的小圈子。",
    body
  ));
  injectCircleCss();
  bindCircleActions();
}

function bindCircleActions() {
  const modal = document.querySelector("[data-circle-modal]");
  const firstModalField = modal?.querySelector("input[name='name']");
  const closeModal = () => {
    if (!modal) {
      return;
    }
    modal.hidden = true;
    document.body.classList.remove("modal-open");
    document.removeEventListener("keydown", onModalKeydown);
  };
  const onModalKeydown = (event) => {
    if (event.key === "Escape") {
      closeModal();
    }
  };
  document.querySelector("[data-circle-modal-open]")?.addEventListener("click", () => {
    if (!modal) {
      return;
    }
    modal.hidden = false;
    document.body.classList.add("modal-open");
    document.addEventListener("keydown", onModalKeydown);
    setTimeout(() => firstModalField?.focus(), 0);
  });
  document.querySelectorAll("[data-circle-modal-close]").forEach((button) => {
    button.addEventListener("click", closeModal);
  });

  document.querySelectorAll("[data-circle-link]").forEach((link) => {
    link.addEventListener("click", async (event) => {
      event.preventDefault();
      const id = link.dataset.circleLink;
      history.pushState({ page: "circles", id }, "", `${ROUTES.circles}?id=${encodeURIComponent(id)}`);
      await renderCircles();
    });
  });

  document.querySelector("[data-circle-toggle]")?.addEventListener("click", async (event) => {
    const button = event.currentTarget;
    const joined = button.dataset.joined === "1";
    try {
      await apiRequest(`/circles/${button.dataset.circleToggle}/join`, {
        method: joined ? "DELETE" : "POST"
      });
      const nextJoined = !joined;
      const delta = nextJoined ? 1 : -1;
      const circleId = button.dataset.circleToggle;
      button.dataset.joined = nextJoined ? "1" : "0";
      button.textContent = nextJoined ? "退出圈子" : "加入圈子";
      button.classList.toggle("button--outline", nextJoined);
      button.classList.toggle("button--solid", !nextJoined);
      document.querySelectorAll(`[data-circle-card-members="${circleId}"]`).forEach((node) => {
        node.textContent = String(Math.max(0, Number(node.textContent || 0) + delta));
      });
      document.querySelectorAll("[data-circle-member-count]").forEach((node) => {
        node.textContent = String(Math.max(0, Number(node.textContent || 0) + delta));
      });
      const meta = document.querySelector(`[data-circle-card="${circleId}"] .circle-card__meta`);
      const joinedPill = meta?.querySelector("[data-circle-joined-pill]");
      if (nextJoined && meta && !joinedPill) {
        meta.insertAdjacentHTML("beforeend", '<span class="status-pill status-pill--ok" data-circle-joined-pill>已加入</span>');
      } else if (!nextJoined) {
        joinedPill?.remove();
      }
      toast(nextJoined ? "已加入圈子" : "已退出圈子", "success");
    } catch (error) {
      toast(error.message, "warning");
    }
  });

  document.querySelector("[data-circle-create-form]")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = formValues(event.currentTarget);
    try {
      const circle = await apiRequest("/circles", {
        method: "POST",
        body: {
          name: String(data.name || "").trim(),
          icon: String(data.icon || "").trim() || "社",
          description: String(data.description || "").trim()
        }
      });
      toast("圈子创建成功", "success");
      history.pushState({ page: "circles", id: circle.id }, "", `${ROUTES.circles}?id=${circle.id}`);
      await renderCircles();
    } catch (error) {
      toast(error.message, "warning");
    }
  });
}

function injectCircleCss() {
  if (document.querySelector("[data-circle-style]")) {
    return;
  }
  const style = document.createElement("style");
  style.dataset.circleStyle = "true";
  style.textContent = `
    .circle-list { display: grid; gap: 10px; }
    .circle-card { padding: 12px; border-radius: var(--radius-md); border: 1px solid rgba(0,117,184,.12); background: var(--surface); }
    .circle-card--active { border-color: rgba(0,117,184,.35); box-shadow: 0 12px 28px rgba(0,117,184,.1); }
    .circle-card__main { display: grid; grid-template-columns: auto 1fr; gap: 10px; align-items: center; color: inherit; text-decoration: none; }
    .circle-card__icon { width: 42px; height: 42px; border-radius: 16px; display: grid; place-items: center; background: rgba(0,117,184,.08); color: #fff; font-weight: 900; overflow: hidden; }
    .circle-card__icon img { width: 34px; height: 34px; object-fit: contain; display: block; }
    .circle-card__icon--xl { width: 58px; height: 58px; border-radius: 20px; font-size: 22px; }
    .circle-card__icon--xl img { width: 50px; height: 50px; }
    .circle-card strong { display: block; color: var(--ink); }
    .circle-card small { display: block; margin-top: 3px; color: var(--muted); line-height: 1.45; }
    .circle-card__meta { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 10px; color: var(--muted); font-size: 12px; }
    .circle-hero { display: flex; align-items: center; gap: 14px; }
    .circle-action-row { display: flex; justify-content: flex-end; margin: 10px 0 12px; }
    .empty-inline { display: grid; grid-template-columns: auto 1fr; align-items: center; gap: 14px; }
    .empty-inline img { width: 88px; height: 88px; object-fit: contain; }
    .circle-modal[hidden] { display: none !important; }
    .circle-modal { position: fixed; inset: 0; z-index: 90; display: grid; place-items: center; padding: 20px; }
    .circle-modal__backdrop { position: absolute; inset: 0; border: 0; background: rgba(9, 35, 56, .42); backdrop-filter: blur(8px); cursor: pointer; }
    .circle-modal__panel { position: relative; z-index: 1; width: min(520px, calc(100vw - 32px)); max-height: calc(100vh - 48px); overflow: auto; padding: 22px; border-radius: var(--radius-lg); border: 1px solid var(--border-strong); background: var(--surface); box-shadow: var(--shadow-float); }
    body.modal-open { overflow: hidden; }
  `;
  document.head.appendChild(style);
}
