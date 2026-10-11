// Post detail page: detail view, comments, like/favorite, report submission.
// `data-slot="post-detail-content"` shell marker is referenced for parity with page entries.
import { apiRequest, pageContent } from "../api.js";
import { badgeChips } from "../badges.js";
import { ROUTES } from "../constants.js";
import { state } from "../session.js";
import { buttonLoading, buttonReset, commentEnter } from "../motion.js";
import {
  avatarHtml,
  escapeHtml,
  formValues,
  formatDate,
  isOwnPost,
  pageShell,
  postImageUrls,
  postStatusClass,
  postStatusLabel,
  requireLogin,
  setMain,
  stateCard,
  toast,
  uploadUrl,
  userProfileHref
} from "../ui.js";

export async function resolvePostId() {
  const queryId = new URLSearchParams(location.search).get("id");
  if (queryId) {
    return queryId;
  }
  const first = pageContent(await apiRequest("/posts/hot", { auth: false }))[0];
  return first?.id;
}

function authorIdentity(user, fallback = "论坛用户", avatarClass = "avatar") {
  const name = user?.username || fallback;
  const href = userProfileHref(user);
  if (!href) {
    return {
      avatar: `<span class="${avatarClass}">${avatarHtml(user, name)}</span>`,
      name: `<strong>${escapeHtml(name)}</strong>`
    };
  }
  return {
    avatar: `<a class="${avatarClass} avatar-link" href="${href}" title="查看 ${escapeHtml(name)} 的主页">${avatarHtml(user, name)}</a>`,
    name: `<a class="author-link" href="${href}"><strong>${escapeHtml(name)}</strong></a>`
  };
}

// Render one comment plus its nested replies. Replies are indented one level;
// each comment carries a reply button that reveals an inline reply input.
function commentCard(comment, post, ownPost) {
  const replies = Array.isArray(comment.replies) ? comment.replies : [];
  const replyCount = comment.replyCount ?? replies.length;
  const accepted = Boolean(comment.accepted);
  const canAccept = Boolean(ownPost && state.user && Number(post.status) === 1);
  const commentAuthor = authorIdentity(comment.author);
  const repliesHtml = replies.map((reply) => {
    const replyAuthor = authorIdentity(reply.author);
    return `
      <article class="comment-card comment-card--reply">
        <div class="comment-card__top">
          ${replyAuthor.avatar}
          ${replyAuthor.name}
        </div>
        <p class="muted">${escapeHtml(reply.content || "")}</p>
        <span class="label">${formatDate(reply.createdAt)}</span>
      </article>
    `;
  }).join("");
  return `
    <article class="comment-card${accepted ? " comment-card--accepted" : ""}" data-comment="${escapeHtml(String(comment.id))}">
      <div class="comment-card__top">
        ${commentAuthor.avatar}
        ${commentAuthor.name}
        <div class="detail-badges">
          ${accepted ? '<span class="status-pill status-pill--solved">最佳答案</span>' : ""}
          ${canAccept && !accepted ? `<button type="button" class="button button--solid button--sm" data-accept-comment="${escapeHtml(String(comment.id))}">采纳</button>` : ""}
          ${canAccept && accepted ? `<button type="button" class="button button--outline button--sm" data-cancel-accept="${escapeHtml(String(comment.id))}">取消采纳</button>` : ""}
        </div>
      </div>
      <p class="muted">${escapeHtml(comment.content || "")}</p>
      <div class="comment-card__meta">
        <span class="label">${formatDate(comment.createdAt)}</span>
        <button type="button" class="comment-reply-btn" data-reply-toggle="${escapeHtml(String(comment.id))}">回复${replyCount ? ` (${replyCount})` : ""}</button>
      </div>
      ${repliesHtml ? `<div class="comment-replies">${repliesHtml}</div>` : ""}
      <form class="quick-form comment-reply-form" data-reply-form="${escapeHtml(String(comment.id))}" hidden>
        <div class="field"><textarea class="textarea" name="content" required placeholder="回复 ${escapeHtml(comment.author?.username || "该评论")}"></textarea></div>
        <button class="button button--solid button--sm" type="submit">发送回复</button>
      </form>
    </article>
  `;
}

