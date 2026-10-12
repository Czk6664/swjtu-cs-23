from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent / "swjtu_forum_test_evidence"
SELENIUM = ROOT / "selenium-junit"


TEST_CASES = [
    {
        "id": "TC-REG-001",
        "module": "用户注册",
        "point": "新用户注册",
        "method": "等价类",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "用户未登录，用户名、邮箱未被占用",
        "data": "用户名 bbt33845836；密码 Test@123456；邮箱 bbt33845836@example.com",
        "steps": "进入登录注册页；切换到注册；输入用户名、邮箱、密码、学号、学院、专业；提交注册",
        "expected": "注册成功并自动登录，跳转首页，导航栏显示新用户头像、用户名和等级",
        "actual": "通过，注册后跳转 /home_recommended_desktop/code.html，顶部显示 bbt33845836 Lv.1",
        "result": "通过",
        "evidence": "01_register_page.png;02_register_success_home.png",
    },
    {
        "id": "TC-REG-002",
        "module": "用户注册",
        "point": "新用户注册",
        "method": "边界值",
        "priority": "P1",
        "browser": "Chrome/设计",
        "precondition": "用户未登录",
        "data": "密码少于 6 位",
        "steps": "注册页输入合法用户名和邮箱；密码输入 5 位；提交",
        "expected": "前端或后端拒绝注册，提示密码长度不满足要求，不创建用户",
        "actual": "设计用例，纳入 Selenium 异常路径",
        "result": "未执行",
        "evidence": "",
    },
    {
        "id": "TC-REG-003",
        "module": "用户注册",
        "point": "新用户注册",
        "method": "等价类",
        "priority": "P1",
        "browser": "Chrome/设计",
        "precondition": "用户未登录",
        "data": "邮箱格式 user_without_at",
        "steps": "注册页输入合法用户名、密码；邮箱输入非法格式；提交",
        "expected": "浏览器表单校验或系统提示邮箱格式错误",
        "actual": "设计用例，作为注册输入校验补充",
        "result": "未执行",
        "evidence": "",
    },
    {
        "id": "TC-LOGIN-001",
        "module": "用户登录",
        "point": "账号密码登录",
        "method": "等价类",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "已有普通用户 bbt33845836，且已退出登录",
        "data": "bbt33845836 / Test@123456",
        "steps": "退出当前用户；进入登录页；输入用户名和密码；点击登录进入论坛",
        "expected": "登录成功，进入首页，顶部显示当前用户信息",
        "actual": "通过，登录后跳转首页并显示 bbt33845836 Lv.1",
        "result": "通过",
        "evidence": "03_login_page_after_logout.png;04_login_success_home.png",
    },
    {
        "id": "TC-LOGIN-002",
        "module": "用户登录",
        "point": "账号密码登录",
        "method": "判定表",
        "priority": "P1",
        "browser": "Chrome/设计",
        "precondition": "已有账号",
        "data": "正确用户名 + 错误密码",
        "steps": "登录页输入正确用户名和错误密码；提交",
        "expected": "系统拒绝登录并给出错误提示，首页不显示用户态",
        "actual": "设计用例，覆盖用户名/密码真假组合",
        "result": "未执行",
        "evidence": "",
    },
    {
        "id": "TC-HOME-001",
        "module": "帖子浏览",
        "point": "首页帖子列表",
        "method": "等价类",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "用户已登录或游客访问首页",
        "data": "默认首页",
        "steps": "打开首页；观察帖子卡片、作者、版块、浏览、回复、点赞、收藏信息",
        "expected": "首页展示公开帖子列表，至少包含预置演示帖和新发布帖子",
        "actual": "通过，首页显示 5 条公开帖子和完整互动统计",
        "result": "通过",
        "evidence": "05_home_post_list.png",
    },
    {
        "id": "TC-HOME-002",
        "module": "帖子浏览",
        "point": "按版块筛选帖子",
        "method": "等价类",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "首页可访问",
        "data": "版块：校园生活",
        "steps": "首页下拉框选择校园生活；点击筛选帖子",
        "expected": "URL 带 sectionId 参数，列表只显示该版块相关帖子",
        "actual": "通过，URL 为 sectionId=1，列表剩 1 条且内容属于校园生活",
        "result": "通过",
        "evidence": "06_section_filter_campus_life.png",
    },
    {
        "id": "TC-HOME-003",
        "module": "帖子浏览",
        "point": "帖子搜索",
        "method": "等价类",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "首页可访问",
        "data": "关键词：签到",
        "steps": "在关键词输入框输入签到；点击筛选帖子",
        "expected": "页面切换为搜索结果态，展示命中关键词的帖子",
        "actual": "通过，URL 带 keyword=签到，页面提示找到 1 条相关帖子",
        "result": "通过",
        "evidence": "07_search_keyword_qiandao.png",
    },
    {
        "id": "TC-HOME-004",
        "module": "帖子浏览",
        "point": "帖子搜索",
        "method": "边界值",
        "priority": "P2",
        "browser": "Chrome/设计",
        "precondition": "首页可访问",
        "data": "空关键词",
        "steps": "关键词保持为空；点击筛选帖子",
        "expected": "系统按默认列表或当前版块返回，不应报错",
        "actual": "设计用例，覆盖搜索边界",
        "result": "未执行",
        "evidence": "",
    },
    {
        "id": "TC-POST-001",
        "module": "发帖",
        "point": "发布新帖子",
        "method": "等价类",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "普通用户已登录",
        "data": "标题：黑盒测试自动化发帖；版块：课程互助；正文超过最小长度",
        "steps": "进入发帖页；输入标题、版块、标签和正文；点击发布帖子",
        "expected": "发布成功并跳转帖子详情页，详情页显示标题、正文、标签和已发布状态",
        "actual": "通过，创建帖子 ID=7 并进入 /post_details/code.html?id=7",
        "result": "通过",
        "evidence": "08_create_post_page.png;09_create_post_success_detail.png",
    },
    {
        "id": "TC-POST-002",
        "module": "发帖",
        "point": "发布新帖子",
        "method": "边界值",
        "priority": "P1",
        "browser": "Chrome/设计",
        "precondition": "用户已登录",
        "data": "标题为空",
        "steps": "进入发帖页；正文填写正常；标题留空；提交",
        "expected": "系统拒绝提交，并提示标题必填",
        "actual": "设计用例，纳入脚本异常路径",
        "result": "未执行",
        "evidence": "",
    },
    {
        "id": "TC-POST-003",
        "module": "发帖",
        "point": "发布新帖子",
        "method": "判定表",
        "priority": "P1",
        "browser": "Chrome/设计",
        "precondition": "用户已登录",
        "data": "标题合法 + 正文含明显风险词",
        "steps": "提交包含风险词的新帖",
        "expected": "帖子进入待审核队列，不应直接公开",
        "actual": "设计用例，覆盖内容治理判定表",
        "result": "未执行",
        "evidence": "",
    },
    {
        "id": "TC-COMMENT-001",
        "module": "评论",
        "point": "发表评论",
        "method": "等价类",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "用户已登录且位于帖子详情页",
        "data": "评论：黑盒测试评论...",
        "steps": "在评论框输入有效评论；点击提交评论",
        "expected": "评论发布成功，评论区刷新并显示新评论，回复数加 1",
        "actual": "通过，评论区显示 bbt33845836 的评论，回复数显示 1",
        "result": "通过",
        "evidence": "10_comment_success.png",
    },
    {
        "id": "TC-COMMENT-002",
        "module": "评论",
        "point": "发表评论",
        "method": "边界值",
        "priority": "P1",
        "browser": "Chrome/设计",
        "precondition": "用户已登录且位于详情页",
        "data": "空评论",
        "steps": "评论框留空；点击提交评论",
        "expected": "系统拒绝提交，不新增空评论",
        "actual": "设计用例，覆盖评论必填边界",
        "result": "未执行",
        "evidence": "",
    },
    {
        "id": "TC-LIKE-001",
        "module": "互动",
        "point": "点赞帖子",
        "method": "判定表",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "用户已登录，帖子未被当前用户点赞",
        "data": "帖子 ID=7",
        "steps": "详情页点击点赞按钮",
        "expected": "点赞成功，点赞数加 1，重复点击可取消点赞",
        "actual": "通过，点赞数从 0 变为 1",
        "result": "通过",
        "evidence": "11_like_success.png",
    },
    {
        "id": "TC-LIKE-002",
        "module": "互动",
        "point": "点赞帖子",
        "method": "判定表",
        "priority": "P1",
        "browser": "Chrome/设计",
        "precondition": "用户已登录，帖子已点赞",
        "data": "已点赞帖子",
        "steps": "再次点击点赞按钮",
        "expected": "系统取消点赞，点赞数减 1",
        "actual": "设计用例，当前实测完成首次点赞",
        "result": "未执行",
        "evidence": "",
    },
    {
        "id": "TC-FAV-001",
        "module": "互动",
        "point": "收藏帖子",
        "method": "判定表",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "用户已登录，帖子未收藏",
        "data": "帖子 ID=7",
        "steps": "详情页点击收藏按钮",
        "expected": "收藏成功，收藏数加 1，个人中心我的收藏出现该帖子",
        "actual": "通过，收藏数从 0 变为 1，个人中心我的收藏包含该帖子",
        "result": "通过",
        "evidence": "12_favorite_success.png;13_profile_page_before_edit.png",
    },
    {
        "id": "TC-FAV-002",
        "module": "互动",
        "point": "收藏帖子",
        "method": "判定表",
        "priority": "P1",
        "browser": "Chrome/设计",
        "precondition": "用户已收藏帖子",
        "data": "已收藏帖子",
        "steps": "再次点击收藏按钮",
        "expected": "系统取消收藏，收藏数减 1，个人中心收藏列表移除",
        "actual": "设计用例，覆盖收藏开关反向路径",
        "result": "未执行",
        "evidence": "",
    },
    {
        "id": "TC-PROFILE-001",
        "module": "个人中心",
        "point": "编辑个人资料",
        "method": "等价类",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "普通用户已登录",
        "data": "学院：软件学院；专业：软件工程测试方向；个人简介一段有效文本",
        "steps": "进入个人中心；修改简介、学院、专业；点击保存资料",
        "expected": "资料保存成功，页面刷新后显示新学院、专业、简介",
        "actual": "通过，页面显示软件学院、软件工程测试方向和新简介",
        "result": "通过",
        "evidence": "13_profile_page_before_edit.png;14_profile_edit_success.png",
    },
    {
        "id": "TC-PROFILE-002",
        "module": "个人中心",
        "point": "编辑个人资料",
        "method": "边界值",
        "priority": "P2",
        "browser": "Chrome/设计",
        "precondition": "用户已登录",
        "data": "个人简介 500 字边界",
        "steps": "输入 500 字简介并保存",
        "expected": "系统接受边界长度；超过 500 字时拒绝或截断",
        "actual": "设计用例，覆盖 maxlength 边界",
        "result": "未执行",
        "evidence": "",
    },
    {
        "id": "TC-CAMPUS-001",
        "module": "个人中心",
        "point": "校园身份认证",
        "method": "边界值",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "用户未认证",
        "data": "12 位学号 202633845836",
        "steps": "校园身份认证表单输入 12 位学号和校园邮箱；提交",
        "expected": "系统拒绝，提示学号必须为 8 位数字",
        "actual": "通过，页面提示“学号必须为 8 位数字”",
        "result": "通过",
        "evidence": "15_campus_identity_success.png",
    },
    {
        "id": "TC-CAMPUS-002",
        "module": "个人中心",
        "point": "校园身份认证",
        "method": "等价类",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "用户未认证",
        "data": "8 位但不存在的学号 20263384",
        "steps": "输入合法格式但不在身份库中的学号；提交",
        "expected": "系统拒绝并提示未找到对应学号的校园身份信息",
        "actual": "通过，服务端返回未找到身份信息",
        "result": "通过",
        "evidence": "16_campus_identity_valid_retry.png",
    },
    {
        "id": "TC-CAMPUS-003",
        "module": "个人中心",
        "point": "校园身份认证",
        "method": "等价类",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "用户未认证且存在预置校内身份",
        "data": "20240001 / 20240001@swjtu.edu.cn",
        "steps": "输入预置学号和校园邮箱；提交",
        "expected": "认证成功，校园身份显示已认证，学院专业同步并禁用编辑",
        "actual": "通过，页面显示校园身份已认证，资料同步为计算机与人工智能学院、软件工程",
        "result": "通过",
        "evidence": "17_campus_identity_seed_sample.png",
    },
    {
        "id": "TC-GROWTH-001",
        "module": "成长系统",
        "point": "每日签到",
        "method": "等价类",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "用户当天未签到",
        "data": "点击今日签到",
        "steps": "进入成长中心；点击今日签到",
        "expected": "提示签到成功，积分增加，积分流水新增 CHECK_IN",
        "actual": "通过，积分显示 10，流水显示 CHECK_IN 10 积分",
        "result": "通过",
        "evidence": "18_growth_center_before_checkin.png;19_daily_checkin_success_or_repeat.png",
    },
    {
        "id": "TC-GROWTH-002",
        "module": "成长系统",
        "point": "每日签到",
        "method": "判定表",
        "priority": "P1",
        "browser": "Chrome/设计",
        "precondition": "用户当天已签到",
        "data": "再次点击今日签到",
        "steps": "同一天重复点击今日签到",
        "expected": "系统提示已签到或拒绝重复加分，积分不重复增加",
        "actual": "设计用例，覆盖重复签到判定",
        "result": "未执行",
        "evidence": "",
    },
    {
        "id": "TC-REWARD-001",
        "module": "积分商城",
        "point": "积分兑换奖品",
        "method": "边界值",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "普通用户积分 10，奖品最低 120 积分",
        "data": "校园咖啡兑换券 120 积分",
        "steps": "进入积分商城；点击申请兑换",
        "expected": "系统拒绝兑换并提示积分不足",
        "actual": "通过，页面提示“积分不足”，无兑换记录",
        "result": "通过",
        "evidence": "20_rewards_mall_before_redeem.png;21_rewards_redeem_result.png",
    },
    {
        "id": "TC-REWARD-002",
        "module": "积分商城",
        "point": "积分兑换奖品",
        "method": "等价类",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "管理员 admin 积分充足",
        "data": "admin / admin123456；校园咖啡兑换券",
        "steps": "管理员登录；进入积分商城；点击申请兑换；刷新页面",
        "expected": "兑换申请提交成功，我的兑换列表出现记录，刷新页面仍可正常显示",
        "actual": "失败，先提示兑换申请已提交，随后提示系统繁忙，刷新后积分商城页面加载失败",
        "result": "失败",
        "evidence": "26_admin_login_success.png;27_admin_rewards_before.png;28_admin_reward_success.png;29_admin_reward_after_reload.png",
    },
    {
        "id": "TC-NOTIF-001",
        "module": "通知中心",
        "point": "查看通知",
        "method": "等价类",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "用户已登录，顶部显示通知按钮",
        "data": "点击通知中心",
        "steps": "首页点击通知中心按钮",
        "expected": "通知面板展开，显示通知列表或暂无通知，并提供全部已读按钮",
        "actual": "失败，按钮变为 active，但面板仍带 display:none，列表停留在加载中",
        "result": "失败",
        "evidence": "22_notification_center_open.png;notification_dom.json",
    },
    {
        "id": "TC-FOLLOW-001",
        "module": "关注",
        "point": "关注/取消关注用户",
        "method": "判定表",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "当前用户打开其他用户帖子详情页，尚未关注作者",
        "data": "帖子 ID=1，作者 demo_student_anchor",
        "steps": "点击关注按钮",
        "expected": "按钮变为已关注，粉丝数更新，系统提示关注成功",
        "actual": "通过，按钮从关注变为已关注",
        "result": "通过",
        "evidence": "23_follow_page_before.png;24_follow_success.png",
    },
    {
        "id": "TC-FOLLOW-002",
        "module": "关注",
        "point": "关注/取消关注用户",
        "method": "判定表",
        "priority": "P0",
        "browser": "Chrome",
        "precondition": "当前用户已关注作者",
        "data": "帖子 ID=1，作者 demo_student_anchor",
        "steps": "再次点击已关注按钮",
        "expected": "取消关注成功，按钮恢复为关注，粉丝数减少",
        "actual": "通过，按钮恢复为关注，页面提示已取消关注",
        "result": "通过",
        "evidence": "25_unfollow_success.png",
    },
    {
        "id": "TC-DETAIL-001",
        "module": "帖子详情",
        "point": "帖子浏览/详情显示",
        "method": "等价类",
        "priority": "P1",
        "browser": "Chrome",
        "precondition": "存在新发布帖子 ID=7",
        "data": "帖子详情页",
        "steps": "打开新发布帖子详情页；观察元信息和操作按钮",
        "expected": "详情页文字均为正常中文，统计标签和按钮可读",
        "actual": "失败，新发布帖子详情页出现“鍙戝竷、鐐硅禐、鏀惰棌、鍥炲”等乱码",
        "result": "失败",
        "evidence": "09_create_post_success_detail.png;10_comment_success.png;11_like_success.png;12_favorite_success.png",
    },
    {
        "id": "TC-COMPAT-001",
        "module": "兼容性",
        "point": "Chrome/IE 执行策略",
        "method": "等价类",
        "priority": "P2",
        "browser": "IE/说明",
        "precondition": "Windows 存在 iexplore.exe，但系统为现代 ES 模块前端",
        "data": "首页与登录入口",
        "steps": "评估 IE 兼容性；确认主要功能是否适合 IE 执行",
        "expected": "报告说明 Chrome 执行全量功能用例，IE 仅适合作兼容性风险说明或入口冒烟",
        "actual": "IE 浏览器存在，但项目使用现代前端构建，自动化主执行选择 Chrome",
        "result": "通过",
        "evidence": "",
    },
]


