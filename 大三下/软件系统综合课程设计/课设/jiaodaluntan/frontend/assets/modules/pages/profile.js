// User center: profile editing, campus identity, posts, favorites, history.
import { apiRequest, pageContent } from "../api.js";
import { badgePanel } from "../badges.js";
import { ROUTES, STORAGE_KEYS } from "../constants.js";
import { state } from "../session.js";
import {
  avatarHtml,
  avatarUrl,
  escapeHtml,
  formValues,
  formatDate,
  pageShell,
  postCard,
  postStatusLabel,
  requireLogin,
  setMain,
  toast,
  userProfileHref
} from "../ui.js";
import { avatarAsset } from "../visual-assets.js";

function resolveViewedUserId() {
  const raw = new URLSearchParams(location.search).get("userId");
  const id = Number(raw);
  return Number.isFinite(id) && id > 0 ? id : null;
}

async function renderPublicProfile(userId) {
  const [user, posts, userBadges, followStats] = await Promise.all([
    apiRequest(`/users/${userId}`, { auth: false }),
    apiRequest(`/posts/by-user/${userId}?size=50`, { auth: false }).then(pageContent),
    apiRequest(`/users/${userId}/badges`, { auth: false }).catch(() => []),
    apiRequest(`/users/${userId}/follow-stats`).catch(() => null)
  ]);
  const ownProfile = Boolean(state.user?.id && Number(state.user.id) === Number(user.id));
  if (ownProfile) {
    history.replaceState(null, "", ROUTES.profile);
    await renderProfile();
    return;
  }
  const tags = Array.isArray(user.tags) && user.tags.length
    ? user.tags.map((tag) => `<span class="tag">#${escapeHtml(tag.name || tag)}</span>`).join("")
    : '<span class="muted">暂未设置校园标签</span>';
  const profileBio = user.bio || `${user.college || "西南交通大学"} · ${user.major || "论坛用户"}`;
  const postsHtml = posts.length
    ? posts.map(postCard).join("")
    : '<article class="card"><p class="muted">这位用户还没有公开发布的帖子。</p></article>';

  setMain(pageShell(
    "用户主页",
    `${user.username} 的主页`,
    `${user.college || "西南交通大学"} · ${user.major || "论坛用户"} · Lv.${user.level || 1}`,
    `
      <section class="section">
        <div class="container split-layout">
          <section class="surface-section stack">
            <div class="avatar-row profile-hero">
              <span class="avatar avatar--lg">${avatarHtml(user, user.username)}</span>
              <div>
                <h2 class="post-card__title">${escapeHtml(user.username)}</h2>
                <p class="muted">${escapeHtml(profileBio)}</p>
                <div class="inline-tags">${tags}</div>
              </div>
            </div>
            <div class="meta-row muted">
              <span>Lv.${escapeHtml(String(user.level || 1))}</span>
              <span>${escapeHtml(String(user.points || 0))} 积分</span>
              <span>${posts.length} 篇公开帖子</span>
              ${user.campusVerified ? '<span class="status-pill status-pill--ok">校园身份已认证</span>' : ""}
            </div>
            ${state.user && !ownProfile ? `<button class="button button--outline" data-public-follow="${escapeHtml(String(user.id))}" hidden>关注</button>` : ""}
          </section>
          <aside class="stack">
            <section class="card">
              <div class="label">他的徽章</div>
              ${badgePanel(userBadges)}
            </section>
            <section class="card">
              <div class="label">关注数据</div>
              <p class="muted" data-public-followers>${followStats ? `${followStats.followers || 0} 粉丝 · ${followStats.following || 0} 关注` : "登录后可查看关注状态"}</p>
            </section>
          </aside>
        </div>
      </section>
      <section class="section">
        <div class="container stack">
          <div class="toolbar-space">
            <div>
              <div class="label">公开帖子</div>
              <h2 class="post-card__title">他发布的内容</h2>
            </div>
          </div>
          <div class="post-list">${postsHtml}</div>
        </div>
      </section>
    `
  ));

  const followButton = document.querySelector("[data-public-follow]");
  const followerText = document.querySelector("[data-public-followers]");
  const applyStats = (stats) => {
    if (!stats || !followButton) {
      return;
    }
    followButton.hidden = false;
    followButton.textContent = stats.isFollowing ? "已关注" : "关注";
    followButton.classList.toggle("button--solid", !stats.isFollowing);
    followButton.classList.toggle("button--outline", Boolean(stats.isFollowing));
    followButton.dataset.following = stats.isFollowing ? "1" : "0";
    if (followerText) {
      followerText.textContent = `${stats.followers || 0} 粉丝 · ${stats.following || 0} 关注`;
    }
  };
  applyStats(followStats);
  followButton?.addEventListener("click", async () => {
    if (!requireLogin()) {
      return;
    }
    const isFollowing = followButton.dataset.following === "1";
    try {
      const stats = await apiRequest(`/users/${user.id}/follow`, {
        method: isFollowing ? "DELETE" : "POST"
      });
      applyStats(stats);
      toast(isFollowing ? "已取消关注" : "关注成功", "success");
    } catch (error) {
      toast(error.message, "warning");
    }
  });
}

