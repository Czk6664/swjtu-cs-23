import avatarStudent from "../generated/avatars/avatar-student-neutral.png";

import badgeActiveCommenter from "../generated/badges/badge-active-commenter.png";
import badgeCourseMaster from "../generated/badges/badge-course-master.png";
import badgeEarlyWarrior from "../generated/badges/badge-early-warrior.png";
import badgeHelpfulStar from "../generated/badges/badge-helpful-star.png";
import badgeSecondhandExpert from "../generated/badges/badge-secondhand-expert.png";
import badgeXipuLifeExpert from "../generated/badges/badge-xipu-life-expert.png";

import circleCareer from "../generated/circles/circle-career-internship.png";
import circleCourse from "../generated/circles/circle-course-help.png";
import circleMarket from "../generated/circles/circle-market-lost-found.png";
import circlePostgraduate from "../generated/circles/circle-postgraduate-road.png";
import circleXipu from "../generated/circles/circle-xipu-life.png";

import emptyBadges from "../generated/empty/empty-badges.png";
import emptyComments from "../generated/empty/empty-comments.png";
import emptyLoginRequired from "../generated/empty/error-login-required.png";
import emptyNetwork from "../generated/empty/error-network.png";
import emptyPermission from "../generated/empty/empty-permission.png";
import emptyPosts from "../generated/empty/empty-posts.png";
import emptyRewards from "../generated/empty/empty-rewards.png";
import emptySearch from "../generated/empty/empty-search.png";

import rewardBookmark from "../generated/rewards/reward-swjtu-bookmark.png";
import rewardClubTicket from "../generated/rewards/reward-club-ticket.png";
import rewardCoffee from "../generated/rewards/reward-campus-coffee-coupon.png";
import rewardLibrary from "../generated/rewards/reward-library-priority-coupon.png";
import rewardPrint from "../generated/rewards/reward-print-coupon.png";

import sectionAnnouncement from "../generated/sections/section-announcement.png";
import sectionCareer from "../generated/sections/section-career.png";
import sectionClub from "../generated/sections/section-club.png";
import sectionCourse from "../generated/sections/section-course-help.png";
import sectionFood from "../generated/sections/section-food.png";
import sectionLostFound from "../generated/sections/section-lost-found.png";
import sectionMarket from "../generated/sections/section-market.png";
import sectionPhotography from "../generated/sections/section-photography.png";
import sectionPostgraduate from "../generated/sections/section-postgraduate.png";
import sectionProgramming from "../generated/sections/section-programming.png";
import sectionRailway from "../generated/sections/section-railway.png";
import sectionSports from "../generated/sections/section-sports.png";
import sectionXipuLife from "../generated/sections/section-xipu-life.png";

const includes = (value, keywords) => {
  const text = String(value || "").toLowerCase();
  return keywords.some((keyword) => text.includes(keyword));
};

export function avatarAsset(role = "USER") {
  return avatarStudent;
}

export function badgeAsset(name = "") {
  if (includes(name, ["评论", "comment"])) return badgeActiveCommenter;
  if (includes(name, ["圈", "circle"])) return badgeCourseMaster;
  if (includes(name, ["文明", "civil"])) return badgeHelpfulStar;
  if (includes(name, ["收藏", "collector"])) return badgeSecondhandExpert;
  if (includes(name, ["课程", "course"])) return badgeCourseMaster;
  if (includes(name, ["弹幕", "danmaku"])) return badgeActiveCommenter;
  if (includes(name, ["早", "early"])) return badgeEarlyWarrior;
  if (includes(name, ["采纳", "帮助", "help"])) return badgeHelpfulStar;
  if (includes(name, ["发帖", "post"])) return badgeCourseMaster;
  if (includes(name, ["二手", "闲置", "secondhand"])) return badgeSecondhandExpert;
  if (includes(name, ["老用户", "veteran"])) return badgeEarlyWarrior;
  if (includes(name, ["犀浦", "生活", "xipu"])) return badgeXipuLifeExpert;
  return badgeHelpfulStar;
}

export function circleAsset(name = "") {
  if (includes(name, ["就业", "实习", "career"])) return circleCareer;
  if (includes(name, ["课程", "互助", "course"])) return circleCourse;
  if (includes(name, ["二手", "失物", "market", "lost"])) return circleMarket;
  if (includes(name, ["保研", "考研", "postgraduate"])) return circlePostgraduate;
  return circleXipu;
}

export function emptyAsset(type = "posts") {
  return {
    badges: emptyBadges,
    comments: emptyComments,
    login: emptyLoginRequired,
    network: emptyNetwork,
    permission: emptyPermission,
    posts: emptyPosts,
    rewards: emptyRewards,
    search: emptySearch
  }[type] || emptyPosts;
}

export function rewardAsset(name = "") {
  if (includes(name, ["书签", "bookmark"])) return rewardBookmark;
  if (includes(name, ["社团", "票", "club"])) return rewardClubTicket;
  if (includes(name, ["咖啡", "coffee"])) return rewardCoffee;
  if (includes(name, ["图书馆", "library"])) return rewardLibrary;
  if (includes(name, ["打印", "print"])) return rewardPrint;
  return rewardBookmark;
}

export function sectionAsset(name = "") {
  if (includes(name, ["公告", "站务"])) return sectionAnnouncement;
  if (includes(name, ["就业", "实习"])) return sectionCareer;
  if (includes(name, ["社团"])) return sectionClub;
  if (includes(name, ["课程", "互助", "讨论"])) return sectionCourse;
  if (includes(name, ["食堂", "美食"])) return sectionFood;
  if (includes(name, ["失物", "招领"])) return sectionLostFound;
  if (includes(name, ["二手", "闲置"])) return sectionMarket;
  if (includes(name, ["摄影"])) return sectionPhotography;
  if (includes(name, ["考研", "保研"])) return sectionPostgraduate;
  if (includes(name, ["编程", "程序"])) return sectionProgramming;
  if (includes(name, ["轨道", "铁路"])) return sectionRailway;
  if (includes(name, ["运动", "体育"])) return sectionSports;
  return sectionXipuLife;
}
