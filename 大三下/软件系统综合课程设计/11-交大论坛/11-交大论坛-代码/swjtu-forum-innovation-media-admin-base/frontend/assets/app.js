// Shared runtime entry for every Vite MPA page.
// Bootstraps the session, wires global navigation, then dispatches to the page
// handler selected by `document.body.dataset.page`. All behavior lives in the
// ES modules under ./modules/ (constants, api, session, ui, and pages/*).
import { ROUTES } from "./modules/constants.js";
import { restoreSession } from "./modules/api.js";
import { highlightNav, injectRuntimeCss, isAdminRoute, mountChrome, setMain, stateCard, toast } from "./modules/ui.js";
import { installMotionSystem } from "./modules/motion.js";
import { renderLanding, renderHome } from "./modules/pages/home.js";
import { renderAuth } from "./modules/pages/auth.js";
import { renderCreate } from "./modules/pages/create.js";
import { renderDetail } from "./modules/pages/detail.js";
import { renderProfile } from "./modules/pages/profile.js";
import { renderCircles } from "./modules/pages/circles.js";
import { renderGrowth } from "./modules/pages/growth.js";
import { renderRewards } from "./modules/pages/rewards.js";
import { renderAdmin } from "./modules/pages/admin.js";
import { renderModeration } from "./modules/pages/moderation.js";
import { renderUsers } from "./modules/pages/users.js";
import { renderRecommendation } from "./modules/pages/recommendation.js";

const ADMIN_CLIENT_ROUTES = [
  { route: ROUTES.admin, page: "admin-overview", render: () => renderAdmin() },
  { route: ROUTES.moderation, page: "moderation", render: () => renderModeration() },
  { route: ROUTES.users, page: "user-management-desktop", render: () => renderUsers() },
  { route: ROUTES.recommendation, page: "recommendation-desktop", render: () => renderRecommendation() },
  { route: ROUTES.adminRewards, page: "admin-rewards", render: () => renderRewards() }
];

function adminClientRouteFor(target = location.href) {
  const current = target instanceof URL ? target : new URL(String(target), location.origin);
  const normalizedPath = current.pathname.replace(/\\/g, "/");
  return ADMIN_CLIENT_ROUTES.find((item) => {
    const routeUrl = new URL(item.route, location.origin);
    const routePath = routeUrl.pathname.replace(/\\/g, "/");
    const searchMatches = routeUrl.search ? current.search === routeUrl.search : true;
    return normalizedPath.endsWith(routePath) && searchMatches;
  });
}

function isAdminClientNavigationTarget(url) {
  return url.origin === location.origin && Boolean(adminClientRouteFor(url));
}

async function renderCurrentAdminRoute() {
  const matched = adminClientRouteFor(new URL(location.href));
  if (!matched) {
    return false;
  }
  if (document.body) {
    document.body.dataset.page = matched.page;
  }
  await matched.render();
  highlightNav();
  return true;
}

function installAdminClientNavigation() {
  document.addEventListener("click", async (event) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }
    if (event.defaultPrevented) {
      return;
    }
    const anchor = event.target instanceof Element
      ? event.target.closest(".admin-dense-shell a[href]")
      : null;
    if (!anchor || anchor.target === "_blank" || anchor.hasAttribute("data-logout")) {
      return;
    }
    const href = anchor.getAttribute("href") || "";
    if (!href || href.startsWith("#") || href.startsWith("javascript:") || href.startsWith("mailto:")) {
      return;
    }
    const url = new URL(href, location.href);
    if (!isAdminClientNavigationTarget(url)) {
      return;
    }

    event.preventDefault();
    if (url.pathname === location.pathname && url.search === location.search) {
      return;
    }
    history.pushState({ adminRoute: true }, "", `${url.pathname}${url.search}${url.hash}`);
    try {
      await renderCurrentAdminRoute();
    } catch (error) {
      console.error(error);
      toast(error.message || "后台页面切换失败", "warning");
    }
  }, { capture: true });
}

// Page bootstrap: restore session first, then route to the current page handler.
async function init() {
  injectRuntimeCss();
  installMotionSystem();
  installAdminClientNavigation();
  try {
    await restoreSession();
    mountChrome();
    highlightNav();
    const page = document.body?.dataset.page || "landing";
    if (page === "landing") await renderLanding();
    else if (page === "home-desktop" || page === "home-mobile") await renderHome();
    else if (page === "auth") renderAuth();
    else if (page === "create") await renderCreate();
    else if (page === "post-detail") await renderDetail();
    else if (page === "profile") await renderProfile();
    else if (page === "circles") await renderCircles();
    else if (page === "growth") await renderGrowth();
    else if (page === "rewards" || page === "admin-rewards") await renderRewards();
    else if (page === "admin-overview") await renderAdmin();
    else if (page === "moderation") await renderModeration();
    else if (page === "user-management-desktop" || page === "user-management-mobile") await renderUsers();
    else if (page === "recommendation-desktop" || page === "recommendation-mobile") await renderRecommendation();
  } catch (error) {
    console.error(error);
    if (error.status === 403 && isAdminRoute(location.pathname)) {
      mountChrome();
      toast("权限不足：后台功能仅管理员可访问，普通用户可以继续在论坛首页浏览、发帖、评论、收藏和签到。", "warning");
      // Do not call clearSession() here: a normal user may simply have opened an admin route.
      location.href = ROUTES.home;
      return;
    }
    setMain(stateCard("页面加载失败", error.message || "请检查后端是否已经启动。", "返回首页", ROUTES.home));
  } finally {
    // Reveal the page once the real content is mounted (see boot cloak in main.css).
    document.documentElement.classList.add("app-ready");
  }
}

document.addEventListener("DOMContentLoaded", init);

window.addEventListener("popstate", () => {
  if (document.querySelector(".admin-dense-shell")) {
    renderCurrentAdminRoute()
      .then((handled) => {
        if (!handled) {
          location.href = `${location.pathname}${location.search}`;
        }
      })
      .catch((error) => {
        console.error(error);
        location.href = `${location.pathname}${location.search}`;
      });
    return;
  }
  highlightNav();
});
