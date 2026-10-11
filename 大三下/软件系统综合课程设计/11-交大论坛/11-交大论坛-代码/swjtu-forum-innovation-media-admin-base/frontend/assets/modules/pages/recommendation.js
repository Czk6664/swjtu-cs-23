// Recommendation strategy: tune weights and preview ranked posts.
import { apiRequest } from "../api.js";
import { adminPageShell } from "../admin-layout.js";
import { escapeHtml, formValues, requireAdmin, setMain, toast } from "../ui.js";

export async function renderRecommendation() {
  if (!requireAdmin()) {
    return;
  }
  const [config, preview] = await Promise.all([
    apiRequest("/admin/recommendations/config"),
    apiRequest("/admin/recommendations/preview")
  ]);
  const weightFields = [
    { name: "tagWeight", label: "标签匹配权重" },
    { name: "engagementWeight", label: "互动热度权重" },
    { name: "recencyWeight", label: "时间新鲜度权重" }
  ];
  setMain(adminPageShell(
    "recommendation",
    "推荐策略",
    "推荐策略",
    "调整各项权重，决定首页热门帖子的排序逻辑，右侧可实时预览效果。",
    `
      <section class="section">
        <div class="container split-layout">
          <section class="surface-section stack">
            <form class="quick-form" data-rec-form>
              ${weightFields.map((f) => `<div class="field"><label>${f.label}</label><input class="input" name="${f.name}" type="number" min="0" max="100" value="${config[f.name]}" /></div>`).join("")}
              <label style="display:flex;align-items:center;gap:8px"><input type="checkbox" name="explainabilityEnabled" ${config.explainabilityEnabled ? "checked" : ""} /> 在帖子上显示推荐理由</label>
              <button class="button button--solid" type="submit">保存策略</button>
            </form>
          </section>
          <aside class="card"><h3 class="widget__title">推荐预览</h3><div class="rank-list">${(preview.posts || []).map((post) => `<div class="rank-item"><span class="rank-item__no"></span><span class="rank-item__title">${escapeHtml(post.title)}</span></div>`).join("") || '<p class="muted">暂无预览数据。</p>'}</div></aside>
        </div>
      </section>
    `
  ));
  document.querySelector("[data-rec-form]")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = formValues(event.currentTarget);
    try {
      await apiRequest("/admin/recommendations/config", {
        method: "PUT",
        body: {
          tagWeight: Number(data.tagWeight || 0),
          engagementWeight: Number(data.engagementWeight || 0),
          recencyWeight: Number(data.recencyWeight || 0),
          explainabilityEnabled: data.explainabilityEnabled === "on"
        }
      });
      toast("推荐策略已保存", "success");
    } catch (error) {
      toast(error.message, "warning");
    }
  });
}
