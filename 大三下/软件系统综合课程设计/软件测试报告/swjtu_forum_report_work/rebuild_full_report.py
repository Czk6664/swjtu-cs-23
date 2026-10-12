from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path


WORK = Path(__file__).resolve().parent
REPORT_ROOT = WORK.parent
EVIDENCE_OLD = REPORT_ROOT / "swjtu_forum_test_evidence"
EVIDENCE_FIX = WORK / "evidence" / "20260609_fix"
FINAL = WORK / "paper_spine_output" / "final_paper"
FIG = FINAL / "figures"
SELENIUM = WORK / "selenium-junit"


FEATURES = [
    {
        "no": 1,
        "prefix": "REG",
        "module": "用户注册",
        "point": "新用户注册",
        "normal": "用户名、邮箱、密码、学号、学院、专业均合法且未被占用",
        "valid_steps": "打开登录注册页，切换到注册，输入唯一用户名、合法邮箱、6位以上密码和校园资料后提交。",
        "valid_expected": "注册成功并自动登录，跳转论坛首页，顶部显示新用户名、头像和等级。",
        "required": "用户名/邮箱/密码任一为空",
        "boundary": "密码长度分别为5位、6位、64位、65位",
        "invalid": "邮箱缺少@或用户名包含空格",
        "duplicate": "使用已存在用户名或已存在邮箱再次注册",
        "unauth": "已登录用户再次访问注册页并提交另一个账号",
        "persist": "注册成功后刷新首页并重新进入个人中心",
        "mobile": "390px移动端注册表单输入与按钮布局",
        "special": "用户名或学院专业中包含中文、连字符和数字",
        "empty": "后端短时不可用或注册接口返回错误",
    },
    {
        "no": 2,
        "prefix": "LOGIN",
        "module": "用户登录",
        "point": "账号密码登录",
        "normal": "admin/admin123456 或已注册普通用户账号",
        "valid_steps": "退出当前登录态，打开登录页，输入正确用户名和密码后提交。",
        "valid_expected": "登录成功，写入会话，跳转首页或next参数目标页。",
        "required": "用户名为空或密码为空",
        "boundary": "密码长度为0、1、6、64位",
        "invalid": "正确用户名+错误密码，不存在用户名+任意密码",
        "duplicate": "连续点击登录按钮两次或重复提交表单",
        "unauth": "未登录直接访问需要权限的发帖页后被引导登录",
        "persist": "登录成功后刷新页面、打开新页面仍保持登录态",
        "mobile": "移动端登录表单是否可见、按钮是否可点击",
        "special": "用户名首尾带空格、大小写变化",
        "empty": "登录接口500或网络超时时显示错误提示且按钮恢复",
    },
    {
        "no": 3,
        "prefix": "HOME",
        "module": "帖子浏览",
        "point": "首页帖子列表",
        "normal": "默认首页公开帖子列表",
        "valid_steps": "打开首页，等待列表加载，观察帖子卡片、作者、版块、摘要、浏览/回复/点赞/收藏数据。",
        "valid_expected": "列表至少显示种子帖子，字段完整，游客和登录用户均可浏览。",
        "required": "列表容器为空但后端有数据",
        "boundary": "第一页0条、1条、满页、多页数据",
        "invalid": "帖子数据缺少作者、版块或摘要字段",
        "duplicate": "刷新首页或前进后退导致重复卡片",
        "unauth": "游客访问首页但不应出现发帖、收藏等已登录状态",
        "persist": "新发帖后返回首页能看到新增帖子或列表计数变化",
        "mobile": "移动端首页卡片换行、按钮和文字不重叠",
        "special": "标题包含中文、英文、数字和较长标签",
        "empty": "后端返回空列表时展示空状态而非白屏",
    },
    {
        "no": 4,
        "prefix": "SEC",
        "module": "帖子浏览",
        "point": "按版块筛选帖子",
        "normal": "选择校园生活、课程互助等真实版块",
        "valid_steps": "首页选择版块下拉框，提交筛选，检查URL和列表内容。",
        "valid_expected": "URL带sectionId，列表仅显示所选版块帖子，版块标签与筛选条件一致。",
        "required": "未选择版块直接筛选",
        "boundary": "sectionId为最小值1、最大种子版块ID",
        "invalid": "URL手工输入不存在sectionId或非数字sectionId",
        "duplicate": "重复选择同一版块不应叠加查询条件",
        "unauth": "游客按版块筛选仍可浏览公开帖子",
        "persist": "刷新筛选结果页后筛选条件仍保留",
        "mobile": "移动端版块下拉框和提交按钮可操作",
        "special": "版块名为中文长文本时卡片布局正常",
        "empty": "筛选到无帖子版块时展示无结果提示",
    },
    {
        "no": 5,
        "prefix": "SEARCH",
        "module": "帖子浏览",
        "point": "帖子搜索",
        "normal": "关键词：签到、保研、二手、课程",
        "valid_steps": "在首页搜索框输入中文关键词并提交，检查URL和结果列表。",
        "valid_expected": "URL带keyword参数，结果标题或摘要命中关键词，搜索状态清晰。",
        "required": "关键词为空或只包含空格",
        "boundary": "关键词1个汉字、50个字符、超长字符",
        "invalid": "关键词包含SQL片段、尖括号或URL保留字符",
        "duplicate": "连续搜索同一关键词不会重复渲染结果",
        "unauth": "游客搜索公开帖子不被强制登录",
        "persist": "刷新搜索结果页后关键词仍保留",
        "mobile": "移动端搜索框宽度、按钮和结果卡片不遮挡",
        "special": "中英文混合关键词和前后空格",
        "empty": "无命中结果时显示无结果而非报错",
    },
    {
        "no": 6,
        "prefix": "POST",
        "module": "发帖",
        "point": "发布新帖子",
        "normal": "标题、版块、标签、正文均合法",
        "valid_steps": "登录后进入发帖页，填写标题、选择版块、输入标签和正文，提交发布。",
        "valid_expected": "发布成功并跳转帖子详情，详情页显示标题、正文、标签和已发布状态。",
        "required": "标题为空、正文为空或未选择版块",
        "boundary": "标题1/2/100/101字符，正文最小长度和超长正文",
        "invalid": "正文包含敏感词或风险引流内容",
        "duplicate": "连续点击发布按钮两次不应生成重复帖子",
        "unauth": "未登录访问发帖页应跳转登录页",
        "persist": "发布后刷新详情页内容仍存在",
        "mobile": "移动端发帖表单滚动、文本域和提交按钮可操作",
        "special": "标题/标签包含中文、英文逗号、井号和空格",
        "empty": "后端发布失败时保留草稿并显示错误",
    },
    {
        "no": 7,
        "prefix": "COMMENT",
        "module": "评论",
        "point": "发表评论",
        "normal": "登录用户在公开帖子详情页输入有效评论",
        "valid_steps": "进入帖子详情，在评论框输入有效文本并提交。",
        "valid_expected": "评论区新增记录，显示评论作者和内容，回复数增加。",
        "required": "评论内容为空或只输入空格",
        "boundary": "评论1字、2字、500字、501字",
        "invalid": "评论包含脚本标签或违规词",
        "duplicate": "快速连续点击提交不应重复生成多条相同评论",
        "unauth": "未登录提交评论应跳转登录或提示登录",
        "persist": "刷新详情页后评论仍存在",
        "mobile": "移动端评论框、键盘遮挡和按钮位置",
        "special": "评论包含表情符号、换行和中文标点",
        "empty": "帖子不存在或被隐藏时不能提交评论",
    },
    {
        "no": 8,
        "prefix": "LIKE",
        "module": "互动",
        "point": "点赞帖子",
        "normal": "登录用户首次点赞公开帖子",
        "valid_steps": "进入详情页点击点赞按钮，观察计数和按钮状态。",
        "valid_expected": "点赞成功，计数+1，按钮进入已点赞状态。",
        "required": "缺失postId或按钮未绑定帖子",
        "boundary": "点赞数从0到1、从999到1000",
        "invalid": "postId不存在或为非数字",
        "duplicate": "再次点击同一按钮应取消点赞或保持幂等",
        "unauth": "游客点赞应提示登录",
        "persist": "刷新详情页后点赞状态与计数一致",
        "mobile": "移动端点赞按钮可点击且不遮挡",
        "special": "多用户对同一帖子点赞计数累计",
        "empty": "后端点赞接口失败时计数回滚",
    },
    {
        "no": 9,
        "prefix": "FAV",
        "module": "互动",
        "point": "收藏帖子",
        "normal": "登录用户首次收藏公开帖子",
        "valid_steps": "进入详情页点击收藏按钮，观察计数和提示。",
        "valid_expected": "收藏成功，收藏数+1，个人中心收藏列表可追踪。",
        "required": "缺失postId或按钮未绑定帖子",
        "boundary": "收藏数从0到1、从999到1000",
        "invalid": "postId不存在、帖子已隐藏或无权限",
        "duplicate": "再次点击同一按钮应取消收藏或保持幂等",
        "unauth": "游客收藏应提示登录",
        "persist": "刷新详情页和个人中心后收藏状态一致",
        "mobile": "移动端收藏按钮可点击且文本不溢出",
        "special": "多个帖子连续收藏后列表排序正确",
        "empty": "收藏接口失败时页面提示并不错误增加计数",
    },
    {
        "no": 10,
        "prefix": "PROFILE",
        "module": "个人中心",
        "point": "编辑个人资料",
        "normal": "修改简介、学院、专业等资料",
        "valid_steps": "登录进入个人中心，编辑简介、学院和专业，点击保存。",
        "valid_expected": "提示资料已保存，刷新后新资料仍显示。",
        "required": "可选字段为空保存",
        "boundary": "简介0字、1字、500字、501字",
        "invalid": "简介包含脚本标签或超长连续字符",
        "duplicate": "重复点击保存按钮不应产生错误",
        "unauth": "未登录访问个人中心跳转登录",
        "persist": "退出再登录后资料仍保留",
        "mobile": "移动端表单字段和按钮不被遮挡",
        "special": "学院专业包含中文、英文括号和数字",
        "empty": "资料保存接口失败时保留输入并提示",
    },
    {
        "no": 11,
        "prefix": "VERIFY",
        "module": "个人中心",
        "point": "校园身份认证",
        "normal": "种子学号与校园邮箱匹配",
        "valid_steps": "在个人中心输入有效学号和校园邮箱，提交认证。",
        "valid_expected": "认证成功，显示已认证状态，并同步学院、专业等校园身份信息。",
        "required": "学号为空或校园邮箱为空",
        "boundary": "学号7位、8位、9位",
        "invalid": "8位但不存在学号、邮箱与学号不匹配",
        "duplicate": "已认证用户再次提交认证",
        "unauth": "未登录提交认证应被拒绝",
        "persist": "刷新个人中心后已认证状态仍存在",
        "mobile": "移动端认证表单输入和提示正常",
        "special": "校园邮箱大小写、前后空格",
        "empty": "认证数据表无记录时提示未找到身份信息",
    },
    {
        "no": 12,
        "prefix": "CHECKIN",
        "module": "成长系统",
        "point": "每日签到",
        "normal": "当天未签到用户点击今日签到",
        "valid_steps": "登录进入成长中心，点击今日签到，查看积分、签到记录和积分历史。",
        "valid_expected": "签到成功，按钮状态更新，积分增加，记录和流水一致。",
        "required": "未加载用户成长资料时点击签到",
        "boundary": "当天首次签到、当天重复签到、跨天签到",
        "invalid": "手工调用不存在日期或非法用户签到",
        "duplicate": "快速连续点击签到按钮只产生一次记录",
        "unauth": "未登录访问成长中心跳转登录",
        "persist": "刷新成长中心后签到记录仍存在",
        "mobile": "移动端签到按钮和积分卡片布局正常",
        "special": "连续签到天数达到等级临界值",
        "empty": "签到接口失败时不应错误增加积分",
    },
    {
        "no": 13,
        "prefix": "REWARD",
        "module": "积分商城",
        "point": "积分兑换奖品",
        "normal": "积分足够或不足两类用户兑换上架奖品",
        "valid_steps": "登录进入积分商城，查看奖品，点击申请兑换，查看我的兑换记录。",
        "valid_expected": "积分不足时给出明确提示；积分足够时创建待审核兑换记录，刷新页面不报错。",
        "required": "奖品ID为空或按钮未绑定奖品",
        "boundary": "积分低于价格、等于价格、高于价格；库存0和库存1",
        "invalid": "兑换不存在奖品或已下架奖品",
        "duplicate": "快速重复点击兑换按钮不应生成异常记录",
        "unauth": "未登录访问积分商城跳转登录",
        "persist": "兑换后刷新商城，我的兑换记录接口仍返回200",
        "mobile": "移动端奖品卡和兑换记录布局正常",
        "special": "管理员审核后状态从待审核到通过/驳回",
        "empty": "兑换记录为空时显示空状态而不是页面加载失败",
    },
    {
        "no": 14,
        "prefix": "NOTICE",
        "module": "通知中心",
        "point": "查看通知",
        "normal": "登录后点击顶部通知按钮",
        "valid_steps": "登录首页，点击通知按钮，观察下拉面板、未读徽标和通知列表。",
        "valid_expected": "通知面板可见，hidden=false，display不为none，可读取空状态或通知列表。",
        "required": "通知根节点未挂载时点击",
        "boundary": "0条通知、1条通知、20条通知、99+未读",
        "invalid": "通知接口返回错误或单条通知targetId失效",
        "duplicate": "连续打开/关闭面板，aria-expanded与可见性同步",
        "unauth": "游客不显示通知按钮",
        "persist": "标记已读后刷新，未读数不回弹",
        "mobile": "390px宽度通知面板不超出屏幕",
        "special": "通知内容为长中文和长英文链接",
        "empty": "无通知时显示空状态而不是一直加载中",
    },
    {
        "no": 15,
        "prefix": "FOLLOW",
        "module": "关注",
        "point": "关注/取消关注用户",
        "normal": "登录用户在帖子详情页关注作者",
        "valid_steps": "进入帖子详情页，点击关注按钮，再次点击取消关注。",
        "valid_expected": "按钮在关注/已关注之间切换，粉丝数同步变化。",
        "required": "关注按钮缺失targetUserId",
        "boundary": "粉丝数从0到1、从1到0",
        "invalid": "关注不存在用户或已封禁用户",
        "duplicate": "重复点击关注/取消关注保持幂等",
        "unauth": "游客点击关注提示登录",
        "persist": "刷新详情页后关注状态仍正确",
        "mobile": "移动端作者区关注按钮可点击",
        "special": "不允许关注自己",
        "empty": "关注接口失败时按钮状态回滚",
    },
]


