// Route and storage constants shared by every page entry.
export const ROUTES = {
  home: "/home_recommended_desktop/code.html",
  homeMobile: "/home_recommended/code.html",
  auth: "/login_register/code.html",
  create: "/create_post/code.html",
  detail: "/post_details/code.html",
  profile: "/profile_overview/code.html",
  circles: "/circle_center/code.html",
  growth: "/growth_center/code.html",
  rewards: "/rewards_mall/code.html",
  adminRewards: "/admin_rewards/code.html",
  admin: "/admin_overview/code.html",
  moderation: "/content_governance/code.html",
  users: "/user_management_desktop/code.html",
  recommendation: "/recommendation_strategy_desktop/code.html"
};

export const STORAGE_KEYS = {
  token: "token",
  user: "userInfo",
  draft: "swjtu-forum-draft"
};

export const REQUEST_TIMEOUT_MS = 12000;

export const DATE_FORMATTER = new Intl.DateTimeFormat("zh-CN", {
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit"
});
