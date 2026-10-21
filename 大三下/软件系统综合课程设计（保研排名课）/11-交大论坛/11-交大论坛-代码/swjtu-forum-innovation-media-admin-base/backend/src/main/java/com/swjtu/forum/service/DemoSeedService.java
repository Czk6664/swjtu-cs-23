package com.swjtu.forum.service;

import com.swjtu.forum.entity.Badge;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.PostBrowseHistory;
import com.swjtu.forum.entity.PostFavorite;
import com.swjtu.forum.entity.PointsHistory;
import com.swjtu.forum.entity.RedemptionRequest;
import com.swjtu.forum.entity.RewardItem;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.entity.Tag;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.entity.UserBadge;
import com.swjtu.forum.repository.BadgeRepository;
import com.swjtu.forum.repository.CommentRepository;
import com.swjtu.forum.repository.DailyCheckInRepository;
import com.swjtu.forum.repository.OperationLogRepository;
import com.swjtu.forum.repository.PointsHistoryRepository;
import com.swjtu.forum.repository.PostBrowseHistoryRepository;
import com.swjtu.forum.repository.PostFavoriteRepository;
import com.swjtu.forum.repository.PostLikeRepository;
import com.swjtu.forum.repository.PostRepository;
import com.swjtu.forum.repository.RedemptionRequestRepository;
import com.swjtu.forum.repository.RewardItemRepository;
import com.swjtu.forum.repository.SectionRepository;
import com.swjtu.forum.repository.TagRepository;
import com.swjtu.forum.repository.UserBadgeRepository;
import com.swjtu.forum.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Optional;
import java.util.Set;

@Service
public class DemoSeedService implements DemoSeeder {

    private static final String DEFAULT_PASSWORD = "demo-password";
    private static final Logger log = LoggerFactory.getLogger(DemoSeedService.class);

    private final UserRepository userRepository;
    private final SectionRepository sectionRepository;
    private final TagRepository tagRepository;
    private final PostRepository postRepository;
    private final CommentRepository commentRepository;
    private final PostLikeRepository postLikeRepository;
    private final PostFavoriteRepository postFavoriteRepository;
    private final PostBrowseHistoryRepository postBrowseHistoryRepository;
    private final PointsHistoryRepository pointsHistoryRepository;
    private final RewardItemRepository rewardItemRepository;
    private final RedemptionRequestRepository redemptionRequestRepository;
    private final OperationLogRepository operationLogRepository;
    private final DailyCheckInRepository dailyCheckInRepository;
    private final BadgeRepository badgeRepository;
    private final UserBadgeRepository userBadgeRepository;
    private final BadgeService badgeService;
    private final PasswordEncoder passwordEncoder;