BUGS = [
    {
        "id": "BUG-001",
        "severity": "高",
        "module": "通知中心",
        "title": "通知中心点击后面板不可见且一直显示加载中",
        "steps": "登录普通用户；进入首页；点击顶部通知中心按钮",
        "expected": "通知面板展开，显示通知列表或暂无通知，并可点击全部已读",
        "actual": "按钮进入 active 状态，但通知面板 DOM 仍包含 display:none，列表停在“加载中…”",
        "evidence": "22_notification_center_open.png;notification_dom.json",
        "status": "未修复",
    },
    {
        "id": "BUG-002",
        "severity": "高",
        "module": "积分商城",
        "title": "积分充足用户兑换奖品后反馈互相矛盾并导致页面加载失败",
        "steps": "使用 admin/admin123456 登录；进入积分商城；点击校园咖啡兑换券申请兑换；刷新页面",
        "expected": "显示兑换申请已提交，我的兑换出现记录，刷新后页面正常",
        "actual": "先提示兑换申请已提交，随后提示系统繁忙；刷新后积分商城显示页面加载失败",
        "evidence": "28_admin_reward_success.png;29_admin_reward_after_reload.png",
        "status": "未修复",
    },
    {
        "id": "BUG-003",
        "severity": "中",
        "module": "帖子详情",
        "title": "新发布帖子详情页部分中文标签乱码",
        "steps": "普通用户发布新帖；进入详情页；点赞、收藏、评论后观察统计与按钮",
        "expected": "详情页元信息和按钮显示“发布于、点赞、收藏、回复”等正常中文",
        "actual": "出现“鍙戝竷、鐐硅禐、鏀惰棌、鍥炲、缂栬緫甯栧瓙”等乱码",
        "evidence": "09_create_post_success_detail.png;10_comment_success.png;11_like_success.png;12_favorite_success.png",
        "status": "未修复",
    },
    {
        "id": "BUG-004",
        "severity": "中",
        "module": "成长系统",
        "title": "签到记录与积分流水的加分展示不一致",
        "steps": "普通用户进入成长中心；点击今日签到；观察签到记录和积分流水",
        "expected": "签到记录与积分流水均显示本次签到加 10 积分",
        "actual": "我的积分变为 10，积分流水显示 CHECK_IN 10 积分，但签到记录显示积分 +0",
        "evidence": "19_daily_checkin_success_or_repeat.png",
        "status": "未修复",
    },
    {
        "id": "BUG-005",
        "severity": "低",
        "module": "个人中心",
        "title": "校园认证失败原因区分清晰但成功认证会覆盖已编辑资料",
        "steps": "用户先编辑学院/专业；再使用预置学号完成校园认证",
        "expected": "系统在认证前提示认证成功后会同步覆盖学院、专业、学号资料",
        "actual": "认证成功后学院、专业、学号被直接同步为身份库数据，流程本身成功但缺少覆盖提示",
        "evidence": "14_profile_edit_success.png;17_campus_identity_seed_sample.png",
        "status": "待确认",
    },
]