EXECUTED = {
    ("REG", 1): ("通过", "01_register_page.png;02_register_success_home.png", "注册后跳转首页，显示新用户信息。"),
    ("LOGIN", 1): ("通过", "03_login_page_after_logout.png;04_login_success_home.png", "账号密码登录成功并恢复用户会话。"),
    ("HOME", 1): ("通过", "05_home_post_list.png", "首页展示公开帖子列表和互动计数。"),
    ("SEC", 1): ("通过", "06_section_filter_campus_life.png", "sectionId筛选生效，结果属于校园生活版块。"),
    ("SEARCH", 1): ("通过", "07_search_keyword_qiandao.png", "中文关键词搜索返回命中结果。"),
    ("POST", 1): ("通过", "08_create_post_page.png;09_create_post_success_detail.png", "发布成功并进入详情页。"),
    ("POST", 9): ("失败", "09_create_post_success_detail.png", "详情页部分中文按钮/静态提示出现乱码，记录为中等缺陷。"),
    ("COMMENT", 1): ("通过", "10_comment_success.png", "评论新增并在详情页可见。"),
    ("LIKE", 1): ("通过", "11_like_success.png", "点赞计数更新。"),
    ("FAV", 1): ("通过", "12_favorite_success.png", "收藏计数更新。"),
    ("PROFILE", 1): ("通过", "13_profile_page_before_edit.png;14_profile_edit_success.png", "资料保存成功并回显。"),
    ("VERIFY", 1): ("通过", "15_campus_identity_success.png", "种子学号和邮箱通过认证。"),
    ("VERIFY", 4): ("通过", "16_campus_identity_valid_retry.png;17_campus_identity_seed_sample.png", "不存在学号和重试路径提示明确。"),
    ("VERIFY", 5): ("失败", "14_profile_edit_success.png;15_campus_identity_success.png", "认证覆盖学院专业前缺少二次确认，记录为低优先体验问题。"),
    ("CHECKIN", 1): ("通过", "18_growth_center_before_checkin.png;19_daily_checkin_success_or_repeat.png", "签到成功或重复签到提示可见。"),
    ("CHECKIN", 7): ("失败", "19_daily_checkin_success_or_repeat.png", "签到记录展示积分与积分流水不完全一致，记录为中等缺陷。"),
    ("REWARD", 1): ("通过", "20_rewards_mall_before_redeem.png", "奖品列表可见，积分不足提示可触发。"),
    ("REWARD", 7): ("通过", "BUG-002-rewards-redemptions.png;verification-summary.json", "修复后兑换记录接口返回200，页面刷新不再加载失败。"),
    ("NOTICE", 1): ("通过", "BUG-001-notification-desktop.png;verification-summary.json", "修复后通知面板hidden=false且display=flex。"),
    ("NOTICE", 8): ("通过", "BUG-001-notification-mobile.png", "移动端通知面板截图通过。"),
    ("FOLLOW", 1): ("通过", "23_follow_page_before.png;24_follow_success.png", "关注按钮切换为已关注。"),
    ("FOLLOW", 5): ("通过", "25_unfollow_success.png", "再次点击后取消关注。"),
}


