// Landing + public home feed: hot posts, search/filter, section navigation.
import { apiRequest, fetchSections, pageContent } from "../api.js";
import { ROUTES } from "../constants.js";
import { escapeHtml, formValues, pageShell, postCard, setMain, stateCard } from "../ui.js";
import { emptyAsset, sectionAsset } from "../visual-assets.js";
import { bindPostActions } from "./detail.js";

const CAMPUS_FALLBACK_TOPICS = [
  "课程互助", "考研保研", "实习就业", "二手闲置", "失物招领",
  "犀浦生活", "通宵复习", "高数", "Java", "实验报告",
  "社团招新", "食堂", "竞赛组队", "图书馆", "夏令营",
  "轨道交通", "摄影", "运动打卡", "四六级", "校园服务"
];

const FEED_SORTS = {
  hot: "最热",
  latest: "最新"
};

function normalizeSort(value) {
  return value === "latest" ? "latest" : "hot";
}

function compareTimeDesc(a, b) {
  return new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime();
}

function postHeat(post) {
  return Number(post.heatScore || 0) * 10
    + Number(post.likeCount || 0) * 6
    + Number(post.collectCount || 0) * 8
    + Number(post.commentCount || 0) * 4
    + Number(post.viewCount || 0);
}

function sortPosts(posts, sort) {
  const next = [...posts];
  if (sort === "latest") {
    return next.sort(compareTimeDesc);
  }
  return next.sort((a, b) => postHeat(b) - postHeat(a) || compareTimeDesc(a, b));
}

function homeUrl({ keyword = "", sectionId = "", sort = "hot" } = {}) {
  const params = new URLSearchParams();
  if (keyword.trim()) {
    params.set("keyword", keyword.trim());
  }
  if (String(sectionId || "").trim()) {
    params.set("sectionId", String(sectionId).trim());
  }
  params.set("sort", normalizeSort(sort));
  return `${ROUTES.home}?${params.toString()}`;
}

function feedRequestPath({ keyword, sectionId, sort }) {
  if (keyword) {
    return `/posts/search?keyword=${encodeURIComponent(keyword)}`;
  }
  if (sectionId) {
    return `/posts?sectionId=${encodeURIComponent(sectionId)}`;
  }
  return sort === "latest" ? "/posts" : "/posts/hot";
}

function sectionWidget(sections) {
  const chips = sections
    .map((section) => `
      <a class="section-tile" href="${ROUTES.home}?sectionId=${section.id}">
        <img src="${sectionAsset(section.name)}" alt="" loading="lazy" />
        <span>${escapeHtml(section.name)}</span>
      </a>
    `)
    .join("");
  return `
    <section class="card">
      <h3 class="widget__title">板块导航</h3>
      <div class="section-chips">${chips || '<span class="muted">暂无板块</span>'}</div>
    </section>
  `;
}

function normalizeTopicWords(trendingTags = []) {
  const words = trendingTags.map((item) => ({
    text: item.tag || item.name || item.text,
    count: Number(item.count || item.heat || 1)
  })).filter((item) => item.text);
  const seen = new Set(words.map((item) => item.text));
  CAMPUS_FALLBACK_TOPICS.forEach((text, index) => {
    if (!seen.has(text)) {
      words.push({ text, count: Math.max(1, 10 - Math.floor(index / 2)) });
    }
  });
  return words.slice(0, 36);
}

function trendingTagsWidget(trendingTags) {
  const items = normalizeTopicWords(trendingTags).slice(0, 12)
    .map((item) => `<a class="tag tag--brand" href="${ROUTES.home}?keyword=${encodeURIComponent(item.text)}">#${escapeHtml(item.text)} <span>${item.count}</span></a>`)
    .join("");
  return `
    <section class="card">
      <h3 class="widget__title">今日热点话题</h3>
      <div class="section-chips">${items}</div>
    </section>
  `;
}

function hotTodayWidget(posts) {
  const items = (posts || []).slice(0, 5)
    .map((post, index) => `
      <a class="rank-item" href="${ROUTES.detail}?id=${post.id}">
        <span class="rank-item__no">${index + 1}</span>
        <span class="rank-item__title">${escapeHtml(post.title)}</span>
        <span class="muted">${escapeHtml(String(post.heatScore || 0))} 热度</span>
      </a>
    `)
    .join("");
  return `
    <section class="card">
      <h3 class="widget__title">今日热帖</h3>
      <div class="rank-list">${items || '<span class="muted">今天还没有热帖，先去发一帖吧。</span>'}</div>
    </section>
  `;
}