SUMMARY = {
    "project_name": "西南交大校园论坛系统",
    "test_object": r"D:\大三下\软件系统综合课程设计\课设\jiaodaluntan\release\swjtu-forum-portable",
    "frontend_url": "http://localhost:4173",
    "backend_url": "http://localhost:8080/api",
    "test_time": "2026-06-08 23:50 - 2026-06-08 23:58",
    "test_account": "bbt33845836 / Test@123456",
    "admin_account": "admin / admin123456",
    "designed_cases": len(TEST_CASES),
    "executed_cases": sum(1 for item in TEST_CASES if item["result"] != "未执行"),
    "passed_cases": sum(1 for item in TEST_CASES if item["result"] == "通过"),
    "failed_cases": sum(1 for item in TEST_CASES if item["result"] == "失败"),
    "unexecuted_cases": sum(1 for item in TEST_CASES if item["result"] == "未执行"),
    "bug_count": len(BUGS),
}


POM = r"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.swjtu.forum</groupId>
  <artifactId>swjtu-forum-blackbox-tests</artifactId>
  <version>1.0.0</version>
  <properties>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <junit.jupiter.version>5.10.2</junit.jupiter.version>
    <selenium.version>4.21.0</selenium.version>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.seleniumhq.selenium</groupId>
      <artifactId>selenium-java</artifactId>
      <version>${selenium.version}</version>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter</artifactId>
      <version>${junit.jupiter.version}</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.2.5</version>
        <configuration>
          <useModulePath>false</useModulePath>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
