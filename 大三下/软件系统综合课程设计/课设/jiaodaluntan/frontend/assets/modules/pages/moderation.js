// Content governance: pending post review queue and report queue handling.
import { apiRequest, pageContent } from "../api.js";
import { adminPageShell } from "../admin-layout.js";
import { escapeHtml, formatDate, requireAdmin, setMain, toast } from "../ui.js";

export async function renderModeration() {
  if (!requireAdmin()) {
    return;
  }
  const [pending, reports] = await Promise.all([
    apiRequest("/admin/posts/pending").then(pageContent),
    apiRequest("/admin/reports?status=0").then(pageContent)
  ]);
  setMain(adminPageShell(
    "moderation",
    "内容审核",
    "内容审核",
    "处理待审核的帖子和用户举报，保持社区氛围。",
    `
      <section class="section">
        <div class="container split-layout">
          <section class="surface-section stack">
            <h3 class="widget__title">待审核帖子</h3>
            ${pending.map((post) => `<article class="comment-card"><strong>${escapeHtml(post.title)}</strong><p class="muted">${escapeHtml(post.section?.name || "")} · ${escapeHtml(post.author?.username || "未知用户")}</p><div class="post-actions"><button class="button button--solid button--sm" data-post-status="${post.id}" data-status="1">通过</button><button class="button button--outline button--sm" data-post-status="${post.id}" data-status="3">驳回</button><button class="button button--outline button--sm" data-post-status="${post.id}" data-status="2">隐藏</button></div></article>`).join("") || '<p class="muted">没有待审核的帖子。</p>'}
          </section>
          <aside class="card"><h3 class="widget__title">举报队列</h3><div class="comment-list">${reports.map((report) => `<article class="comment-card"><strong>${escapeHtml(report.reason || "举报")}</strong><p class="muted">${escapeHtml(report.post?.title || "相关帖子")} · ${formatDate(report.createdAt)}</p><p class="muted">${escapeHtml(report.detail || "无补充说明")}</p><div class="post-actions"><button class="button button--solid button--sm" data-review-report="${report.id}" data-accept="true">采纳</button><button class="button button--outline button--sm" data-review-report="${report.id}" data-accept="false">驳回</button></div></article>`).join("") || '<p class="muted">暂无举报。</p>'}</div></aside>
        </div>
      </section>
    `
  ));
  document.querySelectorAll("[data-post-status]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await apiRequest(`/admin/posts/${button.dataset.postStatus}/status`, {
          method: "PATCH",
          body: { status: Number(button.dataset.status) }
        });
        toast("帖子状态已更新", "success");
        button.closest(".comment-card")?.remove();
      } catch (error) {
        toast(error.message, "warning");
      }
    });
  });
  document.querySelectorAll("[data-review-report]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await apiRequest(`/admin/reports/${button.dataset.reviewReport}/review`, {
          method: "PATCH",
          body: {
            accept: button.dataset.accept === "true",
            reviewNote: button.dataset.accept === "true" ? "后台审核采纳" : "后台审核驳回"
          }
        });
        toast(button.dataset.accept === "true" ? "举报已采纳" : "举报已驳回", "success");
        button.closest(".comment-card")?.remove();
      } catch (error) {
        toast(error.message, "warning");
      }
    });
  });
}