VARIANTS = [
    ("有效等价类", "P0", "Chrome", "normal", "valid_steps", "valid_expected"),
    ("边界值", "P1", "Chrome/设计", "required", None, "系统拒绝提交或给出必填提示，数据不被写入。"),
    ("边界值", "P1", "Chrome/设计", "boundary", None, "边界内数据被接受，边界外数据被拒绝并提示原因。"),
    ("等价类", "P1", "Chrome/设计", "invalid", None, "非法输入被拦截或后端返回业务错误，页面不出现白屏。"),
    ("判定表", "P1", "Chrome", "duplicate", None, "重复操作遵循幂等或状态切换规则，不产生脏数据。"),
    ("判定表", "P0", "Chrome", "unauth", None, "未授权用户被引导登录或明确拒绝，不能执行受限操作。"),
    ("状态迁移", "P1", "Chrome", "persist", None, "刷新或重新进入后状态与数据库保持一致。"),
    ("等价类", "P2", "Chrome移动端", "mobile", None, "窄屏下控件可见可点，文字不重叠。"),
    ("边界值", "P2", "Chrome/设计", "special", None, "特殊字符按规则保存、转义或提示，不破坏页面。"),
    ("等价类+判定表", "P2", "IE/Edge IE模式设计", "empty", None, "异常或空数据路径有兜底提示，不影响其他功能。"),
]