function swjtuWordCloud(trendingTags) {
  const words = normalizeTopicWords(trendingTags);
  const layout = [
    [260, 156, 54, 0, "SWJTU", "core"], [260, 218, 40, 0, words[0]?.text || "犀浦", "hot"],
    [164, 112, 28, -8], [344, 112, 25, 7], [126, 158, 23, 8], [394, 160, 26, -8],
    [126, 208, 22, -6], [382, 212, 24, 8], [178, 258, 21, 7], [330, 260, 22, -7],
    [216, 92, 17, -5], [304, 92, 17, 5], [96, 246, 17, -8], [424, 246, 17, 8],
    [146, 292, 16, 5], [372, 292, 16, -6], [224, 306, 16, -4], [300, 312, 15, 5],
    [98, 116, 14, -5], [422, 118, 14, 6], [94, 188, 14, 5], [430, 190, 14, -5],
    [196, 334, 13, 5], [324, 334, 13, -5], [254, 344, 12, 0], [142, 76, 12, -7],
    [378, 78, 12, 7], [260, 74, 12, 0]
  ];
  const cloudWords = layout.map((position, index) => ({
    text: position[4] || words[index % words.length]?.text || "校园话题",
    position
  }));
  return `
    <section class="card swjtu-cloud-card">
      <h3 class="widget__title">SWJTU 热词云</h3>
      <svg class="heart-word-cloud" viewBox="0 0 520 390" role="img" aria-label="由校园热点话题组成的爱心形词云">
        <path class="heart-word-cloud__shape" d="M260 354C160 286 74 226 74 142C74 84 114 48 164 48C202 48 235 69 260 104C285 69 318 48 356 48C406 48 446 84 446 142C446 226 360 286 260 354Z" />
        ${cloudWords.map((word, index) => {
          const [x, y, size, rotate,, variant] = word.position;
          const textLength = Math.min(Math.max(word.text.length * size * 0.92, size * 2.4), variant ? 190 : 118);
          return `
            <a href="${ROUTES.home}?keyword=${encodeURIComponent(word.text)}" class="heart-word-cloud__link">
              <text x="${x}" y="${y}" text-anchor="middle"
                class="heart-word-cloud__word heart-word-cloud__word--${(index % 4) + 1}${variant ? ` heart-word-cloud__word--${variant}` : ""}"
                style="font-size:${size}px;--delay:${index * 48}ms"
                textLength="${textLength}" lengthAdjust="spacingAndGlyphs"
                transform="rotate(${rotate} ${x} ${y})">${escapeHtml(word.text)}</text>
            </a>
          `;
        }).join("")}
      </svg>
    </section>
  `;
}

function trendingWidget(posts) {
  const items = posts.slice(0, 6)
    .map((post) => `
      <a class="rank-item" href="${ROUTES.detail}?id=${post.id}">
        <span class="rank-item__no"></span>
        <span class="rank-item__title">${escapeHtml(post.title)}</span>
      </a>
    `)
    .join("");
  return `
    <section class="card">
      <h3 class="widget__title">热门榜</h3>
      <div class="rank-list">${items || '<span class="muted">还没有热门内容</span>'}</div>
    </section>
  `;
}

export async function renderLanding() {
  const [sections, posts, trendingTags, hotToday] = await Promise.all([
    fetchSections(),
    apiRequest("/posts/hot", { auth: false }).then(pageContent),
    apiRequest("/posts/trending-tags", { auth: false }).catch(() => []),
    apiRequest("/posts/hot-today", { auth: false }).catch(() => [])
  ]);
  setMain(pageShell(
    "西南交大论坛",
    "交大人交流学习与校园生活的社区",
    "课程互助、保研考研、实习就业、犀浦生活、二手闲置、失物招领，同学们正在聊的话题都在这里。",
    `
      <section class="section">
        <div class="container split-layout">
          <div class="stack">
            ${posts.map(postCard).join("") || stateCard("还没有帖子", "成为第一个发布的人，开启社区话题。", "去发布", ROUTES.create, `<img src="${emptyAsset("posts")}" alt="" />`)}
          </div>
          <aside class="stack">
            ${sectionWidget(sections)}
            ${trendingTagsWidget(trendingTags)}
            ${swjtuWordCloud(trendingTags)}
            ${hotTodayWidget(hotToday)}
            ${trendingWidget(posts)}
          </aside>
        </div>
      </section>
    `,
    "",
    `<a class="button button--solid" href="${ROUTES.create}">发布帖子</a>`
  ));
  bindPostActions();
}