export async function renderDetail() {
  const id = await resolvePostId();
  if (!id) {
    setMain(stateCard("暂无帖子", "数据库里还没有可展示的帖子。", "发布第一篇", ROUTES.create));
    return;
  }
  const [post, comments] = await Promise.all([
    apiRequest(`/posts/${id}`),
    apiRequest(`/posts/${id}/comments`).then(pageContent)
  ]);
  const ownPost = isOwnPost(post);
  const authorId = post.author?.id;
  const canFollow = Boolean(state.user && authorId && !ownPost);
  const solved = Boolean(post.acceptedCommentId);
  const authorBadges = authorId ? await apiRequest(`/users/${authorId}/badges`, { auth: false }).catch(() => []) : [];
  const images = postImageUrls(post);
  const postAuthor = authorIdentity(post.author, "匿名用户", "avatar avatar--lg");

  setMain(pageShell(
    post.section?.name || "帖子详情",
    `${solved ? "[已解决] " : ""}${post.title}`,
    `${post.author?.username || "匿名用户"} 发布于 ${formatDate(post.createdAt)}`,
    `
      <section class="section">
        <div class="container split-layout">
          <section class="surface-section stack">
            <div class="detail-author">
              ${postAuthor.avatar}
              <span class="detail-author__name">${postAuthor.name}</span>
              ${badgeChips(authorBadges, 3)}
              ${solved ? '<span class="status-pill status-pill--solved">已解决</span>' : ""}
              ${canFollow ? `<button class="button button--outline button--sm" data-follow="${escapeHtml(String(authorId))}" hidden>关注</button><span class="detail-author__followers" data-follower-count hidden></span>` : ""}
            </div>
            <span class="${postStatusClass(post.status)}">${postStatusLabel(post.status)}</span>
            <p class="post-detail__content">${escapeHtml(post.content)}</p>
            ${images.length ? `<div class="post-detail__media-grid">${images.map((url, index) => `<figure class="post-detail__media"><img src="${escapeHtml(url)}" alt="帖子图片 ${index + 1}" loading="lazy" /></figure>`).join("")}</div>` : ""}
            <div class="inline-tags">${(post.tags || []).map((tag) => `<span class="tag">${escapeHtml(tag.name || tag)}</span>`).join("")}</div>
            <div class="meta-row muted">
              <span>${post.viewCount || 0} 浏览</span>
              <span><span data-like-count>${post.likeCount || 0}</span> 点赞</span>
              <span><span data-collect-count>${post.collectCount || 0}</span> 收藏</span>
              <span><span data-comment-count>${post.commentCount || 0}</span> 回复</span>
            </div>
            <div class="hero__actions">
              <button class="button button--outline" data-like-post="${post.id}" data-count-target="[data-like-count]">点赞</button>
              <button class="button button--outline" data-favorite="${post.id}" data-count-target="[data-collect-count]">收藏</button>
              ${ownPost ? `<a class="button button--outline" href="${ROUTES.create}?edit=${post.id}">编辑帖子</a><button class="button button--outline" data-withdraw-detail="${post.id}">撤回帖子</button>` : ""}
            </div>
            <form class="quick-form" data-comment-form>
              <div class="field"><label>发表评论</label><textarea class="textarea" name="content" required placeholder="写下你的回复。"></textarea></div>
              <button class="button button--solid" type="submit">提交评论</button>
            </form>
          </section>
          <aside class="stack">
            <section class="card">
              <div class="label">评论区</div>
              <div class="comment-list" data-comment-list>
                ${comments.map((comment) => commentCard(comment, post, ownPost)).join("") || '<article class="comment-card"><p class="muted">还没有评论，来做第一个回复的人。</p></article>'}
              </div>
            </section>
            <section class="card card--quiet">
              <div class="label">举报反馈</div>
              <form class="quick-form" data-report-form>
                <div class="field"><label>举报原因</label><select class="select" name="reason"><option>垃圾广告</option><option>骚扰辱骂</option><option>违法违规</option><option>虚假信息</option><option>其他</option></select></div>
                <div class="field"><label>补充说明</label><textarea class="textarea" name="detail" maxlength="300" placeholder="可选，说明你看到的问题。"></textarea></div>
                <button class="button button--outline" type="submit">${state.user ? "提交举报" : "登录后举报"}</button>
              </form>
            </section>
          </aside>
        </div>
      </section>
    `
  ));

  hydratePostInteractionState(post);

  const refreshComments = async (highlight = false) => {
    const latestComments = await apiRequest(`/posts/${post.id}/comments`).then(pageContent);
    const list = document.querySelector("[data-comment-list]");
    if (list) {
      list.innerHTML = latestComments.map((comment) => commentCard(comment, post, ownPost)).join("")
        || '<article class="comment-card"><p class="muted">还没有评论，来做第一个回复的人。</p></article>';
    }
    const commentTotal = latestComments.reduce((total, comment) => {
      const replies = Array.isArray(comment.replies) ? comment.replies.length : Number(comment.replyCount || 0);
      return total + 1 + replies;
    }, 0);
    document.querySelectorAll("[data-comment-count]").forEach((node) => {
      node.textContent = String(commentTotal);
    });
    bindCommentInteractions(post, ownPost, refreshComments);
    if (highlight) {
      commentEnter(document.querySelector(".comment-list .comment-card"));
    }
  };

  bindPostActions();
  document.querySelector("[data-withdraw-detail]")?.addEventListener("click", async (event) => {
    try {
      await apiRequest(`/posts/mine/${event.currentTarget.dataset.withdrawDetail}/withdraw`, { method: "PATCH" });
      toast("帖子已撤回", "success");
      location.href = ROUTES.profile;
    } catch (error) {
      toast(error.message, "warning");
    }
  });
  document.querySelector("[data-like-post]")?.addEventListener("click", async (event) => {
    if (!requireLogin()) {
      return;
    }
    const button = event.currentTarget;
    if (button.disabled) {
      return;
    }
    try {
      button.dataset.requesting = "1";
      button.setAttribute("aria-busy", "true");
      button.disabled = true;
      const result = await apiRequest(`/posts/${post.id}/like`, { method: "POST" });
      applyInteractionState(button, result.liked, result.likeCount);
      toast(result.liked ? "点赞成功" : "已取消点赞", "success");
    } catch (error) {
      toast(error.message, "warning");
    } finally {
      button.disabled = false;
      button.dataset.requesting = "0";
      button.removeAttribute("aria-busy");
    }
  });
  document.querySelector("[data-comment-form]")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!requireLogin()) {
      return;
    }
    const submitButton = event.currentTarget.querySelector('button[type="submit"]');
    const data = formValues(event.currentTarget);
    try {
      buttonLoading(submitButton, "Loading");
      await apiRequest(`/posts/${post.id}/comments`, {
        method: "POST",
        body: { content: String(data.content || "").trim() }
      });
      toast("评论已发布", "success");
      event.currentTarget.reset();
      await refreshComments(true);
    } catch (error) {
      buttonReset(submitButton);
      toast(error.message, "warning");
    }
  });
  bindCommentInteractions(post, ownPost, refreshComments);

  // Follow toggle near the author: hydrate state, then flip on click.
  if (canFollow) {
    const followBtn = document.querySelector("[data-follow]");
    const followerEl = document.querySelector("[data-follower-count]");
    const applyStats = (stats) => {
      if (!stats || !followBtn) {
        return;
      }
      followBtn.hidden = false;
      followBtn.textContent = stats.isFollowing ? "已关注" : "关注";
      followBtn.classList.toggle("button--solid", !stats.isFollowing);
      followBtn.classList.toggle("button--outline", Boolean(stats.isFollowing));
      followBtn.dataset.following = stats.isFollowing ? "1" : "0";
      if (followerEl) {
        followerEl.hidden = false;
        followerEl.textContent = `${stats.followers || 0} 粉丝`;
      }
    };
    apiRequest(`/users/${authorId}/follow-stats`).then(applyStats).catch(() => {});
    followBtn?.addEventListener("click", async () => {
      const isFollowing = followBtn.dataset.following === "1";
      try {
        const stats = await apiRequest(`/users/${authorId}/follow`, {
          method: isFollowing ? "DELETE" : "POST"
        });
        applyStats(stats);
        toast(isFollowing ? "已取消关注" : "关注成功", "success");
      } catch (error) {
        toast(error.message, "warning");
      }
    });
  }

  document.querySelector("[data-report-form]")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!requireLogin()) {
      return;
    }
    const data = formValues(event.currentTarget);
    const submitButton = event.currentTarget.querySelector('button[type="submit"]');
    try {
      buttonLoading(submitButton, "Loading");
      await apiRequest(`/posts/${post.id}/report`, {
        method: "POST",
        body: {
          reason: String(data.reason || "").trim(),
          detail: String(data.detail || "").trim() || null
        }
      });
      event.currentTarget.reset();
      toast("举报已提交，管理员会处理", "success");
      buttonReset(submitButton);
    } catch (error) {
      buttonReset(submitButton);
      toast(error.message, "warning");
    }
  });
}