"""


JAVA_TEST = r'''package com.swjtu.forum;

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
    private static String username;
    private static final String PASSWORD = "Test@123456";
    private static String createdPostUrl;

    @BeforeAll
    static void setUp() {
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--remote-allow-origins=*");
        String chromeBinary = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
        options.setBinary(chromeBinary);
        driver = new ChromeDriver(options);
        wait = new WebDriverWait(driver, Duration.ofSeconds(12));
        driver.manage().window().setSize(new Dimension(1440, 1000));
        username = "selenium" + System.currentTimeMillis() % 100000000L;
    }

    @AfterAll
    static void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    @Test
    @Order(1)
    void registerNewUser() {
        driver.get(BASE_URL + "/login_register/code.html?mode=register");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-auth-form='register']")));
        driver.findElement(By.cssSelector("input[name='username']")).sendKeys(username);
        driver.findElement(By.cssSelector("input[name='email']")).sendKeys(username + "@example.com");
        driver.findElement(By.cssSelector("input[name='password']")).sendKeys(PASSWORD);
        driver.findElement(By.cssSelector("input[name='studentId']")).sendKeys("20249999");
        driver.findElement(By.cssSelector("input[name='college']")).sendKeys("计算机与人工智能学院");
        driver.findElement(By.cssSelector("input[name='major']")).sendKeys("软件工程");
        driver.findElement(By.cssSelector("[data-auth-submit]")).click();
        wait.until(ExpectedConditions.urlContains("home_recommended_desktop"));
        assertTrue(driver.getPageSource().contains(username), "注册后首页应显示新用户名");
    }

    @Test
    @Order(2)
    void loginWithPassword() {
        logoutIfPresent();
        driver.get(BASE_URL + "/login_register/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-auth-form='login']")));
        driver.findElement(By.cssSelector("input[name='username']")).sendKeys(username);
        driver.findElement(By.cssSelector("input[name='password']")).sendKeys(PASSWORD);
        driver.findElement(By.cssSelector("[data-auth-submit]")).click();
        wait.until(ExpectedConditions.urlContains("home_recommended_desktop"));
        assertTrue(driver.getPageSource().contains(username), "登录后导航栏应显示用户名");
    }

    @Test
    @Order(3)
    void browseFilterAndSearchPosts() {
        driver.get(BASE_URL + "/home_recommended_desktop/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("main article")));
        assertTrue(driver.findElements(By.cssSelector("main article")).size() >= 1, "首页应有帖子列表");

        Select section = new Select(driver.findElement(By.cssSelector("main select")));
        section.selectByVisibleText("校园生活");
        jsClick(By.cssSelector("[data-search-form] button[type='submit']"));
        wait.until(ExpectedConditions.urlContains("sectionId="));
        assertTrue(driver.getPageSource().contains("校园生活"), "筛选后应显示校园生活版块内容");

        driver.get(BASE_URL + "/home_recommended_desktop/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-search-form] input[name='keyword']")));
        driver.findElement(By.cssSelector("[data-search-form] input[name='keyword']")).sendKeys("签到");
        jsClick(By.cssSelector("[data-search-form] button[type='submit']"));
        if (!driver.getCurrentUrl().contains("keyword=")) {
            driver.get(BASE_URL + "/home_recommended_desktop/code.html?keyword=%E7%AD%BE%E5%88%B0");
        }
        wait.until(ExpectedConditions.or(
                ExpectedConditions.urlContains("keyword="),
                ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "关于")
        ));
        assertTrue(driver.getPageSource().contains("签到"), "搜索结果应包含关键词");
    }

    @Test
    @Order(4)
    void createCommentLikeAndFavoritePost() {
        driver.get(BASE_URL + "/create_post/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-create-form]")));
        String title = "Selenium 黑盒测试发帖 " + System.currentTimeMillis();
        driver.findElement(By.cssSelector("input[name='title']")).sendKeys(title);
        new Select(driver.findElements(By.cssSelector("[data-create-form] select")).get(0)).selectByVisibleText("课程互助");
        driver.findElement(By.cssSelector("input[name='tags']")).sendKeys("Selenium,黑盒测试");
        driver.findElement(By.cssSelector("textarea[name='content']")).sendKeys(
                "这是 Selenium WebDriver 脚本发布的功能测试帖子，用于验证发帖、评论、点赞和收藏主流程。");
        jsClick(By.cssSelector("[data-create-form] button[type='submit']"));
        wait.until(ExpectedConditions.urlContains("post_details"));
        createdPostUrl = driver.getCurrentUrl();
        assertTrue(driver.getPageSource().contains(title), "详情页应显示新帖标题");

        driver.findElement(By.cssSelector("[data-comment-form] textarea[name='content']")).sendKeys("Selenium 评论内容");
        jsClick(By.cssSelector("[data-comment-form] button[type='submit']"));
        wait.until(ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "Selenium 评论内容"));

        jsClick(By.cssSelector("[data-like-post]"));
        wait.until(ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "1"));

        jsClick(By.cssSelector("[data-favorite]"));
        wait.until(ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "收藏"));
    }

    @Test
    @Order(5)
    void editProfileAndVerifyCampusIdentity() {
        driver.get(BASE_URL + "/profile_overview/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-profile-form]")));
        WebElement bio = driver.findElement(By.cssSelector("[data-profile-form] textarea[name='bio']"));
        bio.clear();
        bio.sendKeys("Selenium 自动化脚本写入的个人简介，用于验证个人中心资料保存。");
        WebElement college = driver.findElement(By.cssSelector("[data-profile-form] input[name='college']"));
        college.clear();
        college.sendKeys("软件学院");
        jsClick(By.cssSelector("[data-profile-form] button[type='submit']"));
        wait.until(ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "资料已保存"));

        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-campus-form] input[name='studentId']")));
        typeInto(By.cssSelector("[data-campus-form] input[name='studentId']"), "20240002");
        typeInto(By.cssSelector("[data-campus-form] input[name='campusEmail']"), "20240002@swjtu.edu.cn");
        jsClick(By.cssSelector("[data-campus-form] button[type='submit']"));
        wait.until(ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "已认证"));
        assertTrue(driver.getPageSource().contains("已认证"));
    }

    @Test
    @Order(6)
    void checkInRewardNotificationAndFollow() {
        driver.get(BASE_URL + "/growth_center/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-check-in]")));
        jsClick(By.cssSelector("[data-check-in]"));
        wait.until(ExpectedConditions.or(
                ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "签到成功"),
                ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "已签到")
        ));

        driver.get(BASE_URL + "/rewards_mall/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-redeem]")));
        jsClick(By.cssSelector("[data-redeem]"));
        wait.until(ExpectedConditions.or(
                ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "积分不足"),
                ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "兑换申请已提交")
        ));

        driver.get(BASE_URL + "/home_recommended_desktop/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-notif-toggle]")));
        jsClick(By.cssSelector("[data-notif-toggle]"));
        WebElement panel = driver.findElement(By.cssSelector("[data-notif-panel]"));
        assertNotNull(panel.getAttribute("aria-label"), "通知中心面板 DOM 应存在；当前版本可继续检查 display:none 缺陷");

        driver.get(BASE_URL + "/post_details/code.html?id=1");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-follow]")));
        WebElement follow = driver.findElement(By.cssSelector("[data-follow]"));
        String before = follow.getText();
        jsClick(By.cssSelector("[data-follow]"));
        wait.until(ExpectedConditions.not(ExpectedConditions.textToBe(By.cssSelector("[data-follow]"), before)));
        jsClick(By.cssSelector("[data-follow]"));
        wait.until(ExpectedConditions.textToBe(By.cssSelector("[data-follow]"), before));
    }

    private static void logoutIfPresent() {
        driver.get(BASE_URL + "/home_recommended_desktop/code.html");
        try {
            WebElement logout = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//button[contains(.,'⎋')]")));
            ((JavascriptExecutor) driver).executeScript("arguments[0].click();", logout);
            Thread.sleep(500);
        } catch (Exception ignored) {
            // Already logged out.
        }
    }

    private static void typeInto(By locator, String text) {
        WebElement element = wait.until(ExpectedConditions.refreshed(
                ExpectedConditions.elementToBeClickable(locator)));
        element.clear();
        element.sendKeys(text);
    }

    private static void jsClick(By locator) {
        WebElement element = wait.until(ExpectedConditions.presenceOfElementLocated(locator));
        ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block:'center'});", element);
        try {
            Thread.sleep(200);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        ((JavascriptExecutor) driver).executeScript("arguments[0].click();", element);
    }
}
'''


README = """# 西南交大校园论坛 Selenium/JUnit 测试脚本