    public DemoSeedService(UserRepository userRepository,
                           SectionRepository sectionRepository,
                           TagRepository tagRepository,
                           PostRepository postRepository,
                           CommentRepository commentRepository,
                           PostLikeRepository postLikeRepository,
                           PostFavoriteRepository postFavoriteRepository,
                           PostBrowseHistoryRepository postBrowseHistoryRepository,
                           PointsHistoryRepository pointsHistoryRepository,
                           RewardItemRepository rewardItemRepository,
                           RedemptionRequestRepository redemptionRequestRepository,
                           OperationLogRepository operationLogRepository,
                           DailyCheckInRepository dailyCheckInRepository,
                           BadgeRepository badgeRepository,
                           UserBadgeRepository userBadgeRepository,
                           BadgeService badgeService,
                           PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.sectionRepository = sectionRepository;
        this.tagRepository = tagRepository;
        this.postRepository = postRepository;
        this.commentRepository = commentRepository;
        this.postLikeRepository = postLikeRepository;
        this.postFavoriteRepository = postFavoriteRepository;
        this.postBrowseHistoryRepository = postBrowseHistoryRepository;
        this.pointsHistoryRepository = pointsHistoryRepository;
        this.rewardItemRepository = rewardItemRepository;
        this.redemptionRequestRepository = redemptionRequestRepository;
        this.operationLogRepository = operationLogRepository;
        this.dailyCheckInRepository = dailyCheckInRepository;
        this.badgeRepository = badgeRepository;
        this.userBadgeRepository = userBadgeRepository;
        this.badgeService = badgeService;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    @Override
    public void seed() {
        seedCoreDemoData();
        seedScenarioData();
        log.info("Demo seed finished using guarded profile/property entrypoint");
    }

    @Transactional
    public void seedCoreDemoData() {
        ensureUser("demo_guest_anchor", "demo_guest@swjtu.edu.cn", "USER", "游客演示账号", 1, 0, 0);
        User student = ensureUser("demo_student_anchor", "demo_student@swjtu.edu.cn", "USER", "活跃学生演示账号", 3, 180, 260);
        User admin = ensureUser("demo_admin_anchor", "demo_admin@swjtu.edu.cn", "ADMIN", "管理台演示账号", 5, 320, 500);

        Section section = ensureSection("校园生活", "校园动态与社团交流", 2, admin);

        Set<Tag> tags = new LinkedHashSet<>();
        tags.add(ensureTag("社团活动", "demo"));
        tags.add(ensureTag("校园攻略", "demo"));

        ensurePost(
                "【演示】校园热帖：春季社团市集逛展指南",
                student,
                section,
                "为了让首页和详情页有稳定内容，这里预置一篇可重复生成的演示热帖。",
                tags,
                120,
                18,
                6,
                10,
                220
        );

        ensureReward("【演示】校园咖啡兑换券", "用于演示积分商城兑换流程", 120, 20);
        touchReadRepositories();
    }

    @Transactional
    public void seedScenarioData() {
        User student = ensureUser("demo_student_anchor", "demo_student@swjtu.edu.cn", "USER", "活跃学生演示账号", 3, 180, 260);
        User admin = ensureUser("demo_admin_anchor", "demo_admin@swjtu.edu.cn", "ADMIN", "管理台演示账号", 5, 320, 500);
        User moderator = ensureUser("demo_moderator_anchor", "demo_moderator@swjtu.edu.cn", "MODERATOR", "版主演示账号", 4, 220, 300);
        User bannedUser = ensureUser("demo_banned_anchor", "demo_banned@swjtu.edu.cn", "USER", "被封禁案例账号", 2, 90, 40);
        if (Boolean.TRUE.equals(bannedUser.getEnabled())) {
            bannedUser.setEnabled(false);
            userRepository.save(bannedUser);
        }

        resetScenarioState(student);

        Section campusLife = ensureSection("校园生活", "校园动态与社团交流", 2, moderator);
        Section courseSection = ensureSection("课程讨论", "课程经验与学习讨论", 3, moderator);
        Section newsSection = ensureSection("校园资讯", "通知公告与讲座信息", 4, admin);

        Set<Tag> growthTags = new LinkedHashSet<>();
        growthTags.add(ensureTag("成长打卡", "demo"));
        growthTags.add(ensureTag("积分攻略", "demo"));

        Set<Tag> reviewTags = new LinkedHashSet<>();
        reviewTags.add(ensureTag("宿舍生活", "demo"));
        reviewTags.add(ensureTag("交易提醒", "demo"));

        Set<Tag> opsTags = new LinkedHashSet<>();
        opsTags.add(ensureTag("内容治理", "demo"));
        opsTags.add(ensureTag("管理复盘", "demo"));

        Post hotPost = postRepository.findByTitle("【演示】校园热帖：春季社团市集逛展指南")
                .orElseGet(() -> ensurePost("【演示】校园热帖：春季社团市集逛展指南", student, campusLife,
                        "为了让首页和详情页有稳定内容，这里预置一篇可重复生成的演示热帖。", growthTags, 120, 18, 6, 10, 220));

        Post growthPost = ensurePost("【演示】成长中心：四月签到打卡交流帖", student, courseSection,
                "这里集中展示签到、积分和成长任务的讲述型内容，方便个人中心与成长中心联动演示。",
                growthTags, 68, 9, 3, 4, 130);
        Post pendingPost = ensurePost("【演示】待审核：宿舍二手交易注意事项合集", student, campusLife,
                "这是一篇保留待审核状态的帖子，用于后台待审列表演示。",
                reviewTags, 12, 0, 0, 0, 18, PostService.STATUS_PENDING);
        Post opsPost = ensurePost("【演示】后台复盘：本周内容治理值班记录", admin, newsSection,
                "记录管理员与版主的治理动作，保证管理页有已处理案例与运营内容。",
                opsTags, 25, 2, 1, 1, 40);

        RewardItem coffee = ensureReward("【演示】校园咖啡兑换券", "用于演示积分商城兑换流程", 120, 20);
        RewardItem library = ensureReward("【演示】图书馆自习室优先券", "用于演示第二个商城奖励与审核记录", 180, 8);

        ensureComment(hotPost, student, "这条演示评论用于详情页首屏展示，也会出现在管理与互动统计里。");
        ensureFavorite(student, hotPost);
        ensureBrowseHistory(student, hotPost);
        ensurePointsHistory(student, "CHECK_IN", 10, 5, 270, 185, "演示签到：四月打卡第 1 天");
        ensureRedemption(student, library, 0, library.getCostPoints(), "演示申请待管理员审核");

        Long opsTargetId = pendingPost.getId() == null ? -1L : pendingPost.getId();
        ensureOperationLog(admin, "REVIEW_POST", "POST", opsTargetId, "演示环境待审核帖子保留一条处理中记录");
        ensureOperationLog(admin, "BAN_USER", "USER", bannedUser.getId(), "演示封禁案例：发布违规交易广告");
        seedCampusSnapshotData(moderator);
        touchReadRepositories();
    }

    private void seedCampusSnapshotData(User moderator) {
        badgeService.initializeBadgeDefinitions();

        User xipuSeller = ensureUser("xipu_market_senior", "xipu_market_senior@swjtu.edu.cn", "USER",
                "常在二手闲置区整理宿舍好物和交易提醒。", 4, 360, 520);
        User repairHelper = ensureUser("repair_helper_cc", "repair_helper_cc@swjtu.edu.cn", "USER",
                "熟悉电脑外设和校园维修渠道，喜欢把踩坑经验写清楚。", 5, 540, 760);
        User courseFinder = ensureUser("course_table_guide", "course_table_guide@swjtu.edu.cn", "USER",
                "选课、课表和期末资料互助型用户。", 3, 250, 330);
        User foodScout = ensureUser("xipu_food_scout", "xipu_food_scout@swjtu.edu.cn", "USER",
                "记录犀浦食堂窗口、团购券和晚饭选择。", 2, 150, 210);
        User clubWalker = ensureUser("campus_group_walker", "campus_group_walker@swjtu.edu.cn", "USER",
                "关注跨校小组、运动打卡和校园活动。", 6, 680, 880);
        User freshmanAsk = ensureUser("freshman_ask_box", "freshman_ask_box@swjtu.edu.cn", "USER",
                "新生常见问题收集者，擅长把小问题问明白。", 2, 120, 160);
        User keyboardOwner = ensureUser("keyboard_transfer", "keyboard_transfer@swjtu.edu.cn", "USER",
                "偶尔出闲置外设，坚持校内面交和站内私信沟通。", 3, 210, 260);
        User studyPartner = ensureUser("ee_review_partner", "ee_review_partner@swjtu.edu.cn", "USER",
                "电工电子、课程互助和复习资料整理。", 4, 390, 430);
        assignAvatar(xipuSeller, "/uploads/avatars/demo-avatar-xipu-market.png");
        assignAvatar(repairHelper, "/uploads/avatars/demo-avatar-repair-helper.png");
        assignAvatar(courseFinder, "/uploads/avatars/demo-avatar-course-guide.png");
        assignAvatar(foodScout, "/uploads/avatars/demo-avatar-food-scout.png");
        assignAvatar(clubWalker, "/uploads/avatars/demo-avatar-club-walker.png");
        assignAvatar(freshmanAsk, "/uploads/avatars/demo-avatar-freshman-ask.png");
        assignAvatar(keyboardOwner, "/uploads/avatars/demo-avatar-keyboard-transfer.png");
        assignAvatar(studyPartner, "/uploads/avatars/demo-avatar-ee-review.png");

        Section market = ensureSection("二手闲置", "校内二手、转让与交易提醒", 5, moderator);
        Section life = ensureSection("犀浦生活", "校区生活、食堂、图书馆和通勤信息", 4, moderator);
        Section course = ensureSection("课程互助", "课程资料、选课建议、作业与考试经验", 1, moderator);
        Section ask = ensureSection("打听求助", "维修、回收、校园信息与日常求助", 7, moderator);
        Section club = ensureSection("社团招新", "社团活动、运动打卡和跨校小组交流", 8, moderator);

        Set<Tag> marketTags = tagSet("二手闲置", "站内私信", "宿舍好物");
        Set<Tag> repairTags = tagSet("电脑维修", "打听求助", "避坑经验");
        Set<Tag> courseTags = tagSet("课程互助", "课表", "期末复习");
        Set<Tag> foodTags = tagSet("犀浦生活", "食堂", "团购券");
        Set<Tag> clubTags = tagSet("社团活动", "运动打卡", "跨校小组");

        Post heater = ensurePost("出一台宿舍取暖器，九成新，适合租房或冬天自习用",
                xipuSeller, market,
                "之前短期租房买的取暖器，现在用不上了。制热速度快，外观保持得比较好，适合在校外租房、宿舍阳台整理衣物时临时取暖。只接受校内当面确认，感兴趣请站内私信，不在帖子里留联系方式。",
                marketTags, 186, 21, 4, 12, 280);
        Post fan = ensurePost("收一个小风扇，有闲置的同学可以私信我",
                freshmanAsk, market,
                "最近寝室晚上有点闷，想收一个还能正常转的小风扇，桌面款或者夹子款都可以。希望能在犀浦校区附近当面看一下成色，价格按新旧程度商量。",
                marketTags, 98, 9, 3, 5, 145);
        Post bike = ensurePost("附近哪里可以回收自行车？想处理一辆旧车",
                freshmanAsk, ask,
                "自行车放了很久不怎么骑，想问问校区附近有没有比较正规的回收点，或者有没有同学知道校内二手处理流程。主要希望省事、安全，不想随便丢在楼下。",
                repairTags, 142, 13, 5, 6, 190);
        Post repair = ensurePost("求推荐靠谱修电脑的店，充电接口疑似接触不良",
                repairHelper, ask,
                "电脑充电口需要找角度才能充上，官方检测说不一定能当场判断原因。我想先找一家靠谱店做基础检查，不急着换主板。有没有同学修过类似问题，可以分享一下流程和大概注意事项？",
                repairTags, 234, 28, 7, 18, 330);
        Post schedule = ensurePost("下学期课表怎么查不到？教务系统入口是不是换了",
                courseFinder, course,
                "按照以前的方式没有查到下学期课表，后来发现和选课状态、必修课时间安排有关。这里整理一下我试过的入口和查询顺序，也欢迎知道更稳方法的同学补充。",
                courseTags, 318, 35, 8, 24, 420);
        Post eeReview = ensurePost("电子与电工技术基础 A 期末复习资料求分享",
                studyPartner, course,
                "想集中整理一份电子与电工技术基础 A 的期末复习清单，包括重点章节、例题类型和容易混淆的概念。已有部分课堂笔记，可以和同学互补资料，统一放到帖子评论里。",
                courseTags, 276, 31, 9, 27, 390);
        Post studentPrefix = ensurePost("打听一下某届学号前缀对应哪个学院",
                courseFinder, ask,
                "帮同学核对课程名单时遇到一个学号前缀，不确定对应学院。为保护隐私不贴完整学号，只想了解学院编码规则的大致查询方式，知道的同学麻烦指路。",
                courseTags, 88, 6, 2, 4, 110);
        Post keyboard = ensurePost("九里校区出一把二手机械键盘，适合宿舍学习桌",
                keyboardOwner, market,
                "键盘功能正常，轴体手感偏轻，外壳有正常使用痕迹。因为换了新键盘所以转给需要的同学。价格不写死，现场看成色后再商量，默认站内私信沟通。",
                marketTags, 167, 14, 4, 10, 220);
        Post food = ensurePost("今天在食堂吃什么比较稳？求晚饭窗口推荐",
                foodScout, life,
                "最近几天不知道吃什么，想收集一下犀浦校区晚饭比较稳定的窗口。希望推荐能具体一点，比如排队情况、口味偏淡还是偏辣、适合不适合赶课前快速吃完。",
                foodTags, 201, 19, 6, 15, 260);
        Post coupon = ensurePost("出一张甜品团购券，想换给最近会去的同学",
                foodScout, market,
                "之前囤的甜品团购券快到使用期限了，自己这周没空去。想转给刚好要去的同学，券面信息可以站内私信确认，交易尽量在校区内完成。",
                foodTags, 109, 7, 3, 6, 140);
        Post groups = ensurePost("热门跨校小组整理：树洞、恋爱互助、健身和食堂话题",
                clubWalker, club,
                "看到很多同学在问跨校小组入口和适合讨论的话题，我按截图里常见分类整理了几个方向：树洞倾诉、恋爱问题互助、搭子小组、健身俱乐部、食堂推荐。建议大家理性发言，不公开个人隐私。",
                clubTags, 356, 42, 10, 31, 480);
        Post lost = ensurePost("失物招领提醒：捡到物品请优先写清时间地点和特征",
                clubWalker, life,
                "最近看到不少求助帖只有一句话，后续确认起来比较困难。建议发失物招领时写清大致时间、地点、物品特征和认领方式；涉及证件信息时不要公开完整编号。",
                tagSet("失物招领", "犀浦生活", "隐私保护"), 122, 16, 4, 9, 180);

        ensureComment(heater, repairHelper, "这个类型建议先看功率和插座安全，校内面交时可以现场试一下开关和发热速度。");
        ensureComment(heater, foodScout, "冬天租房确实用得上，建议标题里标明是否带遥控和是否有定时功能。");
        ensureComment(fan, xipuSeller, "我之前收过桌面小风扇，记得看噪音和电源线接口，晚上用会舒服很多。");
        ensureComment(bike, clubWalker, "可以先问楼栋宿管有没有统一清理安排，不建议直接放公共区域。");
        ensureComment(repair, keyboardOwner, "如果只是接口松动，先别急着换大件，找店检测时让对方把检测项写清楚。");
        ensureComment(schedule, freshmanAsk, "原来还和选课状态有关，感谢整理，我之前一直以为是入口打不开。");
        ensureComment(schedule, studyPartner, "补充一下：必修课时间一般可以提前看到，但选修课要等选课结果稳定。");
        ensureComment(eeReview, courseFinder, "我可以补一份实验部分的易错点，整理好后放评论区。");
        ensureComment(keyboard, repairHelper, "外设交易建议现场试每个键位，尤其是空格、回车和方向键。");
        ensureComment(food, freshmanAsk, "赶课前推荐选排队短的窗口，别在高峰期尝试新菜。");
        ensureComment(groups, moderator, "这个帖子方向不错，提醒大家不要在公开评论里发个人账号和隐私信息。");
        ensureComment(lost, moderator, "涉及学生证、身份证等敏感信息时，只描述部分特征即可。");

        ensureFavorite(repairHelper, schedule);
        ensureFavorite(courseFinder, eeReview);
        ensureFavorite(foodScout, food);
        ensureFavorite(clubWalker, groups);
        ensureBrowseHistory(xipuSeller, repair);
        ensureBrowseHistory(freshmanAsk, schedule);
        ensureBrowseHistory(studyPartner, eeReview);
        ensureBrowseHistory(keyboardOwner, keyboard);

        assignBadges(xipuSeller, "secondhand_expert", "civil_user");
        assignBadges(repairHelper, "helpful_star", "active_commenter", "civil_user");
        assignBadges(courseFinder, "course_master", "helpful_star");
        assignBadges(foodScout, "xipu_life_expert", "civil_user");
        assignBadges(clubWalker, "veteran", "active_commenter");
        assignBadges(freshmanAsk, "civil_user");
        assignBadges(keyboardOwner, "secondhand_expert");
        assignBadges(studyPartner, "course_master", "helpful_star");

        ensurePointsHistory(xipuSeller, "POST_REWARD", 18, 25, 520, 360, "二手闲置区优质帖奖励");
        ensurePointsHistory(repairHelper, "HELPFUL_REPLY", 24, 35, 760, 540, "维修求助帖高质量回复");
        ensurePointsHistory(courseFinder, "COURSE_HELP", 15, 30, 330, 250, "课表查询经验整理");
        ensurePointsHistory(foodScout, "LIFE_SHARE", 12, 18, 210, 150, "食堂窗口推荐互动");
        seedExpandedCampusSnapshotData(moderator, market, life, course, ask, club);
    }

    private void seedExpandedCampusSnapshotData(User moderator, Section market, Section life,
                                                Section course, Section ask, Section club) {
        Section career = ensureSection("实习就业", "实习内推、招聘信息与面试经验", 3, moderator);
        Section postgraduate = ensureSection("保研考研", "夏令营、预推免、复试与备考交流", 2, moderator);
        Section railway = ensureSection("轨道交通", "轨道交通、铁路工程和专业学习交流", 9, moderator);
        Section programming = ensureSection("程序设计", "编程学习、项目协作与开发工具交流", 10, moderator);

        User librarySeat = ensureUser("library_seat_keeper", "library_seat_keeper@swjtu.edu.cn", "USER",
                "关注图书馆座位、打印和自习效率。", 3, 240, 310);
        User railwayMajor = ensureUser("railway_major_2026", "railway_major_2026@swjtu.edu.cn", "USER",
                "轨道交通专业学习记录者。", 4, 410, 480);
        User sportBuddy = ensureUser("sport_buddy_xipu", "sport_buddy_xipu@swjtu.edu.cn", "USER",
                "约跑、球场和运动打卡常驻用户。", 5, 520, 650);
        User photoWalk = ensureUser("photo_walk_swjtu", "photo_walk_swjtu@swjtu.edu.cn", "USER",
                "喜欢拍校园日落、银杏和列车元素。", 3, 260, 290);
        User lostFound = ensureUser("lost_found_guard", "lost_found_guard@swjtu.edu.cn", "USER",
                "整理失物招领格式和隐私提醒。", 4, 340, 420);
        User dormLife = ensureUser("dorm_life_notes", "dorm_life_notes@swjtu.edu.cn", "USER",
                "宿舍收纳、洗衣和生活小技巧分享。", 2, 170, 230);
        User internship = ensureUser("internship_ready", "internship_ready@swjtu.edu.cn", "USER",
                "简历、面试和实习信息互助。", 5, 590, 710);
        User programmer = ensureUser("java_lab_partner", "java_lab_partner@swjtu.edu.cn", "USER",
                "Java、数据库和课设协作答疑。", 4, 450, 560);
        User printHelper = ensureUser("print_shop_runner", "print_shop_runner@swjtu.edu.cn", "USER",
                "熟悉打印店、装订和资料整理路线。", 3, 230, 260);
        User notesKeeper = ensureUser("course_notes_keeper", "course_notes_keeper@swjtu.edu.cn", "USER",
                "课程笔记、复习清单和资料索引维护者。", 6, 720, 900);
        User commute = ensureUser("xipu_commute_observer", "xipu_commute_observer@swjtu.edu.cn", "USER",
                "记录犀浦通勤、校车和地铁换乘体验。", 3, 280, 340);
        User eventPlanner = ensureUser("campus_event_planner", "campus_event_planner@swjtu.edu.cn", "USER",
                "整理讲座、社团摊位和活动报名提醒。", 4, 390, 470);

        assignAvatar(librarySeat, "/uploads/avatars/demo-avatar-library-seat.png");
        assignAvatar(railwayMajor, "/uploads/avatars/demo-avatar-railway-major.png");
        assignAvatar(sportBuddy, "/uploads/avatars/demo-avatar-sport-buddy.png");
        assignAvatar(photoWalk, "/uploads/avatars/demo-avatar-photography.png");
        assignAvatar(lostFound, "/uploads/avatars/demo-avatar-lost-found.png");
        assignAvatar(dormLife, "/uploads/avatars/demo-avatar-dorm-life.png");
        assignAvatar(internship, "/uploads/avatars/demo-avatar-internship.png");
        assignAvatar(programmer, "/uploads/avatars/demo-avatar-programming.png");
        assignAvatar(printHelper, "/uploads/avatars/demo-avatar-print-shop.png");
        assignAvatar(notesKeeper, "/uploads/avatars/demo-avatar-course-notes.png");
        assignAvatar(commute, "/uploads/avatars/demo-avatar-commute.png");
        assignAvatar(eventPlanner, "/uploads/avatars/demo-avatar-campus-event.png");

        Set<Tag> libraryTags = tagSet("图书馆", "自习", "打印");
        Set<Tag> railwayTags = tagSet("轨道交通", "专业课", "课程互助");
        Set<Tag> sportTags = tagSet("运动打卡", "搭子", "犀浦生活");
        Set<Tag> photoTags = tagSet("摄影", "校园风景", "活动记录");
        Set<Tag> careerTags = tagSet("实习就业", "简历", "面试");
        Set<Tag> programmingTags = tagSet("Java", "课设", "数据库");
        Set<Tag> dormTags = tagSet("宿舍生活", "收纳", "二手闲置");
        Set<Tag> commuteTags = tagSet("通勤", "校车", "地铁");

        Post library1 = ensurePost("图书馆二楼靠窗座位什么时候比较容易有空位",
                librarySeat, life,
                "最近想固定找一个安静位置复习，但上午和下午的座位情况差异挺大。想问问大家二楼、三楼和自习室哪个时间段比较稳，也欢迎补充不用占座的文明自习建议。",
                libraryTags, 210, 18, 5, 13, 270);
        Post library2 = ensurePost("打印复习资料怎么装订比较划算？求经验",
                printHelper, ask,
                "期末资料页数比较多，想问问打印、双面、胶装和订书钉分别适合什么情况。希望大家分享的是流程和避坑点，不需要推荐具体个人联系方式。",
                libraryTags, 148, 11, 4, 9, 190);
        Post railway1 = ensurePost("轨道交通专业课复习顺序怎么安排更合理",
                railwayMajor, railway,
                "这学期几门专业课内容交叉比较多，想按基础概念、计算题、案例分析三个层次复习。有没有学长学姐可以分享一下先看哪类题更有效？",
                railwayTags, 234, 26, 7, 18, 340);
        Post railway2 = ensurePost("求铁路线路相关课程的实验报告排版建议",
                railwayMajor, course,
                "实验报告结构已经有了，但图表、数据说明和结论部分不知道怎么写得更清楚。希望参考的是排版和表达方法，不需要成品报告。",
                railwayTags, 119, 10, 3, 8, 160);
        Post sport1 = ensurePost("想找晚饭后一起绕校园慢跑的搭子",
                sportBuddy, club,
                "最近想恢复运动，但一个人不太容易坚持。计划晚饭后慢跑，不追求速度，主要是打卡和放松。感兴趣可以在帖子下面约时间段，尽量不要公开个人账号。",
                sportTags, 286, 32, 9, 20, 390);
        Post sport2 = ensurePost("犀浦校区羽毛球场预约有什么技巧吗",
                sportBuddy, life,
                "想和室友固定每周打一两次羽毛球，但热门时间段不太好约。求问大家一般提前多久看场地，哪些时间段更适合新手练习。",
                sportTags, 177, 16, 5, 11, 230);
        Post photo1 = ensurePost("这周校园日落很适合拍照，整理几个机位",
                photoWalk, life,
                "最近傍晚光线不错，整理了几个适合拍建筑、银杏和操场剪影的位置。提醒大家拍照时注意不要影响通行，也不要拍到同学正脸后公开发布。",
                photoTags, 301, 39, 8, 28, 430);
        Post photo2 = ensurePost("社团活动需要拍摄记录，有没有轻量设备建议",
                photoWalk, club,
                "社团活动想做照片和短视频记录，但设备不能太重。想问问手机、运动相机和入门微单分别适合什么场景，后期整理有没有推荐流程。",
                photoTags, 156, 14, 4, 10, 210);
        Post lost1 = ensurePost("在教学楼捡到校园卡，已交到楼栋值班处",
                lostFound, life,
                "今天在教学楼走廊捡到一张校园卡，已经交给值班处。为保护隐私不公开姓名和完整编号，失主可以按时间地点去值班处核对。",
                tagSet("失物招领", "隐私保护", "校园卡"), 260, 34, 6, 15, 360);
        Post lost2 = ensurePost("求助：雨伞可能落在教室，怎么找回比较快",
                lostFound, ask,
                "下午上课后发现雨伞不见了，可能落在教室或楼道。想问问一般是先问任课教室、楼栋值班处，还是等失物招领集中整理？",
                tagSet("失物招领", "打听求助", "雨伞"), 128, 9, 4, 6, 170);
        Post dorm1 = ensurePost("宿舍桌面收纳有什么不占地方的方案",
                dormLife, life,
                "书、资料、插排和水杯堆在一起很乱，想找不影响学习桌空间的收纳方式。欢迎分享架子、文件盒、线缆整理这些实际好用的方案。",
                dormTags, 196, 22, 7, 14, 280);
        Post dorm2 = ensurePost("出几本公共课教材和文件夹，适合低年级同学",
                dormLife, market,
                "整理宿舍发现几本公共课教材和文件夹，保存还可以。想转给需要的同学，默认校内面交，具体书名可以在评论里确认，不留外部联系方式。",
                dormTags, 143, 12, 4, 8, 185);
        Post career1 = ensurePost("第一次投实习简历，项目经历怎么写不空泛",
                internship, career,
                "课设、课程项目和社团经历都有，但写进简历后感觉像流水账。想问问大家怎么突出职责、结果和技术点，尤其是没有正式实习经历时怎么表达。",
                careerTags, 336, 45, 10, 34, 520);
        Post career2 = ensurePost("面试复盘：被问到数据库索引和事务时怎么答",
                internship, career,
                "最近一次面试被问到索引、事务隔离级别和慢查询定位，答得不够系统。整理了一版复盘，欢迎同学补充常见追问和更清晰的回答结构。",
                careerTags, 289, 37, 9, 26, 460);
        Post code1 = ensurePost("Java 课设后端接口联调老是 403，排查顺序分享",
                programmer, programming,
                "最近做课设联调时遇到过 403、token 过期、前端代理路径不一致等问题。我把自己的排查顺序写一下：先看请求路径，再看登录态，再看后端权限配置，最后看浏览器控制台。",
                programmingTags, 402, 52, 12, 41, 610);
        Post code2 = ensurePost("数据库表设计评审：论坛系统哪些字段最容易漏",
                programmer, programming,
                "帖子、评论、用户、徽章这些表看起来简单，但统计字段、状态字段、审核记录和收藏浏览记录很容易漏。这里列一版课设答辩时比较容易被问到的点。",
                programmingTags, 350, 48, 11, 36, 560);
        Post notes1 = ensurePost("整理一个期末资料索引帖：大家可以按课程补充",
                notesKeeper, course,
                "为了减少重复求资料，我想做一个索引帖。评论区可以按课程名、资料类型、适用范围来补充，不放网盘提取码和个人账号，只描述资料内容和获取方式。",
                tagSet("期末复习", "资料索引", "课程互助"), 470, 61, 16, 52, 720);
        Post notes2 = ensurePost("通识课选择建议：更适合大三同学的时间安排",
                notesKeeper, course,
                "大三课程、实验和实习准备比较挤，通识课最好看时间、考核方式和作业频率。想整理一份不涉及刷分的选择建议，帮助大家合理安排课表。",
                tagSet("选课", "通识课", "课表"), 244, 29, 8, 21, 350);
        Post commute1 = ensurePost("犀浦到市区通勤路线怎么选更稳",
                commute, life,
                "周末去市区办事，想比较一下地铁、校车和打车拼车的时间稳定性。希望大家分享的是路线体验和时间预估，不涉及私人拼车联系方式。",
                commuteTags, 225, 24, 7, 18, 310);
        Post commute2 = ensurePost("早八通勤避坑：哪些时间段容易堵",
                commute, life,
                "最近几次早八差点迟到，感觉不同路线差异挺大。想整理一下早高峰容易堵的时间段，以及提前出门多久比较保险。",
                commuteTags, 183, 18, 5, 12, 250);
        Post event1 = ensurePost("本周讲座和社团摊位信息汇总",
                eventPlanner, club,
                "把这周看到的讲座、社团摊位和活动报名信息做一个汇总。欢迎社团负责人在评论里补充时间地点，注意不要发布个人联系方式，统一用站内消息沟通。",
                tagSet("社团活动", "讲座", "报名提醒"), 388, 44, 13, 32, 540);
        Post event2 = ensurePost("新生参加社团活动前需要准备什么",
                eventPlanner, club,
                "很多新生第一次参加社团活动会紧张，其实提前看清时间地点、活动要求和是否需要报名就可以。也建议活动组织者把规则写清楚，减少临场沟通成本。",
                tagSet("社团招新", "新生", "活动指南"), 219, 23, 6, 17, 300);
        Post pg1 = ensurePost("保研材料开始准备时，推荐先整理哪些内容",
                notesKeeper, postgraduate,
                "成绩单、获奖、科研项目、英语成绩和个人陈述最好提前归档。这里整理一个材料清单，适合刚开始准备的同学对照，不涉及任何机构广告。",
                tagSet("保研", "材料清单", "经验分享"), 332, 40, 10, 29, 500);
        Post pg2 = ensurePost("考研复习到六月，如何调整每天的任务量",
                notesKeeper, postgraduate,
                "复习计划不能只看时长，更要看任务完成质量。建议把大目标拆成每日题量、错题复盘和背诵轮次，周末留出半天做调整。",
                tagSet("考研", "复习计划", "时间管理"), 305, 36, 9, 25, 470);

        ensureComment(library1, notesKeeper, "二楼靠窗上午比较紧张，下午晚些时候反而容易有零散位置。");
        ensureComment(library1, dormLife, "建议不要用物品长期占座，临时离开可以给旁边同学说一声。");
        ensureComment(library2, notesKeeper, "双面打印加简单装订就够用了，太厚的资料可以分章节装。");
        ensureComment(railway1, notesKeeper, "先把概念框架过一遍，再做计算题，最后看案例题会顺很多。");
        ensureComment(railway2, programmer, "图表编号和数据来源写清楚，老师看起来会更省力。");
        ensureComment(sport1, eventPlanner, "可以把时间段写成几个备选，避免评论里来回确认。");
        ensureComment(sport2, sportBuddy, "新手可以避开饭后黄金时间，周末上午体验会好一点。");
        ensureComment(photo1, lostFound, "不拍同学正脸这个提醒很重要，校园摄影也要注意隐私。");
        ensureComment(photo2, eventPlanner, "社团活动记录重点是流程完整，不一定需要很重的设备。");
        ensureComment(lost1, dormLife, "这样处理很规范，不公开完整信息更安全。");
        ensureComment(lost2, lostFound, "先问教室楼栋值班处，再看当天失物招领集中登记。");
        ensureComment(dorm1, librarySeat, "线缆整理真的有用，桌面会立刻清爽很多。");
        ensureComment(dorm2, dormLife, "低年级同学很需要这种教材，建议写清版本和新旧程度。");
        ensureComment(career1, programmer, "项目经历可以按问题、方案、结果写，不要只堆技术名词。");
        ensureComment(career2, internship, "事务隔离级别可以结合实际场景答，会比背概念自然。");
        ensureComment(code1, programmer, "403 先看 token 和路径，别一上来就改后端权限。");
        ensureComment(code1, internship, "这个排查顺序适合放进课设联调文档。");
        ensureComment(code2, notesKeeper, "状态字段和审核日志确实容易漏，答辩很可能会问。");
        ensureComment(notes1, railwayMajor, "索引帖很有必要，资料分散在各个帖子里太难找了。");
        ensureComment(notes1, printHelper, "可以加一个打印建议列，期末会很实用。");
        ensureComment(notes2, librarySeat, "大三确实要把实验和实习准备时间留出来。");
        ensureComment(commute1, eventPlanner, "活动集中时去市区要提前看路线，别卡点出发。");
        ensureComment(commute2, sportBuddy, "早八最好给自己留 15 到 20 分钟缓冲。");
        ensureComment(event1, moderator, "活动汇总可以保留，注意后续评论里不要出现私人联系方式。");
        ensureComment(event1, photoWalk, "如果需要拍照记录，可以提前说明是否允许拍摄。");
        ensureComment(event2, dormLife, "新生看到这种指南会安心很多。");
        ensureComment(pg1, internship, "材料清单最好按月份安排，不然容易临近才发现缺证明。");
        ensureComment(pg1, notesKeeper, "个人陈述不要照搬模板，经历和动机要能对应上。");
        ensureComment(pg2, railwayMajor, "任务量按周调整更稳，状态不好时也不至于全盘崩。");
        ensureComment(pg2, librarySeat, "错题复盘比盲目刷题重要，尤其是后期。");
        ensureComment(commute1, commute, "食堂排队情况和通勤时间其实很相关，赶课前要选快的窗口。");
        ensureComment(code1, programmer, "维修帖和 403 帖都说明：先定位问题，再决定要不要大改。");
        ensureComment(dorm2, lostFound, "二手交易也建议少公开个人信息，用站内私信就够了。");
        ensureComment(event1, eventPlanner, "跨校小组如果能和校内活动分区联动，会更像完整社区。");

        ensureFavorite(librarySeat, notes1);
        ensureFavorite(railwayMajor, railway1);
        ensureFavorite(sportBuddy, sport1);
        ensureFavorite(photoWalk, photo1);
        ensureFavorite(lostFound, lost1);
        ensureFavorite(internship, career1);
        ensureFavorite(programmer, code1);
        ensureFavorite(notesKeeper, pg1);
        ensureBrowseHistory(librarySeat, library2);
        ensureBrowseHistory(railwayMajor, railway2);
        ensureBrowseHistory(sportBuddy, event1);
        ensureBrowseHistory(photoWalk, photo2);
        ensureBrowseHistory(lostFound, lost2);
        ensureBrowseHistory(internship, career2);
        ensureBrowseHistory(programmer, code2);
        ensureBrowseHistory(notesKeeper, notes2);

        assignBadges(librarySeat, "active_commenter", "civil_user");
        assignBadges(railwayMajor, "course_master", "helpful_star");
        assignBadges(sportBuddy, "active_commenter", "veteran");
        assignBadges(photoWalk, "civil_user", "post_master");
        assignBadges(lostFound, "helpful_star", "civil_user");
        assignBadges(dormLife, "secondhand_expert", "civil_user");
        assignBadges(internship, "helpful_star", "active_commenter");
        assignBadges(programmer, "course_master", "post_master");
        assignBadges(printHelper, "helpful_star");
        assignBadges(notesKeeper, "course_master", "veteran", "collector");
        assignBadges(commute, "xipu_life_expert", "civil_user");
        assignBadges(eventPlanner, "circle_creator", "active_commenter");

        ensurePointsHistory(librarySeat, "LIBRARY_SHARE", 12, 18, 310, 240, "图书馆自习经验分享");
        ensurePointsHistory(railwayMajor, "COURSE_HELP", 18, 24, 480, 410, "轨道交通课程互助");
        ensurePointsHistory(sportBuddy, "CIRCLE_ACTIVITY", 20, 28, 650, 520, "运动打卡组织互动");
        ensurePointsHistory(photoWalk, "CAMPUS_SHARE", 14, 20, 290, 260, "校园摄影内容分享");
        ensurePointsHistory(internship, "CAREER_HELP", 24, 35, 710, 590, "实习面试复盘");
        ensurePointsHistory(programmer, "TECH_HELP", 26, 38, 560, 450, "课设联调经验分享");
        ensurePointsHistory(notesKeeper, "RESOURCE_INDEX", 30, 45, 900, 720, "期末资料索引维护");
        ensurePointsHistory(eventPlanner, "EVENT_SHARE", 18, 25, 470, 390, "社团活动汇总");
    }

    private void resetScenarioState(User student) {
        postFavoriteRepository.deleteByUser(student);
        postBrowseHistoryRepository.deleteByUser(student);
        pointsHistoryRepository.deleteByUser(student);
        redemptionRequestRepository.deleteByUser(student);
        // Comments may already have likes or replies in a reused MySQL database.
        // Keep them and let ensureComment remain idempotent instead of breaking FK constraints.
        dailyCheckInRepository.deleteByUser(student);
        student.setPoints(260);
        student.setExp(180);
        student.setConsecutiveDays(0);
        userRepository.save(student);
    }

    private User ensureUser(String username, String email, String role, String bio, int level, int exp, int points) {
        Optional<User> existing = userRepository.findByUsername(username);
        if (existing.isPresent()) {
            return existing.get();
        }

        User user = new User();
        user.setUsername(username);
        user.setPassword(passwordEncoder.encode(DEFAULT_PASSWORD));
        user.setEmail(email);
        user.setRole(role);
        user.setBio(bio);
        user.setLevel(level);
        user.setExp(exp);
        user.setPoints(points);
        user.setEnabled(true);
        user.setCampusIdentityStatus("VERIFIED");
        user.setCampusVerified(true);
        return userRepository.save(user);
    }

    private Section ensureSection(String name, String description, int sortOrder, User moderator) {
        return sectionRepository.findByName(name).orElseGet(() -> {
            Section section = new Section();
            section.setName(name);
            section.setDescription(description);
            section.setSortOrder(sortOrder);
            section.setModerator(moderator);
            return sectionRepository.save(section);
        });
    }

    private Tag ensureTag(String name, String category) {
        return tagRepository.findByName(name).orElseGet(() -> {
            Tag tag = new Tag();
            tag.setName(name);
            tag.setCategory(category);
            tag.setUseCount(1);
            return tagRepository.save(tag);
        });
    }

    private Set<Tag> tagSet(String... names) {
        Set<Tag> tags = new LinkedHashSet<>();
        for (String name : names) {
            tags.add(ensureTag(name, "campus-snapshot"));
        }
        return tags;
    }

    private Post ensurePost(String title, User author, Section section, String content, Set<Tag> tags,
                            int views, int likes, int comments, int collects, int heat) {
        return ensurePost(title, author, section, content, tags, views, likes, comments, collects, heat, PostService.STATUS_PUBLISHED);
    }

    private Post ensurePost(String title, User author, Section section, String content, Set<Tag> tags,
                            int views, int likes, int comments, int collects, int heat, int status) {
        return postRepository.findByTitle(title).orElseGet(() -> {
            Post post = new Post();
            post.setTitle(title);
            post.setAuthor(author);
            post.setSection(section);
            post.setContent(content);
            post.setStatus(status);
            post.setViewCount(views);
            post.setLikeCount(likes);
            post.setCommentCount(comments);
            post.setCollectCount(collects);
            post.setHeatScore(heat);
            post.setTags(tags);
            return postRepository.save(post);
        });
    }

    private RewardItem ensureReward(String name, String description, int costPoints, int stock) {
        return rewardItemRepository.findByName(name).orElseGet(() -> {
            RewardItem rewardItem = new RewardItem();
            rewardItem.setName(name);
            rewardItem.setDescription(description);
            rewardItem.setCostPoints(costPoints);
            rewardItem.setStock(stock);
            rewardItem.setStatus(1);
            return rewardItemRepository.save(rewardItem);
        });
    }

    private void ensureComment(Post post, User author, String content) {
        if (commentRepository.findByPostAndAuthorAndContent(post, author, content).isPresent()) {
            return;
        }
        com.swjtu.forum.entity.Comment comment = new com.swjtu.forum.entity.Comment();
        comment.setPost(post);
        comment.setAuthor(author);
        comment.setContent(content);
        commentRepository.save(comment);
    }

    private void ensureFavorite(User user, Post post) {
        if (postFavoriteRepository.findByUserAndPost(user, post).isPresent()) {
            return;
        }
        PostFavorite favorite = new PostFavorite();
        favorite.setUser(user);
        favorite.setPost(post);
        postFavoriteRepository.save(favorite);
    }

    private void ensureBrowseHistory(User user, Post post) {
        if (postBrowseHistoryRepository.findByUserAndPost(user, post).isPresent()) {
            return;
        }
        PostBrowseHistory history = new PostBrowseHistory();
        history.setUser(user);
        history.setPost(post);
        postBrowseHistoryRepository.save(history);
    }

    private void ensurePointsHistory(User user, String changeType, int pointsDelta, int expDelta,
                                     int currentPoints, int currentExp, String note) {
        if (pointsHistoryRepository.findByUserAndChangeTypeAndNote(user, changeType, note).isPresent()) {
            return;
        }
        PointsHistory history = new PointsHistory();
        history.setUser(user);
        history.setChangeType(changeType);
        history.setPointsDelta(pointsDelta);
        history.setExpDelta(expDelta);
        history.setCurrentPoints(currentPoints);
        history.setCurrentExp(currentExp);
        history.setNote(note);
        pointsHistoryRepository.save(history);
    }

    private void ensureRedemption(User user, RewardItem reward, int status, int pointsCost, String reviewNote) {
        if (redemptionRequestRepository.findByUserAndRewardAndStatus(user, reward, status).isPresent()) {
            return;
        }
        RedemptionRequest request = new RedemptionRequest();
        request.setUser(user);
        request.setReward(reward);
        request.setStatus(status);
        request.setPointsCost(pointsCost);
        request.setReviewNote(reviewNote);
        redemptionRequestRepository.save(request);
    }

    private void ensureOperationLog(User actor, String action, String targetType, Long targetId, String detail) {
        if (operationLogRepository.findByActionAndTargetTypeAndTargetId(action, targetType, targetId).isPresent()) {
            return;
        }
        com.swjtu.forum.entity.OperationLog operationLog = new com.swjtu.forum.entity.OperationLog();
        operationLog.setActor(actor);
        operationLog.setAction(action);
        operationLog.setTargetType(targetType);
        operationLog.setTargetId(targetId);
        operationLog.setDetail(detail);
        operationLogRepository.save(operationLog);
    }

    private void assignBadges(User user, String... badgeCodes) {
        for (String code : badgeCodes) {
            Optional<Badge> badge = badgeRepository.findByCode(code);
            if (badge.isEmpty() || userBadgeRepository.findByUserAndBadge(user, badge.get()).isPresent()) {
                continue;
            }
            UserBadge userBadge = new UserBadge();
            userBadge.setUser(user);
            userBadge.setBadge(badge.get());
            userBadgeRepository.save(userBadge);
        }
    }

    private void assignAvatar(User user, String avatarUrl) {
        if (avatarUrl.equals(user.getAvatar())) {
            return;
        }
        user.setAvatar(avatarUrl);
        userRepository.save(user);
    }

    private void touchReadRepositories() {
        commentRepository.count();
        postLikeRepository.count();
        postFavoriteRepository.count();
        postBrowseHistoryRepository.count();
        pointsHistoryRepository.count();
        redemptionRequestRepository.count();
        operationLogRepository.count();
    }
}