BUGS = [
    {
        "id": "BUG-001",
        "module": "通知中心",
        "severity": "高",
        "title": "点击通知后面板DOM存在但仍被hidden/display:none隐藏",
        "steps": "登录首页，点击顶部通知按钮，检查通知面板可见性。",
        "expected": "面板展开，可查看通知列表或空状态。",
        "actual": "旧版本仅改变按钮状态，面板仍不可见；修复后hidden=false、display=flex。",
        "status": "已修复",
        "evidence": "22_notification_center_open.png;BUG-001-notification-desktop.png;BUG-001-notification-mobile.png",
    },
    {
        "id": "BUG-002",
        "module": "积分商城",
        "severity": "高",
        "title": "兑换后刷新我的兑换记录出现500/页面加载失败",
        "steps": "积分足够账号申请兑换，刷新积分商城或调用/growth/redemptions。",
        "expected": "兑换记录返回200并显示待审核记录或空状态。",
        "actual": "旧版本实体序列化触发懒加载异常；修复后DTO返回200，页面不再加载失败。",
        "status": "已修复",
        "evidence": "21_rewards_redeem_result.png;BUG-002-rewards-redemptions.png;verification-summary.json",
    },
    {
        "id": "BUG-003",
        "module": "便携包启动",
        "severity": "高",
        "title": "旧H2数据库升级时comments.accepted非空列无默认值导致启动失败",
        "steps": "替换新jar后使用既有demo数据库启动后端。",
        "expected": "数据库自动迁移完成，服务启动并返回/api/sections=200。",
        "actual": "旧构建报NULL not allowed for column accepted；已增加boolean default false并重新打包。",
        "status": "已修复",
        "evidence": "verification-summary.json",
    },
    {
        "id": "BUG-004",
        "module": "发帖",
        "severity": "中",
        "title": "部分详情页按钮或静态文案出现中文乱码",
        "steps": "发布新帖子后进入详情页，观察部分按钮和提示文案。",
        "expected": "所有中文文案按UTF-8正常显示。",
        "actual": "个别静态页面/按钮有乱码，影响观感但不阻断主流程。",
        "status": "待修复",
        "evidence": "09_create_post_success_detail.png",
    },
    {
        "id": "BUG-005",
        "module": "成长系统",
        "severity": "中",
        "title": "签到记录区域积分展示与积分流水不完全一致",
        "steps": "首次签到后同时查看成长中心签到记录和积分历史。",
        "expected": "签到记录与积分流水均显示相同的增加积分。",
        "actual": "主积分增加，但部分签到记录展示为+0，容易造成理解偏差。",
        "status": "待修复",
        "evidence": "19_daily_checkin_success_or_repeat.png",
    },
    {
        "id": "BUG-006",
        "module": "个人中心",
        "severity": "低",
        "title": "校园身份认证覆盖学院专业前缺少二次确认",
        "steps": "先手工编辑学院专业，再使用种子学号完成校园身份认证。",
        "expected": "覆盖资料前提示用户确认或展示变更内容。",
        "actual": "认证成功会同步覆盖部分资料，功能正确但体验提示不足。",
        "status": "待优化",
        "evidence": "14_profile_edit_success.png;15_campus_identity_success.png",
    },
]


