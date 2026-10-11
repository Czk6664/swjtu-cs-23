// Authenticated writing flow: create, edit, pending-review feedback, withdrawal.
import { apiRequest, fetchSections } from "../api.js";
import { ROUTES, STORAGE_KEYS } from "../constants.js";
import { state } from "../session.js";
import { buttonLoading, buttonReset, publishFlowEnter } from "../motion.js";
import {
  escapeHtml,
  formValues,
  pageShell,
  postStatusClass,
  postStatusLabel,
  requireLogin,
  setMain,
  stateCard,
  toast,
  uploadUrl
} from "../ui.js";

const POST_TEMPLATES = [
  {
    keywords: ["课程", "学习", "学业", "作业"],
    content: `【课程 / 科目】
【遇到的问题】
【已经尝试过的方法】
【希望得到的帮助】
【补充资料或截图】`
  },
  {
    keywords: ["二手", "闲置", "交易"],
    content: `【物品名称】
【新旧程度】
【价格】
【交易地点】
【联系方式】
【补充说明】`
  },
  {
    keywords: ["失物", "招领", "寻物"],
    content: `【物品名称】
【丢失 / 拾到时间】
【地点】
【物品特征】
【联系方式】
【备注】`
  },
  {
    keywords: ["考研", "保研", "升学"],
    content: `【方向 / 院校】
【当前阶段】
【想交流的问题】
【已有资料或经验】
【希望组队或求助内容】`
  },
  {
    keywords: ["实习", "就业", "招聘", "求职"],
    content: `【岗位 / 方向】
【公司 / 地点】
【信息来源】
【适合人群】
【投递方式】
【补充说明】`
  }
];

function templateForSection(sectionName = "") {
  return POST_TEMPLATES.find((template) =>
    template.keywords.some((keyword) => String(sectionName).includes(keyword))
  )?.content || "";
}

