package com.swjtu.forum.service;

import com.swjtu.forum.entity.Badge;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.entity.UserBadge;
import com.swjtu.forum.exception.NotFoundException;
import com.swjtu.forum.repository.BadgeRepository;
import com.swjtu.forum.repository.CommentRepository;
import com.swjtu.forum.repository.PostFavoriteRepository;
import com.swjtu.forum.repository.PostRepository;
import com.swjtu.forum.repository.SectionRepository;
import com.swjtu.forum.repository.UserBadgeRepository;
import com.swjtu.forum.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class BadgeService {

    private static final List<BadgeDefinition> DEFINITIONS = List.of(
            new BadgeDefinition("course_master", "课程大神", "课程互助区 5 条回复被采纳", "🎓", "成就", 10),
            new BadgeDefinition("secondhand_expert", "二手达人", "发布 5 条二手闲置帖", "♻", "成就", 20),
            new BadgeDefinition("xipu_life_expert", "犀浦生活家", "犀浦生活区发帖超 10 篇", "🏫", "成就", 30),
            new BadgeDefinition("early_warrior", "早八战士", "连续签到 7 天", "⏰", "签到", 40),
            new BadgeDefinition("civil_user", "文明发言者", "注册满 30 天且账号状态正常", "🌟", "品质", 50),
            new BadgeDefinition("veteran", "论坛元老", "注册满 60 天", "👑", "资历", 60),
            new BadgeDefinition("active_commenter", "活跃评论者", "发表超 20 条评论", "💬", "活跃", 70),
            new BadgeDefinition("helpful_star", "互助之星", "至少 1 条回复被采纳", "⭐", "成就", 80),
            new BadgeDefinition("post_master", "发帖达人", "发布超 20 篇帖子", "📝", "活跃", 90),
            new BadgeDefinition("collector", "收藏达人", "收藏超 10 个帖子", "📌", "活跃", 100),
            new BadgeDefinition("danmaku_pioneer", "弹幕先锋", "发送超 10 条弹幕", "🔥", "活跃", 110),
            new BadgeDefinition("circle_creator", "圈子创建者", "创建兴趣圈子", "🌐", "成就", 120)
    );

    private final BadgeRepository badgeRepository;
    private final UserBadgeRepository userBadgeRepository;
    private final UserRepository userRepository;
    private final PostRepository postRepository;
    private final CommentRepository commentRepository;
    private final PostFavoriteRepository postFavoriteRepository;
    private final SectionRepository sectionRepository;
    private final UserService userService;

    @Transactional
    public void initializeBadgeDefinitions() {
        for (BadgeDefinition definition : DEFINITIONS) {
            badgeRepository.findByCode(definition.code()).orElseGet(() -> {
                Badge badge = new Badge();
                badge.setCode(definition.code());
                badge.setName(definition.name());
                badge.setDescription(definition.description());
                badge.setIcon(definition.icon());
                badge.setCategory(definition.category());
                badge.setSortOrder(definition.sortOrder());
                return badgeRepository.save(badge);
            });
        }
    }

    @Transactional(readOnly = true)
    public List<Badge> listBadges() {
        return badgeRepository.findAllByOrderBySortOrderAsc();
    }

    @Transactional(readOnly = true)
    public List<UserBadge> listUserBadges(Long userId) {
        User user = userRepository.findById(userId).orElseThrow(() -> new NotFoundException("用户不存在"));
        return userBadgeRepository.findByUserOrderByEarnedAtDesc(user);
    }

    @Transactional(readOnly = true)
    public List<UserBadge> listCurrentUserBadges(String username) {
        return userBadgeRepository.findByUserOrderByEarnedAtDesc(userService.getUserByUsername(username));
    }

    @Transactional
    public List<UserBadge> checkCurrentUserBadges(String username) {
        return checkUserBadges(userService.getUserByUsername(username));
    }

    @Transactional
    public List<UserBadge> checkUserBadges(User user) {
        if (user == null || user.getId() == null) {
            return List.of();
        }
        List<UserBadge> newlyEarned = new ArrayList<>();
        for (BadgeDefinition definition : DEFINITIONS) {
            if (matches(user, definition.code())) {
                grant(user, definition.code()).ifPresent(newlyEarned::add);
            }
        }
        return newlyEarned;
    }

    @Transactional
    public java.util.Optional<UserBadge> grantByCode(User user, String code) {
        return grant(user, code);
    }

    private java.util.Optional<UserBadge> grant(User user, String code) {
        return badgeRepository.findByCode(code)
                .filter(badge -> userBadgeRepository.findByUserAndBadge(user, badge).isEmpty())
                .map(badge -> {
                    UserBadge userBadge = new UserBadge();
                    userBadge.setUser(user);
                    userBadge.setBadge(badge);
                    return userBadgeRepository.save(userBadge);
                });
    }

    private boolean matches(User user, String code) {
        return switch (code) {
            case "course_master" -> commentRepository.countByAuthorAndAcceptedTrue(user) >= 5;
            case "secondhand_expert" -> countPostsInSection(user, "二手闲置") >= 5;
            case "xipu_life_expert" -> countPostsInSection(user, "犀浦生活") >= 10;
            case "early_warrior" -> safe(user.getConsecutiveDays()) >= 7;
            case "civil_user" -> Boolean.TRUE.equals(user.getEnabled()) && registeredDays(user) >= 30;
            case "veteran" -> registeredDays(user) >= 60;
            case "active_commenter" -> commentRepository.countByAuthor(user) >= 20;
            case "helpful_star" -> commentRepository.countByAuthorAndAcceptedTrue(user) >= 1;
            case "post_master" -> postRepository.countByAuthorAndStatus(user, PostService.STATUS_PUBLISHED) >= 20;
            case "collector" -> postFavoriteRepository.countByUser(user) >= 10;
            default -> false;
        };
    }

    private long countPostsInSection(User user, String sectionName) {
        return sectionRepository.findByName(sectionName)
                .map(section -> postRepository.countByAuthorAndSectionAndStatus(user, section, PostService.STATUS_PUBLISHED))
                .orElse(0L);
    }

    private long registeredDays(User user) {
        if (user.getCreatedAt() == null) {
            return 0L;
        }
        return java.time.Duration.between(user.getCreatedAt(), LocalDateTime.now()).toDays();
    }

    private int safe(Integer value) {
        return value == null ? 0 : value;
    }

    private record BadgeDefinition(String code, String name, String description, String icon, String category,
                                   int sortOrder) {
    }
}
