// User & section management: ban/unban accounts and CRUD forum sections.
import { apiRequest, fetchSections, invalidateSectionsCache, pageContent } from "../api.js";
import { adminPageShell } from "../admin-layout.js";
import { escapeHtml, formValues, requireAdmin, setMain, toast } from "../ui.js";

export async function renderUsers() {
  if (!requireAdmin()) {
    return;
  }
  const [users, sections] = await Promise.all([
    apiRequest("/admin/users").then(pageContent),
    fetchSections()
  ]);
  setMain(adminPageShell(
    "users",
    "用户与版块",
    "用户与版块管理",
    "管理注册用户的状态，维护论坛的版块结构。",
    `
      <section class="section">
        <div class="container split-layout">
          <section class="surface-section">
            <table class="table table--compact">
              <thead><tr><th>用户</th><th>角色</th><th>状态</th><th>操作</th></tr></thead>
              <tbody>${users.map((user) => `<tr><td>${escapeHtml(user.username)}</td><td>${escapeHtml(user.role)}</td><td>${user.enabled ? '<span class="status-pill status-pill--ok">正常</span>' : '<span class="status-pill status-pill--danger">封禁</span>'}</td><td><button class="button button--outline button--sm" data-toggle-user="${user.id}" data-enabled="${user.enabled}">${user.enabled ? "封禁" : "解封"}</button></td></tr>`).join("") || '<tr><td colspan="4">暂无用户。</td></tr>'}</tbody>
            </table>
          </section>
          <aside class="stack">
            <section class="card">
              <h3 class="widget__title">创建版块</h3>
              <form class="quick-form" data-section-form>
                <div class="field"><label>版块名称</label><input class="input" name="name" required maxlength="50" placeholder="例如：竞赛组队" /></div>
                <div class="field"><label>版块描述</label><textarea class="textarea" name="description" maxlength="200" placeholder="说明这个版块讨论什么。"></textarea></div>
                <div class="field"><label>排序</label><input class="input" name="sortOrder" type="number" value="0" /></div>
                <button class="button button--solid" type="submit">创建版块</button>
              </form>
            </section>
            <section class="card">
              <h3 class="widget__title">现有版块</h3>
              <div class="comment-list">
                ${sections.map((section) => `<article class="comment-card"><strong>${escapeHtml(section.name)}</strong><p class="muted">${escapeHtml(section.description || "暂无描述")} · ${section.postCount || 0} 帖</p><div class="post-actions"><button class="button button--outline button--sm" data-edit-section="${section.id}" data-name="${escapeHtml(section.name)}" data-description="${escapeHtml(section.description || "")}" data-sort-order="${section.sortOrder || 0}">编辑</button><button class="button button--outline button--sm" data-delete-section="${section.id}">删除</button></div></article>`).join("") || '<p class="muted">暂无版块。</p>'}
              </div>
            </section>
          </aside>
        </div>
      </section>
    `
  ));
  document.querySelectorAll("[data-toggle-user]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        const endpoint = button.dataset.enabled === "true" ? "ban" : "unban";
        await apiRequest(`/admin/users/${button.dataset.toggleUser}/${endpoint}`, { method: "PATCH" });
        toast("用户状态已更新", "success");
        button.disabled = true;
      } catch (error) {
        toast(error.message, "warning");
      }
    });
  });
  document.querySelector("[data-section-form]")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = formValues(event.currentTarget);
    try {
      await apiRequest("/admin/sections", {
        method: "POST",
        body: {
          name: String(data.name || "").trim(),
          description: String(data.description || "").trim() || null,
          sortOrder: Number(data.sortOrder || 0),
          moderatorId: null
        }
      });
      invalidateSectionsCache();
      toast("版块已创建", "success");
      event.currentTarget.reset();
    } catch (error) {
      toast(error.message, "warning");
    }
  });
  document.querySelectorAll("[data-delete-section]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await apiRequest(`/admin/sections/${button.dataset.deleteSection}`, { method: "DELETE" });
        invalidateSectionsCache();
        toast("版块已删除", "success");
        button.closest(".comment-card")?.remove();
      } catch (error) {
        toast(error.message, "warning");
      }
    });
  });
  document.querySelectorAll("[data-edit-section]").forEach((button) => {
    button.addEventListener("click", async () => {
      const name = window.prompt("请输入新版块名称", button.dataset.name || "");
      if (!name) {
        return;
      }
      const description = window.prompt("请输入新版块描述", button.dataset.description || "") || "";
      try {
        await apiRequest(`/admin/sections/${button.dataset.editSection}`, {
          method: "PUT",
          body: {
            name: name.trim(),
            description: description.trim() || null,
            sortOrder: Number(button.dataset.sortOrder || 0),
            moderatorId: null
          }
        });
        invalidateSectionsCache();
        toast("版块已更新", "success");
        const card = button.closest(".comment-card");
        const title = card?.querySelector("strong");
        if (title) {
          title.textContent = name.trim();
        }
        button.dataset.name = name.trim();
        button.dataset.description = description.trim();
      } catch (error) {
        toast(error.message, "warning");
      }
    });
  });
}
