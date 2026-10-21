package com.swjtu.forum.service;

import com.swjtu.forum.dto.RecommendationConfigRequest;
import com.swjtu.forum.dto.RecommendationPreviewResponse;
import com.swjtu.forum.dto.RewardItemManageRequest;
import com.swjtu.forum.entity.*;
import com.swjtu.forum.exception.ApiException;
import com.swjtu.forum.exception.NotFoundException;
import com.swjtu.forum.repository.*;
import com.swjtu.forum.util.Pageables;
import lombok.RequiredArgsConstructor;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class GrowthDiscoveryService {

    private static final int CHECK_IN_POINTS = 10;
    private static final int CHECK_IN_EXP = 5;

    private final UserService userService;
    private final PostRepository postRepository;
    private final PostDisinterestRepository postDisinterestRepository;
    private final DailyCheckInRepository dailyCheckInRepository;
    private final PointsHistoryRepository pointsHistoryRepository;
    private final RewardItemRepository rewardItemRepository;
    private final RedemptionRequestRepository redemptionRequestRepository;
    private final TagRepository tagRepository;
    private final UserRepository userRepository;
    private final CommentRepository commentRepository;
    private final RecommendationConfigRepository recommendationConfigRepository;
    private final NotificationService notificationService;
    private final UserFollowRepository userFollowRepository;
    private final BadgeService badgeService;

    /** Additive boost (on the same 0–100 scale as the weighted score) for posts authored by followed users. */
    private static final double SOCIAL_BONUS = 25D;

    @Transactional(readOnly = true)
    public Page<Post> searchPosts(String keyword, Pageable pageable) {
        if (!StringUtils.hasText(keyword)) {
            return postRepository.findByStatusOrderByCreatedAtDesc(PostService.STATUS_PUBLISHED, pageable);
        }
        return postRepository.searchPublishedExtended(PostService.STATUS_PUBLISHED, keyword.trim(), pageable);
    }

    @Transactional(readOnly = true)
    public Page<Post> recommendPosts(String username, Pageable pageable) {
        User user = userService.getUserByUsername(username);
        return buildRecommendationPage(user, pageable);
    }

    public RecommendationConfig getRecommendationConfig() {
        return loadRecommendationConfig();
    }

    @Transactional
    public RecommendationConfig updateRecommendationConfig(RecommendationConfigRequest request) {
        int totalWeight = request.getTagWeight() + request.getEngagementWeight() + request.getRecencyWeight();
        if (totalWeight != 100) {
            throw new ApiException(400, "推荐因子权重总和必须为 100");
        }

        RecommendationConfig config = loadRecommendationConfig();
        config.setTagWeight(request.getTagWeight());
        config.setEngagementWeight(request.getEngagementWeight());
        config.setRecencyWeight(request.getRecencyWeight());
        config.setExplainabilityEnabled(request.getExplainabilityEnabled());
        return recommendationConfigRepository.save(config);
    }

    @Transactional(readOnly = true)
    public RecommendationPreviewResponse previewRecommendations(String username, int limit) {
        User user = StringUtils.hasText(username) ? userService.getUserByUsername(username.trim()) : null;
        Page<Post> page = buildRecommendationPage(user, PageRequest.of(0, Pageables.safeSize(limit)));

        RecommendationPreviewResponse response = new RecommendationPreviewResponse();
        response.setViewerUsername(user == null ? null : user.getUsername());
        response.setInterestTags(user == null
                ? List.of()
                : user.getTags().stream().map(Tag::getName).sorted().toList());
        response.setPosts(page.getContent());
        return response;
    }

    @Transactional
    public void markNotInterested(Long postId, String username) {
        User user = userService.getUserByUsername(username);
        Post post = postRepository.findById(postId).orElseThrow(() -> new NotFoundException("帖子不存在"));
        if (!postDisinterestRepository.existsByUserAndPost(user, post)) {
            PostDisinterest record = new PostDisinterest();
            record.setUser(user);
            record.setPost(post);
            postDisinterestRepository.save(record);
        }
    }

    @Transactional
    public Set<Tag> updateInterests(String username, List<String> names) {
        User user = userService.getUserByUsername(username);
        Set<Tag> tags = new HashSet<>();
        if (names != null) {
            for (String raw : names) {
                if (!StringUtils.hasText(raw)) continue;
                String name = raw.trim();
                Tag tag = tagRepository.findByName(name).orElseGet(() -> {
                    Tag t = new Tag();
                    t.setName(name);
                    t.setCategory("interest");
                    return tagRepository.save(t);
                });
                tags.add(tag);
            }
        }
        user.setTags(tags);
        userRepository.save(user);
        return tags;
    }

    @Transactional
    public DailyCheckIn checkIn(String username) {
        User user = userService.getUserByUsername(username);
        LocalDate today = LocalDate.now();
        if (dailyCheckInRepository.findByUserAndCheckDate(user, today).isPresent()) {
            throw new ApiException(400, "今日已签到");
        }

        DailyCheckIn checkIn = new DailyCheckIn();
        checkIn.setUser(user);
        checkIn.setCheckDate(today);
        checkIn.setGainedPoints(CHECK_IN_POINTS);
        checkIn.setGainedExp(CHECK_IN_EXP);
        DailyCheckIn saved;
        try {
            saved = dailyCheckInRepository.saveAndFlush(checkIn);
        } catch (DataIntegrityViolationException ex) {
            // The (user_id, check_date) unique constraint is the source of truth; a duplicate
            // means a concurrent request already checked in today.
            throw new ApiException(400, "今日已签到");
        }

        int currentPoints = user.getPoints() == null ? 0 : user.getPoints();
        int currentExp = user.getExp() == null ? 0 : user.getExp();
        int consecutiveDays = user.getConsecutiveDays() == null ? 0 : user.getConsecutiveDays();
        boolean checkedInYesterday = dailyCheckInRepository.findByUserAndCheckDate(user, today.minusDays(1)).isPresent();

        user.setPoints(currentPoints + CHECK_IN_POINTS);
        user.setExp(currentExp + CHECK_IN_EXP);
        user.setConsecutiveDays(checkedInYesterday ? consecutiveDays + 1 : 1);
        userRepository.save(user);

        PointsHistory history = new PointsHistory();
        history.setUser(user);
        history.setChangeType("CHECK_IN");
        history.setPointsDelta(CHECK_IN_POINTS);
        history.setExpDelta(CHECK_IN_EXP);
        history.setCurrentPoints(user.getPoints());
        history.setCurrentExp(user.getExp());
        history.setNote("每日签到");
        pointsHistoryRepository.save(history);
        badgeService.checkUserBadges(user);
        return saved;
    }

    @Transactional(readOnly = true)
    public Page<DailyCheckIn> getCheckInHistory(String username, Pageable pageable) {
        User user = userService.getUserByUsername(username);
        return dailyCheckInRepository.findByUserOrderByCheckDateDesc(user, pageable);
    }

    @Transactional(readOnly = true)
    public Page<PointsHistory> getPointsHistory(String username, Pageable pageable) {
        User user = userService.getUserByUsername(username);
        return pointsHistoryRepository.findByUserOrderByCreatedAtDesc(user, pageable);
    }

    @Transactional(readOnly = true)
    public List<RewardItem> listActiveRewards() {
        return rewardItemRepository.findByStatusOrderByCostPointsAsc(1);
    }

    @Transactional(readOnly = true)
    public List<RewardItem> listAllRewardsForAdmin() {
        return rewardItemRepository.findAll(org.springframework.data.domain.Sort
                .by(org.springframework.data.domain.Sort.Direction.DESC, "status")
                .and(org.springframework.data.domain.Sort.by("costPoints")));
    }

    @Transactional
    public RewardItem createRewardItem(RewardItemManageRequest request) {
        RewardItem reward = new RewardItem();
        applyRewardRequest(reward, request);
        return rewardItemRepository.save(reward);
    }

    @Transactional
    public RewardItem updateRewardItem(Long id, RewardItemManageRequest request) {
        RewardItem reward = rewardItemRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("奖励不存在"));
        applyRewardRequest(reward, request);
        return rewardItemRepository.save(reward);
    }

    @Transactional
    public RewardItem updateRewardStatus(Long id, int status) {
        if (status != 0 && status != 1) {
            throw new ApiException(400, "奖励状态不合法");
        }
        RewardItem reward = rewardItemRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("奖励不存在"));
        reward.setStatus(status);
        return rewardItemRepository.save(reward);
    }

    private void applyRewardRequest(RewardItem reward, RewardItemManageRequest request) {
        String name = request.getName() == null ? "" : request.getName().trim();
        if (!StringUtils.hasText(name)) {
            throw new ApiException(400, "奖励名称不能为空");
        }
        reward.setName(name);
        reward.setDescription(StringUtils.hasText(request.getDescription()) ? request.getDescription().trim() : null);
        reward.setCostPoints(request.getCostPoints() == null ? 1 : request.getCostPoints());
        reward.setStock(request.getStock() == null ? 0 : request.getStock());
        int status = request.getStatus() == null ? reward.getStatus() : request.getStatus();
        if (status != 0 && status != 1) {
            throw new ApiException(400, "奖励状态不合法");
        }
        reward.setStatus(status);
    }

    @Transactional
    public RedemptionRequest redeem(Long rewardId, String username) {
        User user = userService.getUserByUsername(username);
        RewardItem reward = rewardItemRepository.findById(rewardId).orElseThrow(() -> new NotFoundException("奖励不存在"));
        if (reward.getStatus() != 1) {
            throw new ApiException(400, "奖励已下架");
        }
        int cost = reward.getCostPoints();
        Long userId = user.getId();
        String rewardName = reward.getName();

        // Atomic conditional decrements guard against oversell / negative points under
        // concurrent redemption. A 0 row-count means the guard failed; throwing rolls
        // back any earlier decrement in this transaction.
        if (rewardItemRepository.decrementStock(rewardId) == 0) {
            throw new ApiException(400, "库存不足");
        }
        if (userRepository.deductPoints(userId, cost) == 0) {
            throw new ApiException(400, "积分不足");
        }

        // Persistence context was cleared by the bulk updates; re-fetch fresh state.
        User freshUser = userRepository.findById(userId).orElseThrow(() -> new NotFoundException("用户不存在"));
        RewardItem freshReward = rewardItemRepository.findById(rewardId).orElseThrow(() -> new NotFoundException("奖励不存在"));

        RedemptionRequest request = new RedemptionRequest();
        request.setUser(freshUser);
        request.setReward(freshReward);
        request.setPointsCost(cost);
        request.setStatus(0);
        RedemptionRequest saved = redemptionRequestRepository.save(request);

        PointsHistory history = new PointsHistory();
        history.setUser(freshUser);
        history.setChangeType("REDEEM");
        history.setPointsDelta(-cost);
        history.setExpDelta(0);
        history.setCurrentPoints(freshUser.getPoints());
        history.setCurrentExp(freshUser.getExp());
        history.setNote("兑换奖励: " + rewardName);
        pointsHistoryRepository.save(history);
        return redemptionRequestRepository.findByIdWithAssociations(saved.getId())
                .orElse(saved);
    }

    @Transactional(readOnly = true)
    public Page<RedemptionRequest> myRedemptions(String username, Pageable pageable) {
        User user = userService.getUserByUsername(username);
        return redemptionRequestRepository.findByUserOrderByCreatedAtDesc(user, pageable);
    }

    @Transactional(readOnly = true)
    public Page<RedemptionRequest> pendingRedemptions(Pageable pageable) {
        return redemptionRequestRepository.findByStatusOrderByCreatedAtDesc(0, pageable);
    }

    @Transactional
    public RedemptionRequest reviewRedemption(Long requestId, boolean approve, String note) {
        RedemptionRequest request = redemptionRequestRepository.findById(requestId)
                .orElseThrow(() -> new NotFoundException("兑换申请不存在"));
        if (request.getStatus() != 0) {
            throw new ApiException(400, "申请已处理");
        }
        request.setStatus(approve ? 1 : 2);
        request.setReviewNote(note);
        RedemptionRequest saved = redemptionRequestRepository.save(request);

        if (!approve) {
            // Refund points and restock atomically when an申请 is rejected.
            Long userId = request.getUser().getId();
            int refund = request.getPointsCost();
            userRepository.addPoints(userId, refund);
            rewardItemRepository.incrementStock(request.getReward().getId());

            User freshUser = userRepository.findById(userId).orElseThrow(() -> new NotFoundException("用户不存在"));
            PointsHistory history = new PointsHistory();
            history.setUser(freshUser);
            history.setChangeType("REDEEM_REFUND");
            history.setPointsDelta(refund);
            history.setExpDelta(0);
            history.setCurrentPoints(freshUser.getPoints());
            history.setCurrentExp(freshUser.getExp());
            history.setNote("兑换被驳回，积分已退还");
            pointsHistoryRepository.save(history);
            notificationService.notify(freshUser, Notification.TYPE_REDEMPTION,
                    "兑换申请被驳回", "你的积分已退还，可重新选择心仪奖励。", null, "REWARD");
            // The bulk updates cleared the persistence context, detaching `saved`.
            // Re-fetch so lazy associations remain initializable during serialization.
            return redemptionRequestRepository.findByIdWithAssociations(requestId)
                    .orElseThrow(() -> new NotFoundException("兑换申请不存在"));
        }
        notificationService.notify(saved.getUser(), Notification.TYPE_REDEMPTION,
                "兑换申请已通过", "你的奖励正在发放，请留意后续通知。", null, "REWARD");
        return redemptionRequestRepository.findByIdWithAssociations(saved.getId())
                .orElse(saved);
    }

    /**
     * Derives the user's achievement badges from their existing stats — no separate badge
     * table to keep in sync. Each badge reports whether it is earned and its progress so the
     * UI can render an "almost there" state.
     */
    @Transactional(readOnly = true)
    public Map<String, Object> achievements(String username) {
        User user = userService.getUserByUsername(username);
        long postCount = postRepository.countByAuthor(user);
        long likesReceived = postRepository.sumLikesReceived(user);
        int level = user.getLevel() == null ? 1 : user.getLevel();
        int streak = user.getConsecutiveDays() == null ? 0 : user.getConsecutiveDays();
        int points = user.getPoints() == null ? 0 : user.getPoints();

        List<Map<String, Object>> badges = new ArrayList<>();
        badges.add(badge("first_post", "初来乍到", "发布第一篇帖子", "🌱", postCount, 1));
        badges.add(badge("prolific", "笔耕不辍", "累计发布 10 篇帖子", "✍️", postCount, 10));
        badges.add(badge("popular", "人气作者", "累计获得 50 个赞", "🔥", likesReceived, 50));
        badges.add(badge("streak_7", "坚持不懈", "连续签到 7 天", "📅", streak, 7));
        badges.add(badge("streak_30", "月度常客", "连续签到 30 天", "🏆", streak, 30));
        badges.add(badge("level_5", "等级达人", "成长等级达到 Lv.5", "⭐", level, 5));
        badges.add(badge("points_500", "积分新贵", "积累 500 积分", "💎", points, 500));

        long earned = badges.stream().filter(b -> Boolean.TRUE.equals(b.get("achieved"))).count();
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("earned", earned);
        result.put("total", badges.size());
        result.put("badges", badges);
        return result;
    }

    private Map<String, Object> badge(String id, String name, String description, String icon,
                                      long current, long target) {
        Map<String, Object> badge = new LinkedHashMap<>();
        badge.put("id", id);
        badge.put("name", name);
        badge.put("description", description);
        badge.put("icon", icon);
        badge.put("achieved", current >= target);
        badge.put("current", Math.min(current, target));
        badge.put("target", target);
        badge.put("progress", target == 0 ? 100 : (int) Math.min(100, Math.round(current * 100.0 / target)));
        return badge;
    }

    @Transactional(readOnly = true)
    public Map<String, Object> reportSummary() {
        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("users", userRepository.count());
        summary.put("posts", postRepository.count());
        summary.put("comments", commentRepository.count());
        summary.put("pendingPosts", postRepository.findByStatusOrderByCreatedAtDesc(0, Pageable.ofSize(1)).getTotalElements());
        summary.put("pendingRedemptions", redemptionRequestRepository.findByStatusOrderByCreatedAtDesc(0, Pageable.ofSize(1)).getTotalElements());
        return summary;
    }

    private RecommendationConfig loadRecommendationConfig() {
        return recommendationConfigRepository.findById(1L)
                .orElseGet(() -> {
                    RecommendationConfig config = new RecommendationConfig();
                    config.setId(1L);
                    return recommendationConfigRepository.save(config);
                });
    }

    private Page<Post> buildRecommendationPage(User user, Pageable pageable) {
        RecommendationConfig config = loadRecommendationConfig();
        int requiredSize = (int) pageable.getOffset() + pageable.getPageSize();
        int fetchSize = Math.max(requiredSize * 4, 40);
        Collection<Long> tagIds = user == null || user.getTags() == null
                ? List.of()
                : user.getTags().stream().map(Tag::getId).toList();
        List<Long> followingIds = user == null ? null : userFollowRepository.findFollowingIds(user);
        Set<Long> followedAuthorIds = followingIds == null ? Set.of() : new HashSet<>(followingIds);

        LinkedHashMap<Long, Post> candidateMap = new LinkedHashMap<>();
        collectCandidates(candidateMap, postRepository.findHotPosts(PageRequest.of(0, fetchSize)).getContent());
        collectCandidates(candidateMap, postRepository.findByStatusOrderByCreatedAtDesc(PostService.STATUS_PUBLISHED, PageRequest.of(0, fetchSize)).getContent());
        if (!tagIds.isEmpty()) {
            collectCandidates(candidateMap, postRepository.recommendByTagIds(tagIds, false, PageRequest.of(0, fetchSize)).getContent());
        }
        if (!followedAuthorIds.isEmpty()) {
            collectCandidates(candidateMap, postRepository.findPublishedByAuthorIds(followedAuthorIds, PageRequest.of(0, fetchSize)).getContent());
        }

        List<Post> candidates = new ArrayList<>(candidateMap.values());
        if (user != null) {
            Set<Long> ignoredPostIds = findIgnoredPostIds(user, candidates);
            candidates = candidates.stream()
                    .filter(post -> !ignoredPostIds.contains(post.getId()))
                    .toList();
        }

        Map<Long, Double> engagementScores = new HashMap<>();
        double maxEngagement = 0D;
        for (Post post : candidates) {
            double engagement = rawEngagement(post);
            engagementScores.put(post.getId(), engagement);
            maxEngagement = Math.max(maxEngagement, engagement);
        }
        double safeMaxEngagement = maxEngagement <= 0 ? 1D : maxEngagement;

        List<Post> ranked = new ArrayList<>(candidates);
        ranked.sort(Comparator
                .comparingDouble((Post post) -> scorePost(post, user, config, engagementScores.getOrDefault(post.getId(), 0D), safeMaxEngagement, followedAuthorIds))
                .reversed()
                .thenComparing(Post::getCreatedAt, Comparator.nullsLast(Comparator.reverseOrder())));

        ranked.forEach(post -> decorateRecommendation(post, user, config, engagementScores.getOrDefault(post.getId(), 0D), safeMaxEngagement, followedAuthorIds));

        int start = Math.min((int) pageable.getOffset(), ranked.size());
        int end = Math.min(start + pageable.getPageSize(), ranked.size());
        return new PageImpl<>(ranked.subList(start, end), pageable, ranked.size());
    }

    private void collectCandidates(Map<Long, Post> target, List<Post> posts) {
        for (Post post : posts) {
            if (post != null && post.getId() != null) {
                target.putIfAbsent(post.getId(), post);
            }
        }
    }

    private Set<Long> findIgnoredPostIds(User user, List<Post> candidates) {
        Set<Long> candidateIds = candidates.stream()
                .map(Post::getId)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());
        if (candidateIds.isEmpty()) {
            return Set.of();
        }
        return postDisinterestRepository.findPostIdsByUserAndPostIdIn(user, candidateIds);
    }

    private double scorePost(Post post, User user, RecommendationConfig config, double engagementRaw,
                             double maxEngagement, Set<Long> followedAuthorIds) {
        double tagScore = computeTagScore(post, user);
        double engagementScore = engagementRaw / maxEngagement;
        double recencyScore = computeRecencyScore(post.getCreatedAt());
        return config.getTagWeight() * tagScore
                + config.getEngagementWeight() * engagementScore
                + config.getRecencyWeight() * recencyScore
                + socialBonus(post, followedAuthorIds);
    }

    private double socialBonus(Post post, Set<Long> followedAuthorIds) {
        if (followedAuthorIds == null || followedAuthorIds.isEmpty()
                || post.getAuthor() == null || post.getAuthor().getId() == null) {
            return 0D;
        }
        return followedAuthorIds.contains(post.getAuthor().getId()) ? SOCIAL_BONUS : 0D;
    }

    private void decorateRecommendation(Post post, User user, RecommendationConfig config, double engagementRaw,
                                        double maxEngagement, Set<Long> followedAuthorIds) {
        double tagScore = computeTagScore(post, user);
        double engagementScore = engagementRaw / maxEngagement;
        double recencyScore = computeRecencyScore(post.getCreatedAt());
        double bonus = socialBonus(post, followedAuthorIds);
        double totalScore = config.getTagWeight() * tagScore
                + config.getEngagementWeight() * engagementScore
                + config.getRecencyWeight() * recencyScore
                + bonus;

        post.setRecommendationScore(Math.round(totalScore * 100D) / 100D);

        if (!Boolean.TRUE.equals(config.getExplainabilityEnabled())) {
            post.setRecommendationReasons(List.of());
            return;
        }

        List<String> reasons = new ArrayList<>();
        if (bonus > 0) {
            reasons.add("来自你关注的用户");
        }
        if (tagScore > 0.4D) {
            reasons.add("匹配你的兴趣标签");
        }
        if (engagementScore > 0.45D) {
            reasons.add("近期互动热度较高");
        }
        if (recencyScore > 0.6D) {
            reasons.add("发布时间较新");
        }
        if (reasons.isEmpty()) {
            reasons.add("综合推荐结果");
        }
        post.setRecommendationReasons(reasons);
    }

    private double computeTagScore(Post post, User user) {
        if (user == null || user.getTags() == null || user.getTags().isEmpty() || post.getTags() == null || post.getTags().isEmpty()) {
            return 0D;
        }

        Set<Long> userTagIds = user.getTags().stream()
                .map(Tag::getId)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());
        long matched = post.getTags().stream().map(Tag::getId).filter(userTagIds::contains).count();
        return matched == 0 ? 0D : (double) matched / post.getTags().size();
    }

    private double rawEngagement(Post post) {
        int heat = Optional.ofNullable(post.getHeatScore()).orElse(0);
        int likes = Optional.ofNullable(post.getLikeCount()).orElse(0);
        int comments = Optional.ofNullable(post.getCommentCount()).orElse(0);
        int collects = Optional.ofNullable(post.getCollectCount()).orElse(0);
        int views = Optional.ofNullable(post.getViewCount()).orElse(0);
        return heat + likes * 2D + comments * 3D + collects * 2D + views * 0.2D;
    }

    private double computeRecencyScore(LocalDateTime createdAt) {
        if (createdAt == null) {
            return 0D;
        }
        long hours = Math.max(0L, Duration.between(createdAt, LocalDateTime.now()).toHours());
        double decayWindowHours = 24D * 14D;
        return Math.max(0D, 1D - (hours / decayWindowHours));
    }
}