export function bindPostActions() {
  document.querySelectorAll("[data-favorite]").forEach((button) => {
    if (button.dataset.bound === "1") {
      return;
    }
    button.dataset.bound = "1";
    button.addEventListener("click", async () => {
      if (!requireLogin()) {
        return;
      }
      if (button.disabled) {
        return;
      }
      try {
        button.dataset.requesting = "1";
        button.setAttribute("aria-busy", "true");
        button.disabled = true;
        const result = await apiRequest(`/posts/${button.dataset.favorite}/favorite`, { method: "POST" });
        applyInteractionState(button, result.favorited, result.collectCount);
        toast(result.favorited ? "收藏成功" : "已取消收藏", "success");
      } catch (error) {
        toast(error.message, "warning");
      } finally {
        button.disabled = false;
        button.dataset.requesting = "0";
        button.removeAttribute("aria-busy");
      }
    });
  });
}

function hydratePostInteractionState(post) {
  const likeButton = document.querySelector("[data-like-post]");
  if (likeButton) {
    applyInteractionState(likeButton, post.likedByCurrentUser, post.likeCount);
  }

  const favoriteButton = document.querySelector(`[data-favorite="${post.id}"]`);
  if (favoriteButton) {
    applyInteractionState(favoriteButton, post.favoritedByCurrentUser, post.collectCount);
  }
}