JAVA = r'''package com.swjtu.forum;

import org.junit.jupiter.api.*;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ForumBlackBoxTest {
    private static final String BASE_URL = System.getProperty("forum.baseUrl", "http://localhost:4173");
    private static WebDriver driver;
    private static WebDriverWait wait;
    private static final String ADMIN = "admin";
    private static final String ADMIN_PASSWORD = "admin123456";

    @BeforeAll
    static void setUp() {
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--remote-allow-origins=*", "--window-size=1440,1000");
        options.setBinary("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe");
        driver = new ChromeDriver(options);
        wait = new WebDriverWait(driver, Duration.ofSeconds(15));
    }

    @AfterAll
    static void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    @Test
    @Order(1)
    void loginBrowseFilterAndSearch() {
        loginAsAdmin();
        driver.get(BASE_URL + "/home_recommended_desktop/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("main article")));
        assertTrue(driver.findElements(By.cssSelector("main article")).size() >= 1);

        Select section = new Select(driver.findElement(By.cssSelector("main select")));
        section.selectByIndex(1);
        click(By.cssSelector("[data-search-form] button[type='submit']"));
        wait.until(ExpectedConditions.urlContains("sectionId="));

        driver.get(BASE_URL + "/home_recommended_desktop/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-search-form] input[name='keyword']")));
        driver.findElement(By.cssSelector("[data-search-form] input[name='keyword']")).sendKeys("签到");
        click(By.cssSelector("[data-search-form] button[type='submit']"));
        wait.until(ExpectedConditions.or(
                ExpectedConditions.urlContains("keyword="),
                ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "签到")
        ));
    }

    @Test
    @Order(2)
    void notificationPanelMustBecomeVisible() {
        loginAsAdmin();
        driver.get(BASE_URL + "/home_recommended_desktop/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-notif-toggle]")));
        click(By.cssSelector("[data-notif-toggle]"));
        WebElement panel = wait.until(ExpectedConditions.presenceOfElementLocated(By.cssSelector("[data-notif-panel]")));
        Boolean hidden = (Boolean) ((JavascriptExecutor) driver).executeScript("return arguments[0].hidden;", panel);
        String display = (String) ((JavascriptExecutor) driver).executeScript("return getComputedStyle(arguments[0]).display;", panel);
        assertFalse(hidden, "notification panel should not be hidden after clicking bell");
        assertNotEquals("none", display, "notification panel display should not be none");
        assertEquals("true", driver.findElement(By.cssSelector("[data-notif-toggle]")).getAttribute("aria-expanded"));
    }

    @Test
    @Order(3)
    void rewardsAndRedemptionsMustLoadWithoutServerError() {
        loginAsAdmin();
        driver.get(BASE_URL + "/rewards_mall/code.html");
        wait.until(ExpectedConditions.not(ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "页面加载失败")));
        assertFalse(driver.getPageSource().contains("Internal Server Error"));
        assertTrue(driver.getPageSource().contains("积分") || driver.findElements(By.cssSelector("[data-redeem]")).size() > 0);
    }

    @Test
    @Order(4)
    void createCommentLikeFavoriteAndFollow() {
        loginAsAdmin();
        driver.get(BASE_URL + "/post_details/code.html?id=1");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("body")));

        if (driver.findElements(By.cssSelector("[data-comment-form] textarea[name='content']")).size() > 0) {
            driver.findElement(By.cssSelector("[data-comment-form] textarea[name='content']")).sendKeys("Selenium black-box comment");
            click(By.cssSelector("[data-comment-form] button[type='submit']"));
            wait.until(ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "Selenium black-box comment"));
        }
        if (driver.findElements(By.cssSelector("[data-like-post]")).size() > 0) {
            click(By.cssSelector("[data-like-post]"));
        }
        if (driver.findElements(By.cssSelector("[data-favorite]")).size() > 0) {
            click(By.cssSelector("[data-favorite]"));
        }
        if (driver.findElements(By.cssSelector("[data-follow]")).size() > 0) {
            click(By.cssSelector("[data-follow]"));
            wait.until(ExpectedConditions.presenceOfElementLocated(By.cssSelector("[data-follow]")));
        }
    }

    private static void loginAsAdmin() {
        driver.get(BASE_URL + "/home_recommended_desktop/code.html");
        try {
            new WebDriverWait(driver, Duration.ofSeconds(4))
                    .until(ExpectedConditions.presenceOfElementLocated(By.cssSelector("[data-notif-toggle]")));
            return;
        } catch (TimeoutException ignored) {
            ((JavascriptExecutor) driver).executeScript("window.localStorage.clear(); window.sessionStorage.clear();");
        }

        driver.get(BASE_URL + "/login_register/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-auth-form='login']")));
        WebElement username = driver.findElement(By.cssSelector("[data-auth-form='login'] input[name='username']"));
        username.clear();
        username.sendKeys(ADMIN);
        WebElement password = driver.findElement(By.cssSelector("[data-auth-form='login'] input[name='password']"));
        password.clear();
        password.sendKeys(ADMIN_PASSWORD);
        click(By.cssSelector("[data-auth-form='login'] [data-auth-submit]"));
        wait.until(ExpectedConditions.or(
                ExpectedConditions.urlContains("home_recommended"),
                ExpectedConditions.presenceOfElementLocated(By.cssSelector("[data-notif-toggle]"))
        ));
    }

    private static void click(By locator) {
        StaleElementReferenceException last = null;
        for (int i = 0; i < 3; i++) {
            try {
                WebElement element = wait.until(ExpectedConditions.refreshed(
                        ExpectedConditions.presenceOfElementLocated(locator)));
                ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block:'center'});", element);
                ((JavascriptExecutor) driver).executeScript("arguments[0].click();", element);
                return;
            } catch (StaleElementReferenceException error) {
                last = error;
                try {
                    Thread.sleep(300);
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                }
            }
        }
        throw last;
    }
}
'''


def tex_escape(value: object) -> str:
    text = str(value or "")
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(repl.get(ch, ch) for ch in text)


def build_cases() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for feature in FEATURES:
        for idx, (method, priority, browser, data_key, steps_key, expected_template) in enumerate(VARIANTS, start=1):
            case_id = f"TC-{feature['prefix']}-{idx:03d}"
            result, evidence, actual = EXECUTED.get((feature["prefix"], idx), ("未执行", "", "设计用例，作为后续回归和兼容性测试补充。"))
            steps = feature[steps_key] if steps_key else f"围绕“{feature[data_key]}”构造输入或状态，执行{feature['point']}流程并观察页面、接口与数据变化。"
            expected = feature[expected_template] if expected_template in feature else expected_template
            rows.append({
                "编号": case_id,
                "一级功能": feature["module"],
                "二级功能": feature["point"],
                "测试方法": method,
                "优先级": priority,
                "执行环境": browser,
                "前置条件": "便携包后端8080、前端4173已启动；按用例需要准备游客、普通用户或管理员登录态。",
                "测试数据": feature[data_key],
                "测试步骤": steps,
                "预期结果": expected,
                "实际结果": actual,
                "执行结果": result,
                "证据": evidence,
            })
    return rows


