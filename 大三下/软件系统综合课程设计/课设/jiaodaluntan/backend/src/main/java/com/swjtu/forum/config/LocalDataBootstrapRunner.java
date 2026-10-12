package com.swjtu.forum.config;

import com.swjtu.forum.entity.Circle;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.entity.Tag;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.repository.CircleRepository;
import com.swjtu.forum.repository.PostRepository;
import com.swjtu.forum.repository.SectionRepository;
import com.swjtu.forum.repository.TagRepository;
import com.swjtu.forum.repository.UserRepository;
import com.swjtu.forum.service.BadgeService;
import com.swjtu.forum.service.PostService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.LinkedHashSet;
import java.util.Set;

@Component
public class LocalDataBootstrapRunner implements ApplicationRunner {

    private static final String[] INTEREST_TAGS = {
            "课程互助", "考研保研", "实习就业", "二手闲置",
            "失物招领", "犀浦生活", "社团活动", "运动健身",
            "程序设计", "轨道交通", "摄影旅行", "美食探店"
    };

    private static final String[][] DEFAULT_CIRCLES = {
            {"课程资料互助会", "course-help", "课", "共享课程资料、作业经验、考试复习路线。"},
            {"考研保研同行圈", "postgraduate-road", "研", "保研、考研、夏令营、复试经验集中交流。"},
            {"犀浦生活情报站", "xipu-life", "犀", "食堂、通勤、图书馆、校园生活信息速递。"},
            {"实习就业内推局", "career-internship", "职", "实习内推、招聘信息、面试复盘和简历互助。"},
            {"二手失物互助站", "market-lost-found", "物", "二手闲置、失物招领和校内交易提醒。"}
    };

    private final SectionRepository sectionRepository;
    private final UserRepository userRepository;
    private final TagRepository tagRepository;
    private final CircleRepository circleRepository;
    private final PostRepository postRepository;
    private final PasswordEncoder passwordEncoder;
    private final BadgeService badgeService;

    @Value("${app.bootstrap.enabled:true}")
    private boolean enabled;

    @Value("${app.bootstrap.admin-username:admin}")
    private String adminUsername;

    @Value("${app.bootstrap.admin-password:admin123456}")
    private String adminPassword;

    @Value("${app.bootstrap.admin-email:admin@swjtu.local}")
    private String adminEmail;

    public LocalDataBootstrapRunner(SectionRepository sectionRepository,
                                    UserRepository userRepository,
                                    TagRepository tagRepository,
                                    CircleRepository circleRepository,
                                    PostRepository postRepository,
                                    PasswordEncoder passwordEncoder,
                                    BadgeService badgeService) {
        this.sectionRepository = sectionRepository;
        this.userRepository = userRepository;
        this.tagRepository = tagRepository;
        this.circleRepository = circleRepository;
        this.postRepository = postRepository;
        this.passwordEncoder = passwordEncoder;
        this.badgeService = badgeService;
    }

    @Override
    @Transactional
    public void run(ApplicationArguments args) {
        if (!enabled) {
            return;
        }

        User admin = ensureAdminUser();
        Section notice = ensureSection("站务公告", "论坛规则、系统通知与运营说明", 0, admin);
        ensureSection("课程互助", "课程资料、选课建议、作业与考试经验", 1, admin);
        ensureSection("保研考研", "夏令营、预推免、复试与备考交流", 2, admin);
        ensureSection("实习就业", "实习内推、招聘信息与面试经验", 3, admin);
        ensureSection("犀浦生活", "校区生活、食堂、图书馆和通勤信息", 4, admin);
        ensureSection("二手闲置", "校内二手、转让与交易提醒", 5, admin);
        ensureSection("失物招领", "失物、拾物、求助与线下联系", 6, admin);

        ensureWelcomePost(admin, notice);
        ensureInterestTags();
        ensureDefaultCircles(admin);
        badgeService.initializeBadgeDefinitions();
    }

    private User ensureAdminUser() {
        return userRepository.findByUsername(adminUsername).orElseGet(() -> {
            User user = new User();
            user.setUsername(adminUsername);
            user.setEmail(adminEmail);
            user.setPassword(passwordEncoder.encode(adminPassword));
            user.setRole("ADMIN");
            user.setEnabled(true);
            user.setCampusVerified(true);
            user.setCampusIdentityStatus("VERIFIED");
            user.setCollege("西南交通大学");
            user.setMajor("论坛运营");
            user.setBio("本地可用版本初始化管理员");
            user.setLevel(5);
            user.setExp(500);
            user.setPoints(1000);
            return userRepository.save(user);
        });
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

    private void ensureWelcomePost(User admin, Section section) {
        String title = "欢迎来到西南交大论坛本地可用版";
        if (postRepository.findByTitle(title).isPresent()) {
            return;
        }

        Set<Tag> tags = new LinkedHashSet<>();
        tags.add(ensureTag("站务公告", "system"));
        tags.add(ensureTag("使用说明", "system"));

        Post post = new Post();
        post.setAuthor(admin);
        post.setSection(section);
        post.setTitle(title);
        post.setContent("当前版本使用本地 H2 持久化数据库，注册、登录、发帖、评论、收藏、管理操作都会写入 backend/data/swjtu-forum-local.mv.db。普通用户可以直接注册并使用论坛功能；管理后台仅对具有管理员权限的账号开放。");
        post.setStatus(PostService.STATUS_PUBLISHED);
        post.setViewCount(0);
        post.setLikeCount(0);
        post.setCommentCount(0);
        post.setCollectCount(0);
        post.setHeatScore(100);
        post.setTags(tags);
        postRepository.save(post);

        section.setPostCount(section.getPostCount() + 1);
        sectionRepository.save(section);
    }

    private void ensureInterestTags() {
        for (String tagName : INTEREST_TAGS) {
            ensureTag(tagName, "interest");
        }
    }

    private void ensureDefaultCircles(User admin) {
        for (String[] item : DEFAULT_CIRCLES) {
            circleRepository.findBySlug(item[1]).orElseGet(() -> {
                Circle circle = new Circle();
                circle.setName(item[0]);
                circle.setSlug(item[1]);
                circle.setIcon(item[2]);
                circle.setDescription(item[3]);
                circle.setCreator(admin);
                return circleRepository.save(circle);
            });
        }
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
}
