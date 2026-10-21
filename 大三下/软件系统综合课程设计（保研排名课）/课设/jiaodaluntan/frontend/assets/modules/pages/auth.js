// Auth page: login / register tabs and session reset.
import { apiRequest } from "../api.js";
import { ROUTES } from "../constants.js";
import { clearSession, persistSession, state } from "../session.js";
import { formValues, isAdminRoute, setMain, toast } from "../ui.js";

export function renderAuth() {
  const next = new URLSearchParams(location.search).get("next") || ROUTES.home;
  const wantsAdmin = new URLSearchParams(location.search).get("admin") === "1";
  const isAdminDestination = isAdminRoute(next);
  const wantsCreate = next.includes(ROUTES.create);

  if (state.token && state.user) {
    location.href = !isAdminDestination || state.user.role === "ADMIN" ? next : ROUTES.home;
    return;
  }

  setMain(`
    <section class="hero">
      <div class="container split-layout">
        <section class="band stack">
          <h1 class="hero__title" style="color: white; font-size: clamp(34px, 5vw, 52px);">${wantsAdmin ? "管理员登录" : wantsCreate ? "登录后继续发帖" : "加入交大社区，<br/>和同学聊起来。"}</h1>
          <p class="band__body">${wantsAdmin ? "后台仅面向具有管理权限的账号开放。普通用户可返回论坛首页继续浏览、发帖和评论。" : wantsCreate ? "发帖、评论、收藏和签到需要登录。注册或登录成功后，系统会自动回到发帖页。" : "登录后就能发帖、评论、收藏、签到攒积分。课程互助、保研考研、实习就业、犀浦生活，话题一直在更新。"}</p>
          <ul class="bullet-list" style="color: rgba(255,255,255,0.86)">
            <li>真实校园话题，按热度推荐</li>
            <li>签到成长，积分兑换好礼</li>
            <li>失物招领、二手闲置，校内互助</li>
          </ul>
        </section>
        <section class="surface-section stack">
          <div class="toolbar-space">
            <h2 class="post-card__title">${wantsAdmin ? "验证账号权限" : wantsCreate ? "先完成登录或注册" : "欢迎回来"}</h2>
            <div class="inline-tags">
              <button class="button button--outline button--sm" data-tab="login">登录</button>
              ${wantsAdmin ? "" : '<button class="button button--outline button--sm" data-tab="register">注册</button>'}
            </div>
          </div>
          <div data-auth-panel></div>
        </section>
      </div>
    </section>
  `);

  const panel = document.querySelector("[data-auth-panel]");
  const delegatedSubmit = (event) => {
    const button = event.target instanceof Element ? event.target.closest("[data-auth-submit]") : null;
    if (!button || !panel.contains(button)) {
      return;
    }
    submitAuthForm(button.closest("[data-auth-form]"), next, event);
  };
  panel.addEventListener("pointerdown", delegatedSubmit);
  panel.addEventListener("click", delegatedSubmit);

  const draw = (mode) => {
    panel.innerHTML = mode === "register" ? `
      <form class="quick-form" data-auth-form="register">
        <div class="field"><label>用户名</label><input class="input" name="username" required minlength="3" placeholder="例如 swjtu_student" /></div>
        <div class="field"><label>邮箱</label><input class="input" name="email" type="email" required placeholder="name@swjtu.edu.cn" /></div>
        <div class="field"><label>密码</label><input class="input" name="password" type="password" required minlength="6" placeholder="至少 6 位" /></div>
        <div class="duo-grid">
          <div class="field"><label>学号</label><input class="input" name="studentId" placeholder="可选" /></div>
          <div class="field"><label>学院</label><input class="input" name="college" placeholder="可选" /></div>
        </div>
        <div class="field"><label>专业</label><input class="input" name="major" placeholder="可选" /></div>
        <button class="button button--solid" type="submit" data-auth-submit>注册并进入论坛</button>
      </form>
    ` : `
      <form class="quick-form" data-auth-form="login">
        <div class="field"><label>用户名</label><input class="input" name="username" required placeholder="请输入用户名" /></div>
        <div class="field"><label>密码</label><input class="input" name="password" type="password" required placeholder="请输入密码" /></div>
        <button class="button button--solid" type="submit" data-auth-submit>登录进入论坛</button>
      </form>
    `;
    bindAuthForm(next);
  };

  document.querySelectorAll("[data-tab]").forEach((button) => {
    button.addEventListener("click", () => draw(button.dataset.tab));
  });
  draw(new URLSearchParams(location.search).get("mode") === "register" || wantsCreate ? "register" : "login");

  document.querySelector("[data-auth-panel]")?.insertAdjacentHTML("afterend", `
    <p class="muted" style="font-size:13px;margin:4px 0 0">
      <a class="button button--ghost button--sm" href="${ROUTES.home}">返回论坛首页</a>
      <button class="button button--sm" type="button" data-clear-session style="color:var(--muted)">清除登录状态</button>
    </p>
  `);
  document.querySelector("[data-clear-session]")?.addEventListener("click", () => {
    clearSession();
    toast("旧登录态已清除，请重新登录", "success");
    draw("login");
  });
  if (wantsAdmin) {
    draw("login");
  }
}

function bindAuthForm(next) {
  const form = document.querySelector("[data-auth-form]");
  if (!form) {
    return;
  }

  form.addEventListener("submit", (event) => submitAuthForm(form, next, event));
  const submitButton = form.querySelector("[data-auth-submit]");
  submitButton?.addEventListener("pointerdown", (event) => submitAuthForm(form, next, event));
  submitButton?.addEventListener("click", (event) => submitAuthForm(form, next, event));
}

async function submitAuthForm(form, next, event) {
  event.preventDefault();
  if (!form || form.dataset.submitting === "true") {
    return;
  }
  if (typeof form.reportValidity === "function" && !form.reportValidity()) {
    return;
  }
  form.dataset.submitting = "true";
  const submitButton = form.querySelector("[data-auth-submit]");
  if (submitButton) {
    submitButton.disabled = true;
    submitButton.textContent = "处理中...";
  }
  const mode = form.dataset.authForm;
  const data = formValues(form);
  try {
    const result = await apiRequest(mode === "register" ? "/auth/register" : "/auth/login", {
      method: "POST",
      auth: false,
      body: {
        username: String(data.username || "").trim(),
        password: String(data.password || "").trim(),
        email: data.email ? String(data.email).trim() : undefined,
        studentId: data.studentId ? String(data.studentId).trim() : null,
        college: data.college ? String(data.college).trim() : null,
        major: data.major ? String(data.major).trim() : null
      }
    });
    persistSession(result);
    toast(mode === "register" ? "注册成功，已自动登录" : "登录成功", "success");
    const isAdminDestination = isAdminRoute(next);
    const canEnterDestination = !isAdminDestination || result.user?.role === "ADMIN";
    location.href = canEnterDestination ? next : ROUTES.home;
  } catch (error) {
    toast(error.message, "warning");
    form.dataset.submitting = "false";
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = mode === "register" ? "注册并进入论坛" : "登录进入论坛";
    }
  }
}