function bindCommentInteractions(post, ownPost, refreshComments) {
  document.querySelectorAll("[data-accept-comment]").forEach((button) => {
    if (button.dataset.bound === "1") {
      return;
    }
    button.dataset.bound = "1";
    button.addEventListener("click", async () => {
      if (!requireLogin()) {
        return;
      }
      try {
        await apiRequest(`/posts/${post.id}/comments/${button.dataset.acceptComment}/accept`, { method: "POST" });
        toast("已采纳最佳答案", "success");
        await refreshComments();
      } catch (error) {
        toast(error.message, "warning");
      }
    });
  });

  document.querySelectorAll("[data-cancel-accept]").forEach((button) => {
    if (button.dataset.bound === "1") {
      return;
    }
    button.dataset.bound = "1";
    button.addEventListener("click", async () => {
      if (!requireLogin()) {
        return;
      }
      try {
        await apiRequest(`/posts/${post.id}/comments/${button.dataset.cancelAccept}/accept`, { method: "DELETE" });
        toast("已取消采纳", "success");
        await refreshComments();
      } catch (error) {
        toast(error.message, "warning");
      }
    });
  });

  document.querySelectorAll("[data-reply-toggle]").forEach((button) => {
    if (button.dataset.bound === "1") {
      return;
    }
    button.dataset.bound = "1";
    button.addEventListener("click", () => {
      if (!requireLogin()) {
        return;
      }
      const form = document.querySelector(`[data-reply-form="${button.dataset.replyToggle}"]`);
      if (form) {
        form.hidden = !form.hidden;
        if (!form.hidden) {
          form.querySelector("textarea")?.focus();
        }
      }
    });
  });

  document.querySelectorAll("[data-reply-form]").forEach((form) => {
    if (form.dataset.bound === "1") {
      return;
    }
    form.dataset.bound = "1";
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!requireLogin()) {
        return;
      }
      const content = String(formValues(form).content || "").trim();
      if (!content) {
        return;
      }
      const submitButton = form.querySelector('button[type="submit"]');
      try {
        buttonLoading(submitButton, "Loading");
        await apiRequest(`/posts/${post.id}/comments`, {
          method: "POST",
          body: { content, parentId: Number(form.dataset.replyForm) }
        });
        toast("回复已发布", "success");
        await refreshComments(true);
      } catch (error) {
        buttonReset(submitButton);
        toast(error.message, "warning");
      }
    });
  });
}

function applyInteractionState(button, active, count) {
  button.classList.toggle("is-active", Boolean(active));
  button.classList.toggle("button--solid", Boolean(active) && button.classList.contains("button"));
  button.classList.toggle("button--outline", !active && button.classList.contains("button"));
  button.setAttribute("aria-pressed", active ? "true" : "false");
  if (button.hasAttribute("title")) {
    button.setAttribute("title", active ? "取消收藏" : "收藏");
  }

  const targetSelector = button.dataset.countTarget;
  const countTarget = targetSelector ? document.querySelector(targetSelector) : null;
  if (countTarget && Number.isFinite(Number(count))) {
    countTarget.textContent = String(count);
    return;
  }

  if (!button.classList.contains("stat-chip") || !Number.isFinite(Number(count))) {
    return;
  }
  let countNode = button.querySelector(".stat-chip__count");
  if (!countNode) {
    countNode = document.createElement("span");
    countNode.className = "stat-chip__count";
    button.append(countNode);
  }
  countNode.textContent = String(count);
}