def write_csv_md(cases: list[dict[str, str]]) -> None:
    fields = list(cases[0].keys())
    with (WORK / "测试用例.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(cases)
    with (WORK / "测试用例.md").open("w", encoding="utf-8") as f:
        f.write("|" + "|".join(fields) + "|\n")
        f.write("|" + "|".join(["---"] * len(fields)) + "|\n")
        for row in cases:
            f.write("|" + "|".join(str(row[k]).replace("|", "；") for k in fields) + "|\n")

    bug_fields = ["id", "module", "severity", "title", "steps", "expected", "actual", "status", "evidence"]
    with (WORK / "缺陷清单.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=bug_fields)
        writer.writeheader()
        writer.writerows(BUGS)
    with (WORK / "缺陷清单.md").open("w", encoding="utf-8") as f:
        f.write("|编号|模块|严重程度|标题|状态|证据|\n|---|---|---|---|---|---|\n")
        for bug in BUGS:
            f.write(f"|{bug['id']}|{bug['module']}|{bug['severity']}|{bug['title']}|{bug['status']}|{bug['evidence']}|\n")


def copy_figures() -> dict[str, str]:
    FIG.mkdir(parents=True, exist_ok=True)
    mapping = {}
    for src_dir in [EVIDENCE_OLD, EVIDENCE_FIX]:
        if not src_dir.exists():
            continue
        for src in src_dir.iterdir():
            if src.suffix.lower() not in {".png", ".jpg", ".jpeg", ".json"}:
                continue
            dst = FIG / src.name
            shutil.copy2(src, dst)
            mapping[src.name] = f"figures/{src.name}"
    return mapping


def write_selenium() -> None:
    java_path = SELENIUM / "src" / "test" / "java" / "com" / "swjtu" / "forum" / "ForumBlackBoxTest.java"
    java_path.parent.mkdir(parents=True, exist_ok=True)
    java_path.write_text(JAVA, encoding="utf-8")


def paragraph(feature: dict[str, object]) -> str:
    return (
        f"{feature['module']}—{feature['point']}的测试重点是验证正常路径、异常输入、权限控制、重复操作和刷新后的状态一致性。"
        f"本功能采用等价类划分把数据分为有效数据、缺失必填数据、非法格式数据、重复状态数据和异常返回数据；"
        f"采用边界值分析覆盖长度、数量、积分、学号、未读数等临界点；采用判定表分析登录/未登录、资源存在/不存在、"
        f"积分足够/不足、已关注/未关注等组合条件。针对该功能共设计10条用例，其中P0用例优先验证最可能阻断主流程的路径，"
        f"P1用例覆盖常见失败路径，P2用例补充兼容性、移动端和异常兜底。测试数据包括：{feature['normal']}；"
        f"同时还覆盖{feature['required']}、{feature['boundary']}、{feature['invalid']}等输入。"
        f"这样设计的原因是论坛系统的功能之间存在链式依赖：登录影响发帖、评论和积分，帖子详情影响点赞、收藏和关注，"
        f"成长积分又影响商城兑换，因此每个功能点既要看本页面反馈，也要看刷新后数据是否仍然一致。"
    )


def make_latex(cases: list[dict[str, str]], figures: dict[str, str], summary: dict[str, object]) -> str:
    rows_fp = "\n".join(
        f"{f['no']} & {tex_escape(f['module'])} & {tex_escape(f['point'])} & 10 \\\\"
        for f in FEATURES
    )
    case_rows = "\n".join(
        f"{tex_escape(c['编号'])} & {tex_escape(c['一级功能'])} & {tex_escape(c['二级功能'])} & "
        f"{tex_escape(c['测试方法'])} & {tex_escape(c['优先级'])} & {tex_escape(c['执行结果'])} & "
        f"{tex_escape(c['测试数据'])} & {tex_escape(c['预期结果'])} \\\\"
        for c in cases
    )
    bug_rows = "\n".join(
        f"{tex_escape(b['id'])} & {tex_escape(b['module'])} & {tex_escape(b['severity'])} & "
        f"{tex_escape(b['title'])} & {tex_escape(b['status'])} & {tex_escape(b['evidence'])} \\\\"
        for b in BUGS
    )
    analysis = "\n\n".join(f"\\subsection{{{tex_escape(f['no'])}. {tex_escape(f['module'])}：{tex_escape(f['point'])}}}\n{tex_escape(paragraph(f))}" for f in FEATURES)
    fig_blocks = []
    selected = [
        ("01_register_page.png", "用户注册页面"),
        ("05_home_post_list.png", "首页帖子列表"),
        ("09_create_post_success_detail.png", "发帖成功详情页"),
        ("15_campus_identity_success.png", "校园身份认证成功"),
        ("19_daily_checkin_success_or_repeat.png", "每日签到结果"),
        ("BUG-001-notification-desktop.png", "修复后通知中心桌面端展开"),
        ("BUG-001-notification-mobile.png", "修复后通知中心移动端展开"),
        ("BUG-002-rewards-redemptions.png", "修复后积分商城和兑换记录页面"),
    ]
    for name, caption in selected:
        if name in figures:
            fig_blocks.append(
                "\\begin{figure}[H]\n\\centering\n"
                f"\\includegraphics[width=0.88\\textwidth]{{{figures[name]}}}\n"
                f"\\caption{{{tex_escape(caption)}}}\n\\end{{figure}}"
            )
    return rf"""\documentclass[UTF8,zihao=-4]{{ctexart}}
\usepackage[a4paper,margin=1.8cm]{{geometry}}
\usepackage{{longtable,booktabs,array,graphicx,float,xcolor,hyperref,listings}}
\usepackage{{caption}}
\setCJKmainfont{{SimSun}}
\setCJKsansfont{{Microsoft YaHei}}
\setmainfont{{Times New Roman}}
\hypersetup{{colorlinks=true,linkcolor=blue,urlcolor=blue}}
\lstset{{basicstyle=\ttfamily\scriptsize,breaklines=true,frame=single,columns=fullflexible}}
\newcolumntype{{P}}[1]{{>{{\raggedright\arraybackslash}}p{{#1}}}}
\title{{软件系统综合课程设计——练习1（黑盒+功能测试）\\西南交通大学校园论坛系统测试报告}}
\author{{测试人员：课程设计小组成员}}
\date{{2026年6月9日}}
\begin{{document}}
\maketitle
\tableofcontents
\newpage

\section{{项目名称、简介与测试范围}}
项目名称为“西南交通大学校园论坛系统（SWJTU Forum）”。被测对象是便携运行包：\texttt{{D:\textbackslash 大三下\textbackslash 软件系统综合课程设计\textbackslash 课设\textbackslash jiaodaluntan\textbackslash release\textbackslash swjtu-forum-portable}}。系统采用前后端分离方式运行，前端由内置静态服务器提供，后端为Spring Boot应用，demo profile使用本地H2数据库，适合课程设计验收、黑盒测试和功能回归测试。

本系统面向校园论坛场景，核心业务包括用户注册、账号密码登录、首页帖子浏览、按版块筛选、帖子搜索、发布新帖、发表评论、点赞、收藏、编辑个人资料、校园身份认证、每日签到、积分商城兑换、通知中心和关注/取消关注用户。测试范围严格对应题目给出的15个功能点，每个功能点设计10条黑盒测试用例，共150条。用例并非简单堆数量，而是围绕等价类、边界值和判定表三类黑盒方法展开，优先覆盖能阻断主流程或发现缺陷的关键路径。

\section{{测试功能点清单与个人分工}}
本次报告负责的功能点如下。每个功能点均完成10条测试用例设计，部分P0/P1用例已经通过Chrome和自动化脚本执行，兼容性与低风险异常项作为设计用例纳入后续回归。

\begin{{longtable}}{{P{{1.2cm}}P{{3cm}}P{{6cm}}P{{2cm}}}}
\toprule
序号 & 一级功能 & 二级功能 & 用例数\\
\midrule
\endfirsthead
\toprule
序号 & 一级功能 & 二级功能 & 用例数\\
\midrule
\endhead
{rows_fp}
\bottomrule
\end{{longtable}}

\section{{测试方法选择与设计思路}}
本次采用黑盒测试为主，不依赖源码内部实现推导结果，而是从用户输入、页面状态、接口响应和业务规则出发设计测试。等价类划分用于区分有效输入、无效输入、权限不足、资源不存在、空数据、重复操作等类别；边界值分析用于覆盖长度、数量、积分、学号、未读数、分页数量等容易出错的临界点；判定表用于表达多个条件组合，例如“是否登录、资源是否存在、积分是否足够、是否已关注、是否已签到”等条件对系统动作和提示的影响。

测试执行策略上，Chrome作为主测浏览器，因为课程便携包的前端脚本、截图工具和Selenium WebDriver均能稳定在Chrome上执行；IE已经停止维护，本报告不虚构IE实测结果，而是把IE/Edge IE模式作为兼容性设计项列入用例，明确标注“设计未执行”。这种记录方式符合实验要求中“根据自己判断决定在IE、Chrome执行哪些测试用例”的要求，也避免把没有实际运行的内容写成通过。

\section{{测试环境}}
\begin{{itemize}}
\item 操作系统：Windows，本机时区Asia/Shanghai。
\item 被测系统：swjtu-forum-portable便携包。
\item 后端：内置Java运行时启动Spring Boot，端口8080，demo profile，H2本地数据库。
\item 前端：app/frontend-server.jar，端口4173，代理/api到后端。
\item 浏览器：Google Chrome，桌面视口1440×1000，移动端视口390×844。
\item 自动化工具：Selenium WebDriver + JUnit 5；补充使用Playwright/Chrome生成回归截图。
\item 编译工具：XeLaTeX，用于从本报告的TeX源文件生成PDF。
\end{{itemize}}

\section{{功能点逐项分析}}
{analysis}

\section{{测试用例列表}}
下表为150条测试用例的核心字段。完整CSV和Markdown文件同步输出到报告工作目录，便于教师检查和后续复跑。

{{\scriptsize
\begin{{longtable}}{{P{{1.8cm}}P{{1.7cm}}P{{2.2cm}}P{{1.8cm}}P{{1cm}}P{{1.2cm}}P{{4.1cm}}P{{5.3cm}}}}
\toprule
编号 & 一级功能 & 二级功能 & 方法 & 优先级 & 结果 & 测试数据 & 预期结果\\
\midrule
\endfirsthead
\toprule
编号 & 一级功能 & 二级功能 & 方法 & 优先级 & 结果 & 测试数据 & 预期结果\\
\midrule
\endhead
{case_rows}
\bottomrule
\end{{longtable}}
}}

\section{{自动化脚本开发与执行}}
按照实验要求，已将关键黑盒用例转化为Selenium + WebDriver + JUnit脚本。脚本覆盖登录、首页列表、版块筛选、帖子搜索、通知中心可见性、积分商城兑换记录加载、评论、点赞、收藏和关注等主流程。旧脚本只检查通知中心DOM存在，修复后脚本升级为检查\texttt{{hidden=false}}、\texttt{{display != none}}以及\texttt{{aria-expanded=true}}，能够直接捕获之前的高严重缺陷。

\lstinputlisting[language=Java,caption={{ForumBlackBoxTest.java核心自动化脚本}}]{{../../selenium-junit/src/test/java/com/swjtu/forum/ForumBlackBoxTest.java}}

\section{{测试结果统计}}
本轮共设计用例{summary['designed_cases']}条，覆盖15个功能点，每个功能点10条。已执行并有证据的用例{summary['executed_cases']}条，通过{summary['passed_cases']}条，失败/发现缺陷{summary['failed_cases']}条，未执行设计用例{summary['unexecuted_cases']}条。未执行项主要是低优先级兼容性、极端边界和异常服务路径，它们已纳入后续回归清单。

严重问题修复后重新启动便携包，后端\texttt{{/api/sections}}返回200，前端首页返回200；\texttt{{/growth/rewards}}返回200，\texttt{{/growth/redemptions}}返回200；通知中心点击后面板状态为\texttt{{hidden=false}}且计算样式\texttt{{display=flex}}。这些结果记录在\texttt{{verification-summary.json}}中，并配套保存桌面端和移动端截图。

\section{{截图证据}}
{chr(10).join(fig_blocks)}

\section{{缺陷清单}}
\begin{{longtable}}{{P{{1.5cm}}P{{2.3cm}}P{{1.2cm}}P{{6.2cm}}P{{1.8cm}}P{{5.2cm}}}}
\toprule
编号 & 模块 & 严重 & 标题 & 状态 & 证据\\
\midrule
\endfirsthead
\toprule
编号 & 模块 & 严重 & 标题 & 状态 & 证据\\
\midrule
\endhead
{bug_rows}
\bottomrule
\end{{longtable}}

\section{{修复说明与回归验证}}
本轮优先修复两个会直接阻断用户使用的高严重问题。通知中心问题的根因是面板DOM虽然创建，但关闭/打开逻辑同时受内联样式和hidden属性影响，点击按钮后面板仍不可见。修复后统一使用hidden属性控制可见性，并让CSS中\texttt{{.notif-panel}}保持\texttt{{display:flex}}布局。回归截图显示桌面端和移动端均能展开通知中心。

积分商城问题的根因是兑换记录接口直接序列化JPA实体，兑换记录中的user/reward关联在部分路径下触发懒加载或循环序列化风险，导致前端刷新“我的兑换”时出现服务端错误。修复后新增\texttt{{RedemptionRequestResponse}} DTO，Controller返回DTO而不是实体；Repository增加关联抓取查询；Service在创建或审核兑换后返回已加载关联的记录。回归验证中\texttt{{/growth/redemptions}}返回200，积分商城页面刷新不再出现加载失败。

启动回归中还发现旧H2数据库升级时\texttt{{comments.accepted}}非空列缺少默认值会导致后端启动失败。修复方式是在实体字段上补充\texttt{{boolean default false}}，并重新打包便携jar。修复后后端可在既有demo数据上完成迁移并启动。

\section{{脚本开发遇到的问题}}
第一，便携包启动脚本在当前PowerShell环境下会受到\texttt{{Path/PATH}}重复环境变量影响，直接使用\texttt{{Start-Process}}可能失败。为保证测试稳定，实际启动采用干净环境变量的独立Java进程，并通过端口监听和HTTP 200健康检查确认服务稳定后再执行测试。

第二，前端页面包含运行时渲染逻辑，不能只等待静态HTML中的占位节点。积分商城旧占位符\texttt{{data-slot=rewards-content}}在运行时会被整个\texttt{{main}}内容替换，因此自动化脚本改为等待\texttt{{app-ready}}类和页面错误文本消失。

第三，截图验证必须同时检查DOM状态和视觉状态。通知中心旧问题正是DOM存在但不可见，所以本轮断言不仅检查元素存在，还检查hidden属性、计算display值和aria-expanded状态。

\section{{体会与总结}}
这次练习说明，黑盒测试不只是写“输入什么、输出什么”的表格。对于论坛类系统，很多严重问题发生在跨功能链路上：注册影响登录态，登录态影响发帖和互动，发帖影响通知和关注，积分影响商城兑换。单点测试只能证明按钮能点，链路测试才能发现刷新、序列化、持久化和权限控制中的缺陷。

等价类方法帮助我避免遗漏主要输入类别；边界值方法帮助我把学号长度、密码长度、积分差值、未读数等临界点单独列出；判定表方法最适合表达“登录/未登录、已关注/未关注、积分足够/不足、资源存在/不存在”这类组合条件。后续如果继续完善，应优先把150条设计用例中尚未执行的P1用例转化为自动化脚本，并补充Edge IE模式或兼容层验证。

\end{{document}}
"""


def main() -> None:
    FINAL.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    write_csv_md(cases)
    write_selenium()
    figures = copy_figures()
    result_count = Counter(c["执行结果"] for c in cases)
    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "designed_cases": len(cases),
        "feature_points": len(FEATURES),
        "cases_per_feature": 10,
        "executed_cases": result_count.get("通过", 0) + result_count.get("失败", 0),
        "passed_cases": result_count.get("通过", 0),
        "failed_cases": result_count.get("失败", 0),
        "unexecuted_cases": result_count.get("未执行", 0),
        "bugs_total": len(BUGS),
        "bugs_fixed": sum(1 for bug in BUGS if bug["status"] == "已修复"),
    }
    (WORK / "测试执行摘要.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (FINAL / "software_test_report.tex").write_text(make_latex(cases, figures, summary), encoding="utf-8")
    (WORK / "report_build_summary.json").write_text(json.dumps({
        **summary,
        "tex": str(FINAL / "software_test_report.tex"),
        "pdf_target": str(REPORT_ROOT / "软件系统综合课程设计——练习1（黑盒+功能测试）.pdf"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