export async function renderProfile() {
  const viewedUserId = resolveViewedUserId();
  if (viewedUserId) {
    await renderPublicProfile(viewedUserId);
    return;
  }
  if (!requireLogin()) {
    return;
  }
  const [me, mine, favorites, history, following, followers, selectedTags, interestTags] = await Promise.all([
    apiRequest("/auth/me"),
    apiRequest("/posts/mine").then(pageContent),
    apiRequest("/posts/favorites").then(pageContent),
    apiRequest("/posts/history").then(pageContent),
    apiRequest("/users/me/following").then(pageContent).catch(() => []),
    apiRequest("/users/me/followers").then(pageContent).catch(() => []),
    apiRequest("/users/me/tags").catch(() => []),
    apiRequest("/tags/interests", { auth: false }).catch(() => [])
  ]);
  const userBadges = await apiRequest(`/users/${me.id}/badges`).catch(() => []);
  state.user = me;
  localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(me));
  const selectedTagIds = new Set((selectedTags || []).map((tag) => Number(tag.id)));
  const interestTagOptions = (interestTags || []).length ? interestTags.map((tag) => `
    <label class="interest-tag-option">
      <input type="checkbox" value="${escapeHtml(tag.id)}" ${selectedTagIds.has(Number(tag.id)) ? "checked" : ""} />
      <span>${escapeHtml(tag.name)}</span>
    </label>
  `).join("") : `<p class="muted">暂无可选校园身份标签，请稍后刷新。</p>`;
  const links = (posts, empty, mineList = false) => posts.length ? posts.map((post) => `
    <article class="comment-card">
      <strong>${escapeHtml(post.title)}</strong>
      <p class="muted">${formatDate(post.createdAt)} · ${postStatusLabel(post.status)}</p>
      <div class="post-actions">
        <a class="button button--outline button--sm" href="${ROUTES.detail}?id=${post.id}">查看</a>
        ${mineList ? `<a class="button button--outline button--sm" href="${ROUTES.create}?edit=${post.id}">编辑</a><button class="button button--outline button--sm" data-withdraw-profile="${post.id}">撤回</button>` : ""}
      </div>
    </article>
  `).join("") : `<article class="comment-card"><p class="muted">${escapeHtml(empty)}</p></article>`;
  const followList = (items, type) => items.length ? items.map((item) => {
    const user = type === "following" ? item.following : item.follower;
    if (!user) {
      return "";
    }
    const profileHref = userProfileHref(user);
    return `
      <article class="comment-card follow-card" data-follow-card="${escapeHtml(String(user.id))}">
        <div class="avatar-row">
          <a class="avatar avatar-link" href="${profileHref}" title="查看 ${escapeHtml(user.username)} 的主页">${avatarHtml(user, user.username)}</a>
          <div>
            <a class="author-link" href="${profileHref}"><strong>${escapeHtml(user.username)}</strong></a>
            <p class="muted">Lv.${escapeHtml(String(user.level || 1))} · ${escapeHtml(user.bio || user.major || "交大论坛用户")}</p>
          </div>
        </div>
        <div class="post-actions">
          ${type === "following" ? `<button class="button button--outline button--sm" data-unfollow="${escapeHtml(String(user.id))}">取消关注</button>` : ""}
        </div>
      </article>
    `;
  }).join("") : `<article class="comment-card"><p class="muted">${type === "following" ? "还没有关注任何用户。" : "还没有粉丝。"}</p></article>`;
  const campusStatus = me.campusVerified ? "已认证" : (me.campusIdentityStatus === "FAILED" ? "认证失败" : "未认证");

  setMain(pageShell(
    "个人中心",
    `${me.username} 的主页`,
    `${me.college || "西南交通大学"} · ${me.major || "交大社区用户"} · Lv.${me.level || 1} · ${me.points || 0} 积分`,
    `
      <section class="section">
        <div class="container split-layout">
          <section class="surface-section stack">
            <div class="toolbar-space">
              <div><div class="label">账户资料</div><h2 class="post-card__title">${escapeHtml(me.username)}</h2></div>
              <span class="${me.campusVerified ? "status-pill status-pill--ok" : "status-pill status-pill--warn"}">校园身份：${campusStatus}</span>
            </div>
            <form class="quick-form" data-profile-form>
              <div class="field">
                <label>头像</label>
                <div class="avatar-upload" data-avatar-upload>
                  <div class="avatar-upload__preview" data-avatar-preview>
                    ${me.avatar
                      ? `<img src="${escapeHtml(avatarUrl(me.avatar))}" alt="头像" />`
                      : `<img src="${avatarAsset(me.role)}" alt="" style="width:100%;height:100%;object-fit:contain;border-radius:50%;padding:8px" />`
                    }
                  </div>
                  <div class="avatar-upload__actions">
                    <input type="file" accept="image/*" data-avatar-input style="display:none" />
                    <button type="button" class="button button--outline button--sm" data-avatar-btn>选择图片</button>
                    <p class="muted" style="font-size:13px;margin:4px 0 0">支持 JPG、PNG，最大 5MB</p>
                  </div>
                </div>
                <input type="hidden" name="avatar" value="${escapeHtml(me.avatar || "")}" data-avatar-url />
              </div>
              <div class="field"><label>个人简介</label><textarea class="textarea" name="bio" maxlength="500" placeholder="介绍一下你在论坛里关注什么。">${escapeHtml(me.bio || "")}</textarea></div>
              <div class="duo-grid">
                <div class="field"><label>学院</label><input class="input" name="college" maxlength="50" value="${escapeHtml(me.college || "")}" ${me.campusVerified ? "disabled" : ""} /></div>
                <div class="field"><label>专业</label><input class="input" name="major" maxlength="50" value="${escapeHtml(me.major || "")}" ${me.campusVerified ? "disabled" : ""} /></div>
              </div>
              <div class="field"><label>学号</label><input class="input" name="studentId" maxlength="20" value="${escapeHtml(me.studentId || "")}" ${me.campusVerified ? "disabled" : ""} /></div>
              <button class="button button--solid" type="submit">保存资料</button>
            </form>
            <form class="quick-form" data-campus-form>
              <div class="label">校园身份认证</div>
              <div class="duo-grid">
                <div class="field"><label>学号</label><input class="input" name="studentId" value="${escapeHtml(me.studentId || "20240001")}" placeholder="20240001" /></div>
                <div class="field"><label>校园邮箱</label><input class="input" name="campusEmail" type="email" value="${escapeHtml(me.campusEmail || "20240001@swjtu.edu.cn")}" placeholder="20240001@swjtu.edu.cn" /></div>
              </div>
              <button class="button button--outline" type="submit">提交认证</button>
              <p class="muted">${escapeHtml(me.campusVerificationMessage || "请填写学号和校园邮箱完成校内身份信息核验。")}</p>
            </form>
          </section>
          <aside class="stack">
            <section class="card">
              <div class="label">我的校园徽章</div>
              ${badgePanel(userBadges)}
            </section>
            <section class="card">
              <div class="toolbar-space">
                <div><div class="label">我的关注</div><p class="muted"><span data-following-count>${following.length}</span> 位正在关注</p></div>
              </div>
              <div class="comment-list" data-following-list>${followList(following, "following")}</div>
            </section>
            <section class="card">
              <div class="toolbar-space">
                <div><div class="label">我的粉丝</div><p class="muted">${followers.length} 位关注者</p></div>
              </div>
              <div class="comment-list">${followList(followers, "followers")}</div>
            </section>
            <section class="card">
              <div class="label">校园身份标签</div>
              <p class="muted">选择你关注的校园主题，首页和个人主页会更像真实的交大论坛。</p>
              <form class="quick-form" data-interest-tags-form>
                <div class="interest-tag-picker">${interestTagOptions}</div>
                <button class="button button--outline button--sm" type="submit">保存标签</button>
              </form>
            </section>
            <section class="card"><div class="label">我的帖子</div><div class="comment-list">${links(mine, "还没有发帖。", true)}</div></section>
            <section class="card"><div class="label">我的收藏</div><div class="comment-list">${links(favorites, "还没有收藏。")}</div></section>
            <section class="card"><div class="label">浏览记录</div><div class="comment-list">${links(history, "还没有浏览记录。")}</div></section>
          </aside>
        </div>
      </section>
    `
  ));
  document.querySelector("[data-profile-form]")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = formValues(event.currentTarget);
    try {
      const updated = await apiRequest("/users/me", {
        method: "PUT",
        body: {
          avatar: String(data.avatar || "").trim() || null,
          bio: String(data.bio || "").trim() || null,
          college: String(data.college || "").trim() || null,
          major: String(data.major || "").trim() || null,
          studentId: String(data.studentId || "").trim() || null
        }
      });
      state.user = updated;
      localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(updated));
      toast("资料已保存", "success");
    } catch (error) {
      toast(error.message, "warning");
    }
  });

  // Avatar upload
  const avatarInput = document.querySelector("[data-avatar-input]");
  const avatarBtn = document.querySelector("[data-avatar-btn]");
  const avatarPreview = document.querySelector("[data-avatar-preview]");
  const avatarUrlInput = document.querySelector("[data-avatar-url]");

  avatarBtn?.addEventListener("click", () => avatarInput?.click());

  avatarInput?.addEventListener("change", async () => {
    const file = avatarInput.files?.[0];
    if (!file) return;

    // Preview
    const reader = new FileReader();
    reader.onload = () => {
      if (avatarPreview) {
        avatarPreview.innerHTML = `<img src="${reader.result}" alt="头像" style="width:100%;height:100%;object-fit:cover;border-radius:50%" />`;
      }
    };
    reader.readAsDataURL(file);

    // Upload
    const formData = new FormData();
    formData.append("file", file);
    try {
      const resp = await fetch("/api/users/me/avatar", {
        method: "POST",
        headers: { "Authorization": `Bearer ${state.token}` },
        body: formData
      });
      const result = await resp.json();
      if (result.code === 200 && result.data?.url) {
        if (avatarUrlInput) avatarUrlInput.value = result.data.url;
        toast("头像已上传，保存资料后生效", "success");
      } else {
        toast(result.message || "上传失败", "warning");
      }
    } catch (err) {
      toast("上传失败：" + err.message, "warning");
    }
  });
  document.querySelector("[data-campus-form]")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = formValues(event.currentTarget);
    try {
      const result = await apiRequest("/users/me/campus-identity", {
        method: "PUT",
        body: {
          studentId: String(data.studentId || "").trim(),
          campusEmail: String(data.campusEmail || "").trim()
        }
      });
      state.user = result.user || state.user;
      localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(state.user));
      toast(result.message || "校园身份认证成功", "success");
      const statusPill = document.querySelector(".status-pill");
      if (statusPill && state.user?.campusVerified) {
        statusPill.classList.remove("status-pill--warn");
        statusPill.classList.add("status-pill--ok");
        statusPill.textContent = "校园身份：已认证";
      }
    } catch (error) {
      toast(error.message, "warning");
    }
  });
  document.querySelector("[data-interest-tags-form]")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const tagIds = Array.from(event.currentTarget.querySelectorAll("input[type='checkbox']:checked"))
      .map((input) => Number(input.value))
      .filter((id) => Number.isFinite(id));
    try {
      await apiRequest("/users/me/tags", {
        method: "PUT",
        body: { tagIds }
      });
      toast("校园身份标签已保存", "success");
    } catch (error) {
      toast(error.message, "warning");
    }
  });
  document.querySelectorAll("[data-withdraw-profile]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await apiRequest(`/posts/mine/${button.dataset.withdrawProfile}/withdraw`, { method: "PATCH" });
        toast("帖子已撤回", "success");
        const card = button.closest(".comment-card");
        const meta = card?.querySelector(".muted");
        if (meta) {
          const dateText = meta.textContent.split(" · ")[0] || meta.textContent;
          meta.textContent = `${dateText} · 已撤回`;
        }
        button.remove();
      } catch (error) {
        toast(error.message, "warning");
      }
    });
  });
  document.querySelectorAll("[data-unfollow]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await apiRequest(`/users/${button.dataset.unfollow}/follow`, { method: "DELETE" });
        toast("已取消关注", "success");
        button.closest("[data-follow-card]")?.remove();
        const countNode = document.querySelector("[data-following-count]");
        if (countNode) {
          countNode.textContent = String(Math.max(0, Number(countNode.textContent || 0) - 1));
        }
        const list = document.querySelector("[data-following-list]");
        if (list && !list.querySelector("[data-follow-card]")) {
          list.innerHTML = '<article class="comment-card"><p class="muted">还没有关注任何用户。</p></article>';
        }
      } catch (error) {
        toast(error.message, "warning");
      }
    });
  });
}