export async function renderCreate() {
  if (!requireLogin()) {
    return;
  }
  const editId = new URLSearchParams(location.search).get("edit");
  const circleId = new URLSearchParams(location.search).get("circleId");
  const [sections, circles, editingPost] = await Promise.all([
    fetchSections(),
    apiRequest("/circles", { auth: false }).catch(() => []),
    editId ? apiRequest(`/posts/mine/${editId}`) : Promise.resolve(null)
  ]);
  const initialPost = editingPost ? {
    title: editingPost.title || "",
    sectionId: editingPost.section?.id || editingPost.sectionId || "",
    circleId: editingPost.circle?.id || editingPost.circleId || "",
    tags: (editingPost.tags || []).map((tag) => tag.name || tag).join(", "),
    coverImage: editingPost.coverImage || "",
    imageUrls: Array.isArray(editingPost.imageUrls) ? editingPost.imageUrls : [],
    content: editingPost.content || ""
  } : { ...state.draft, circleId: circleId || state.draft?.circleId || "" };
  const initialImageUrls = (Array.isArray(initialPost.imageUrls) && initialPost.imageUrls.length
    ? initialPost.imageUrls
    : [initialPost.coverImage]
  ).map(uploadUrl).filter(Boolean).slice(0, 9);
  setMain(pageShell(
    editId ? "编辑帖子" : "发布帖子",
    editId ? "编辑我的帖子" : "发布新帖",
    editId ? "修改内容后重新发布，含敏感词的修改会重新进入审核。" : "分享你的问题、经验或资料，让更多交大同学看到。",
    `
      <section class="section">
        <div class="container split-layout">
          <section class="surface-section stack">
            <form class="quick-form" data-create-form>
              ${editId ? `<span class="${postStatusClass(editingPost.status)}">${postStatusLabel(editingPost.status)}</span>` : ""}
              <div class="field"><label>标题</label><input class="input" name="title" required maxlength="200" value="${escapeHtml(initialPost.title || "")}" placeholder="例如：数据结构期末复习资料怎么整理？" /></div>
              <div class="field"><label>版块</label><select class="select" name="sectionId" required>${sections.map((section) => `<option value="${section.id}" ${String(initialPost.sectionId || "") === String(section.id) ? "selected" : ""}>${escapeHtml(section.name)}</option>`).join("")}</select></div>
              <div class="field"><label>发布到圈子（可选）</label><select class="select" name="circleId"><option value="">不选择圈子</option>${circles.map((circle) => `<option value="${circle.id}" ${String(initialPost.circleId || "") === String(circle.id) ? "selected" : ""}>${escapeHtml(circle.name)}</option>`).join("")}</select></div>
              <div class="field"><label>标签</label><input class="input" name="tags" value="${escapeHtml(initialPost.tags || "")}" placeholder="课程互助, 期末复习" /></div>
              <div class="field">
                <label>帖子图片（可选）</label>
                <div class="post-image-upload" data-post-image-upload>
                  <div class="post-image-upload__preview" data-post-image-preview>
                    ${initialImageUrls.length
                      ? initialImageUrls.map((url, index) => `
                        <figure class="post-image-upload__item">
                          <img src="${escapeHtml(url)}" alt="帖子图片预览 ${index + 1}" />
                          <button type="button" class="post-image-upload__remove" data-post-image-remove="${index}" aria-label="移除第 ${index + 1} 张图片">×</button>
                        </figure>
                      `).join("")
                      : '<span class="post-image-upload__empty">可上传课堂截图、校园照片或资料预览图</span>'}
                  </div>
                  <div class="post-image-upload__actions">
                    <input type="file" accept="image/png,image/jpeg" data-post-image-input multiple hidden />
                    <input type="hidden" name="imageUrls" value="${escapeHtml(JSON.stringify(initialImageUrls))}" data-post-image-urls />
                    <button type="button" class="button button--outline button--sm" data-post-image-button>选择图片</button>
                    <button type="button" class="button button--ghost button--sm" data-post-image-clear ${initialImageUrls.length ? "" : "hidden"}>清空图片</button>
                  </div>
                  <p class="muted post-image-upload__hint">支持 PNG、JPG，最多 9 张，单张不超过 8MB。</p>
                </div>
              </div>
              <div class="field"><label>正文</label><textarea class="textarea" name="content" required maxlength="10000" placeholder="写下你的问题、经验或资料说明。">${escapeHtml(initialPost.content || "")}</textarea></div>
              <div class="post-actions">
                <button class="button button--solid" type="submit">${editId ? "更新帖子" : "发布帖子"}</button>
                ${editId ? `<button class="button button--outline" type="button" data-withdraw-post="${editId}">撤回帖子</button>` : '<button class="button button--outline" type="button" data-save-draft>保存草稿</button>'}
              </div>
            </form>
          </section>
          <aside class="stack">
            <section class="card card--quiet">
              <div class="label">发帖规则</div>
              <p class="muted">正常内容会直接发布；包含明显风险词的内容会进入待审核队列。撤回帖子不会物理删除数据，只会从公开列表隐藏。</p>
            </section>
          </aside>
        </div>
      </section>
    `
  ));

  const form = document.querySelector("[data-create-form]");
  const sectionSelect = form?.querySelector('[name="sectionId"]');
  const contentField = form?.querySelector('[name="content"]');
  let lastAppliedTemplate = templateForSection(sections.find((section) =>
    String(section.id) === String(initialPost.sectionId || sectionSelect?.value || "")
  )?.name);

  const applySectionTemplate = () => {
    if (editId || !sectionSelect || !contentField) {
      return;
    }
    const selectedSection = sections.find((section) => String(section.id) === String(sectionSelect.value));
    const nextTemplate = templateForSection(selectedSection?.name);
    if (!nextTemplate) {
      return;
    }
    const current = String(contentField.value || "").trim();
    const canReplace = !current || current === lastAppliedTemplate.trim();
    if (!canReplace) {
      toast("已保留你手写的正文，未自动覆盖模板。", "info");
      return;
    }
    contentField.value = nextTemplate;
    lastAppliedTemplate = nextTemplate;
  };
  sectionSelect?.addEventListener("change", applySectionTemplate);
  applySectionTemplate();

  const imageInput = document.querySelector("[data-post-image-input]");
  const imageButton = document.querySelector("[data-post-image-button]");
  const imagePreview = document.querySelector("[data-post-image-preview]");
  const imageUrlsInput = document.querySelector("[data-post-image-urls]");
  const imageClear = document.querySelector("[data-post-image-clear]");
  let postImageUrls = [...initialImageUrls];
  const syncImageInput = () => {
    if (imageUrlsInput) {
      imageUrlsInput.value = JSON.stringify(postImageUrls);
    }
  };
  const renderImages = () => {
    if (imagePreview) {
      imagePreview.innerHTML = postImageUrls.length
        ? postImageUrls.map((url, index) => `
          <figure class="post-image-upload__item">
            <img src="${escapeHtml(uploadUrl(url))}" alt="帖子图片预览 ${index + 1}" />
            <button type="button" class="post-image-upload__remove" data-post-image-remove="${index}" aria-label="移除第 ${index + 1} 张图片">×</button>
          </figure>
        `).join("")
        : '<span class="post-image-upload__empty">可上传课堂截图、校园照片或资料预览图</span>';
    }
    if (imageClear) {
      imageClear.hidden = postImageUrls.length === 0;
    }
    syncImageInput();
  };
  renderImages();
  imageButton?.addEventListener("click", () => imageInput?.click());
  imageClear?.addEventListener("click", () => {
    if (imageInput) {
      imageInput.value = "";
    }
    postImageUrls = [];
    renderImages();
  });
  imagePreview?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-post-image-remove]");
    if (!button) {
      return;
    }
    postImageUrls.splice(Number(button.dataset.postImageRemove), 1);
    renderImages();
  });
  imageInput?.addEventListener("change", async () => {
    const files = Array.from(imageInput.files || []);
    if (!files.length) {
      return;
    }
    const remaining = 9 - postImageUrls.length;
    if (remaining <= 0) {
      toast("最多只能上传 9 张图片", "warning");
      imageInput.value = "";
      return;
    }
    if (files.length > remaining) {
      toast(`最多还能上传 ${remaining} 张图片，已自动忽略多余图片。`, "info");
    }
    const selectedFiles = files.slice(0, remaining);
    const invalid = selectedFiles.find((file) => !["image/png", "image/jpeg", "image/jpg"].includes(file.type));
    if (invalid) {
      toast("帖子图片仅支持 PNG、JPG", "warning");
      imageInput.value = "";
      return;
    }
    if (selectedFiles.some((file) => file.size > 8 * 1024 * 1024)) {
      toast("单张图片大小不能超过 8MB", "warning");
      imageInput.value = "";
      return;
    }
    try {
      imageButton.disabled = true;
      imageButton.textContent = "上传中";
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append("file", file);
        const resp = await fetch("/api/posts/image", {
          method: "POST",
          headers: { "Authorization": `Bearer ${state.token}` },
          body: formData
        });
        const result = await resp.json().catch(() => null);
        if (!resp.ok || result?.code !== 200 || !result?.data?.url) {
          throw new Error(result?.message || `图片上传失败 (${resp.status})`);
        }
        postImageUrls.push(result.data.url);
      }
      renderImages();
      toast(`已上传 ${selectedFiles.length} 张图片`, "success");
    } catch (error) {
      toast(error.message, "warning");
    } finally {
      imageButton.disabled = false;
      imageButton.textContent = "选择图片";
      imageInput.value = "";
    }
  });

  document.querySelector("[data-save-draft]")?.addEventListener("click", () => {
    const data = formValues(form);
    state.draft = data;
    localStorage.setItem(STORAGE_KEYS.draft, JSON.stringify(data));
    toast("草稿已保存到本地", "success");
  });
  document.querySelector("[data-withdraw-post]")?.addEventListener("click", async (event) => {
    try {
      await apiRequest(`/posts/mine/${event.currentTarget.dataset.withdrawPost}/withdraw`, { method: "PATCH" });
      toast("帖子已撤回", "success");
      location.href = ROUTES.profile;
    } catch (error) {
      toast(error.message, "warning");
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = formValues(form);
    const submitButton = form.querySelector('button[type="submit"]');
    try {
      buttonLoading(submitButton, "Loading");
      const post = await apiRequest(editId ? `/posts/mine/${editId}` : "/posts", {
        method: editId ? "PUT" : "POST",
        body: {
          title: String(data.title || "").trim(),
          sectionId: Number(data.sectionId),
          content: String(data.content || "").trim(),
          coverImage: postImageUrls[0] || null,
          imageUrls: postImageUrls,
          circleId: data.circleId ? Number(data.circleId) : null,
          tags: String(data.tags || "").split(",").map((item) => item.trim()).filter(Boolean)
        }
      });
      localStorage.removeItem(STORAGE_KEYS.draft);
      if (Number(post.status) === 0) {
        setMain(stateCard("帖子已提交审核", "内容已经保存，管理员审核后会公开展示。你可以在个人中心查看状态。", "查看我的主页", ROUTES.profile));
        document.querySelector(".empty-state")?.insertAdjacentHTML("beforeend", `
          <div class="publish-flow" aria-label="publish review flow">
            <span class="publish-flow__step"><span>1</span>已提交</span>
            <i class="publish-flow__line"></i>
            <span class="publish-flow__step"><span>2</span>待审核</span>
            <i class="publish-flow__line"></i>
            <span class="publish-flow__step"><span>3</span>公开展示</span>
          </div>
        `);
        publishFlowEnter(document);
        toast(editId ? "更新已提交审核" : "发布已提交审核", "success");
        return;
      }
      toast(editId ? "帖子已更新" : "发布成功", "success");
      location.href = `${ROUTES.detail}?id=${post.id}`;
    } catch (error) {
      buttonReset(submitButton);
      toast(error.message, "warning");
    }
  });
}