export async function renderHome() {
  const params = new URLSearchParams(location.search);
  const sectionId = params.get("sectionId");
  const keyword = (params.get("keyword") || "").trim();
  const sort = normalizeSort(params.get("sort"));
  const [sections, feed, hot, trendingTags, hotToday] = await Promise.all([
    fetchSections(),
    apiRequest(feedRequestPath({ keyword, sectionId, sort }), { auth: false }),
    apiRequest("/posts/hot", { auth: false }).then(pageContent),
    apiRequest("/posts/trending-tags", { auth: false }).catch(() => []),
    apiRequest("/posts/hot-today", { auth: false }).catch(() => [])
  ]);
  const posts = sortPosts(
    pageContent(feed).filter((post) => !sectionId || String(post.section?.id) === String(sectionId)),
    sort
  );
  const activeSection = sections.find((section) => String(section.id) === String(sectionId));

  const kicker = keyword ? `搜索「${keyword}」` : (activeSection ? activeSection.name : "社区动态");
  const title = keyword
    ? `关于「${keyword}」的讨论`
    : (activeSection ? activeSection.name : (sort === "latest" ? "最新帖子" : "最热帖子"));
  const intro = keyword
    ? `找到 ${posts.length} 条相关帖子，可按最新或最热排序。`
    : (activeSection ? (activeSection.description || "看看这个板块里大家在聊什么。") : "按最新时间或热度查看社区讨论，点进帖子参与回复。");

  const sectionOptions = sections
    .map((section) => `<option value="${section.id}" ${String(sectionId || "") === String(section.id) ? "selected" : ""}>${escapeHtml(section.name)}</option>`)
    .join("");
  const filterBar = `
    <div class="feed-filter">
      <form class="quick-form feed-filter__form" data-search-form>
        <div class="duo-grid">
          <div class="field"><label>关键词</label><input class="input" name="keyword" value="${escapeHtml(keyword)}" placeholder="课程、考研、二手、失物招领" /></div>
          <div class="field"><label>板块</label><select class="select" name="sectionId"><option value="">全部板块</option>${sectionOptions}</select></div>
        </div>
        <div class="post-actions">
          <button class="button button--solid button--sm" type="submit">筛选帖子</button>
          <a class="button button--outline button--sm" href="${ROUTES.home}?sort=${sort}">重置</a>
        </div>
      </form>
    </div>
  `;
  const feedToolbar = `
    <section class="feed-toolbar" aria-label="帖子排序">
      <div>
        <strong>${FEED_SORTS[sort]}排序</strong>
        <span class="muted">当前显示 ${posts.length} 条帖子</span>
      </div>
      <div class="feed-toolbar__actions">
        <button type="button" class="button button--sm ${sort === "latest" ? "button--solid" : "button--outline"}" data-feed-sort="latest">最新</button>
        <button type="button" class="button button--sm ${sort === "hot" ? "button--solid" : "button--outline"}" data-feed-sort="hot">最热</button>
        <button type="button" class="button button--ghost button--sm" data-feed-refresh>刷新</button>
      </div>
    </section>
  `;

  setMain(pageShell(
    kicker,
    title,
    intro,
    `
      <section class="section">
        <div class="container split-layout">
          <div class="stack">
            <section class="feed-results">
              ${filterBar}
              ${feedToolbar}
              <div class="feed-results__list">
                ${posts.map(postCard).join("") || stateCard(
              keyword ? "没有找到相关帖子" : "这个板块还没有帖子",
              keyword ? "换个关键词试试，或浏览其它板块。" : "成为第一个在这里发帖的人。",
              "去发布",
              ROUTES.create,
              `<img src="${emptyAsset(keyword ? "search" : "posts")}" alt="" />`
                )}
              </div>
            </section>
          </div>
          <aside class="stack">
            ${sectionWidget(sections)}
            ${trendingTagsWidget(trendingTags)}
            ${swjtuWordCloud(trendingTags)}
            ${hotTodayWidget(hotToday)}
            ${trendingWidget(hot)}
          </aside>
        </div>
      </section>
    `,
    "",
    `<a class="button button--solid" href="${ROUTES.create}">发布帖子</a>`
  ));
  document.querySelector("[data-search-form]")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = formValues(event.currentTarget);
    history.pushState(
      { page: "home" },
      "",
      homeUrl({ keyword: String(data.keyword || ""), sectionId: data.sectionId, sort })
    );
    renderHome();
  });
  document.querySelectorAll("[data-feed-sort]").forEach((button) => {
    button.addEventListener("click", () => {
      history.pushState({ page: "home" }, "", homeUrl({ keyword, sectionId, sort: button.dataset.feedSort }));
      renderHome();
    });
  });
  document.querySelector("[data-feed-refresh]")?.addEventListener("click", (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    button.textContent = "刷新中";
    renderHome();
  });
  bindPostActions();
}