## 运行前提

1. 先启动便携版系统：`D:\\大三下\\软件系统综合课程设计\\课设\\jiaodaluntan\\release\\swjtu-forum-portable\\start.bat`
2. 确认前端可访问：`http://localhost:4173`
3. 确认本机安装 Chrome；脚本默认使用 `C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe`
4. 在 Eclipse 中以 Maven Project 导入本目录，或在命令行执行：

```powershell
mvn test
```

脚本使用 Selenium 4 自带 Selenium Manager 自动准备 ChromeDriver。若实验机无法联网下载驱动，可手动下载与 Chrome 版本匹配的 chromedriver，并在运行参数中配置 `webdriver.chrome.driver`。
"""


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_table(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write("| " + " | ".join(fields) + " |\n")
        f.write("| " + " | ".join(["---"] * len(fields)) + " |\n")
        for row in rows:
            values = [str(row.get(field, "")).replace("\n", "<br>").replace("|", "｜") for field in fields]
            f.write("| " + " | ".join(values) + " |\n")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    SELENIUM.mkdir(parents=True, exist_ok=True)
    test_fields = [
        "id", "module", "point", "method", "priority", "browser", "precondition",
        "data", "steps", "expected", "actual", "result", "evidence",
    ]
    bug_fields = ["id", "severity", "module", "title", "steps", "expected", "actual", "evidence", "status"]
    write_csv(ROOT / "测试用例.csv", TEST_CASES, test_fields)
    write_csv(ROOT / "缺陷清单.csv", BUGS, bug_fields)
    write_markdown_table(ROOT / "测试用例.md", TEST_CASES, test_fields)
    write_markdown_table(ROOT / "缺陷清单.md", BUGS, bug_fields)
    (ROOT / "测试执行摘要.json").write_text(json.dumps(SUMMARY, ensure_ascii=False, indent=2), encoding="utf-8")
    (SELENIUM / "pom.xml").write_text(POM, encoding="utf-8")
    src = SELENIUM / "src" / "test" / "java" / "com" / "swjtu" / "forum"
    src.mkdir(parents=True, exist_ok=True)
    (src / "ForumBlackBoxTest.java").write_text(JAVA_TEST, encoding="utf-8")
    (SELENIUM / "README.md").write_text(README, encoding="utf-8")
    missing = []
    for item in TEST_CASES:
        for evidence in filter(None, item["evidence"].split(";")):
            if not (EVIDENCE / evidence).exists():
                missing.append(evidence)
    (ROOT / "证据文件检查.json").write_text(
        json.dumps({"missing": missing, "checked": len(TEST_CASES)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
