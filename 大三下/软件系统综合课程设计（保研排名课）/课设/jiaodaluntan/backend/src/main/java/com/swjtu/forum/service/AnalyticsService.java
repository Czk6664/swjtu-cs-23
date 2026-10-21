package com.swjtu.forum.service;

import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.entity.Tag;
import com.swjtu.forum.repository.CommentRepository;
import com.swjtu.forum.repository.PostFavoriteRepository;
import com.swjtu.forum.repository.PostLikeRepository;
import com.swjtu.forum.repository.PostRepository;
import com.swjtu.forum.repository.RedemptionRequestRepository;
import com.swjtu.forum.repository.ReportRepository;
import com.swjtu.forum.repository.SectionRepository;
import com.swjtu.forum.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;

/**
 * Operational analytics for the admin data dashboard: KPI totals, a 7-day activity
 * trend, per-section distribution, trending tags ("舆情监测" signal), and hot content.
 * All figures are derived from existing tables, so the dashboard stays consistent
 * with the live data without a separate analytics pipeline.
 */
@Service
@RequiredArgsConstructor
public class AnalyticsService {

    private static final int DEFAULT_TREND_DAYS = 7;
    private static final int MAX_TREND_DAYS = 30;
    private static final int TRENDING_TAG_WINDOW_DAYS = 14;
    private static final int TRENDING_TAG_LIMIT = 10;
    private static final int HOT_POST_LIMIT = 5;

    private final UserRepository userRepository;
    private final PostRepository postRepository;
    private final CommentRepository commentRepository;
    private final PostLikeRepository postLikeRepository;
    private final PostFavoriteRepository postFavoriteRepository;
    private final SectionRepository sectionRepository;
    private final ReportRepository reportRepository;
    private final RedemptionRequestRepository redemptionRequestRepository;

    @Transactional(readOnly = true)
    public Map<String, Object> dashboard() {
        return dashboard(DEFAULT_TREND_DAYS);
    }

    @Transactional(readOnly = true)
    public Map<String, Object> dashboard(int days) {
        int rangeDays = normalizeDays(days);
        LocalDateTime rangeStart = LocalDateTime.now().minusDays(rangeDays);
        Map<String, Object> active = activeUsers();
        Map<String, Object> interactions = interactionStats(rangeStart, rangeDays);

        Map<String, Object> totals = new LinkedHashMap<>();
        totals.put("users", userRepository.count());
        totals.put("bannedUsers", userRepository.countByEnabledFalse());
        totals.put("newUsers7d", userRepository.countByCreatedAtAfter(LocalDateTime.now().minusDays(DEFAULT_TREND_DAYS)));
        totals.put("newUsersInRange", userRepository.countByCreatedAtAfter(rangeStart));
        totals.put("posts", postRepository.count());
        totals.put("publishedPosts", postRepository.countByStatus(PostService.STATUS_PUBLISHED));
        totals.put("pendingPosts", postRepository.countByStatus(PostService.STATUS_PENDING));
        totals.put("hiddenPosts", postRepository.countByStatus(PostService.STATUS_HIDDEN));
        totals.put("newPosts7d", postRepository.countByCreatedAtAfter(LocalDateTime.now().minusDays(DEFAULT_TREND_DAYS)));
        totals.put("newPostsInRange", postRepository.countByCreatedAtAfter(rangeStart));
        totals.put("comments", commentRepository.count());
        totals.put("newCommentsInRange", interactions.get("newCommentsInRange"));
        totals.put("likes", interactions.get("likes"));
        totals.put("newLikesInRange", interactions.get("newLikesInRange"));
        totals.put("favorites", interactions.get("favorites"));
        totals.put("newFavoritesInRange", interactions.get("newFavoritesInRange"));
        totals.put("dailyActiveUsers", active.get("daily"));
        totals.put("weeklyActiveUsers", active.get("weekly"));
        totals.put("monthlyActiveUsers", active.get("monthly"));
        totals.put("pendingReports", pendingCount(reportRepository));
        totals.put("pendingRedemptions", pendingRedemptions());

        Map<String, Object> dashboard = new LinkedHashMap<>();
        dashboard.put("rangeDays", rangeDays);
        dashboard.put("totals", totals);
        dashboard.put("postTrend", postTrend(rangeDays));
        dashboard.put("activityTrend", activityTrend(rangeDays));
        dashboard.put("activeUsers", active);
        dashboard.put("interactionStats", interactions);
        dashboard.put("sectionDistribution", sectionDistribution());
        dashboard.put("trendingTags", trendingTags());
        dashboard.put("hotPosts", hotPosts());
        dashboard.put("report", operationalReport(totals));
        return dashboard;
    }

    /** Daily new-post counts for the selected range (oldest first), for a line/bar chart. */
    private int normalizeDays(int days) {
        if (days <= 0) {
            return DEFAULT_TREND_DAYS;
        }
        return Math.min(days, MAX_TREND_DAYS);
    }

    private List<Map<String, Object>> postTrend(int days) {
        List<Map<String, Object>> trend = new ArrayList<>();
        LocalDate today = LocalDate.now();
        for (int i = days - 1; i >= 0; i--) {
            LocalDate day = today.minusDays(i);
            LocalDateTime start = day.atStartOfDay();
            LocalDateTime end = day.plusDays(1).atStartOfDay();
            Map<String, Object> point = new LinkedHashMap<>();
            point.put("date", day.toString());
            point.put("posts", postRepository.countByCreatedAtBetween(start, end));
            trend.add(point);
        }
        return trend;
    }

    private List<Map<String, Object>> activityTrend(int days) {
        List<Map<String, Object>> trend = new ArrayList<>();
        LocalDate today = LocalDate.now();
        for (int i = days - 1; i >= 0; i--) {
            LocalDate day = today.minusDays(i);
            LocalDateTime start = day.atStartOfDay();
            LocalDateTime end = day.plusDays(1).atStartOfDay();
            Map<String, Object> point = new LinkedHashMap<>();
            point.put("date", day.toString());
            point.put("posts", postRepository.countByCreatedAtBetween(start, end));
            point.put("comments", commentRepository.countByCreatedAtBetween(start, end));
            point.put("activeUsers", activeUserCount(start, end));
            trend.add(point);
        }
        return trend;
    }

    private Map<String, Object> activeUsers() {
        LocalDateTime now = LocalDateTime.now();
        Map<String, Object> active = new LinkedHashMap<>();
        active.put("daily", activeUserCount(now.minusDays(1), now));
        active.put("weekly", activeUserCount(now.minusDays(7), now));
        active.put("monthly", activeUserCount(now.minusDays(30), now));
        return active;
    }

    private Map<String, Object> interactionStats(LocalDateTime rangeStart, int rangeDays) {
        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("rangeDays", rangeDays);
        stats.put("comments", commentRepository.count());
        stats.put("newComments7d", commentRepository.countByCreatedAtAfter(LocalDateTime.now().minusDays(DEFAULT_TREND_DAYS)));
        stats.put("newCommentsInRange", commentRepository.countByCreatedAtAfter(rangeStart));
        stats.put("likes", postLikeRepository.count());
        stats.put("newLikes7d", postLikeRepository.countByCreatedAtAfter(LocalDateTime.now().minusDays(DEFAULT_TREND_DAYS)));
        stats.put("newLikesInRange", postLikeRepository.countByCreatedAtAfter(rangeStart));
        stats.put("favorites", postFavoriteRepository.count());
        stats.put("newFavorites7d", postFavoriteRepository.countByCreatedAtAfter(LocalDateTime.now().minusDays(DEFAULT_TREND_DAYS)));
        stats.put("newFavoritesInRange", postFavoriteRepository.countByCreatedAtAfter(rangeStart));
        return stats;
    }

    private Map<String, Object> operationalReport(Map<String, Object> totals) {
        Map<String, Object> report = new LinkedHashMap<>();
        report.put("generatedAt", LocalDateTime.now());
        report.put("title", "西南交大论坛运营报告");
        report.put("summary", "本报告汇总用户、内容、互动、热帖和舆情标签，用于课程设计验收和后台运营展示。");
        report.put("riskLevel", ((Number) totals.get("pendingReports")).longValue() > 0 ? "需关注" : "正常");
        return report;
    }

    public Map<String, Object> dashboardReport() {
        return dashboard();
    }

    private List<Map<String, Object>> sectionDistribution() {
        List<Map<String, Object>> distribution = new ArrayList<>();
        List<Section> sections = sectionRepository.findAllByOrderBySortOrderAsc();
        for (Section section : sections) {
            Map<String, Object> entry = new LinkedHashMap<>();
            entry.put("section", section.getName());
            entry.put("posts", postRepository.countBySectionAndStatus(section, PostService.STATUS_PUBLISHED));
            distribution.add(entry);
        }
        distribution.sort(Comparator
                .comparingLong((Map<String, Object> m) -> ((Number) m.get("posts")).longValue())
                .reversed());
        return distribution;
    }

    private int activeUserCount(LocalDateTime start, LocalDateTime end) {
        Set<Long> userIds = new HashSet<>(postRepository.findDistinctAuthorIdsByCreatedAtBetween(start, end));
        userIds.addAll(commentRepository.findDistinctAuthorIdsByCreatedAtBetween(start, end));
        return userIds.size();
    }

    /** Tally tag usage across recently published posts — a lightweight trending/opinion signal. */
    @Transactional(readOnly = true)
    public List<Map<String, Object>> trendingTags() {
        LocalDateTime windowStart = LocalDateTime.now().minusDays(TRENDING_TAG_WINDOW_DAYS);
        List<Post> recent = postRepository.findByStatusAndCreatedAtAfter(PostService.STATUS_PUBLISHED, windowStart);
        Map<String, Integer> counts = new HashMap<>();
        for (Post post : recent) {
            if (post.getTags() == null) {
                continue;
            }
            for (Tag tag : post.getTags()) {
                counts.merge(tag.getName(), 1, Integer::sum);
            }
        }
        return counts.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .limit(TRENDING_TAG_LIMIT)
                .map(e -> {
                    Map<String, Object> entry = new LinkedHashMap<>();
                    entry.put("tag", e.getKey());
                    entry.put("count", e.getValue());
                    return entry;
                })
                .toList();
    }

    @Transactional(readOnly = true)
    public List<Map<String, Object>> hotPosts() {
        return postRepository.findHotPosts(PageRequest.of(0, HOT_POST_LIMIT)).getContent().stream()
                .map(this::postSummary)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<Map<String, Object>> hotPostsToday() {
        LocalDateTime todayStart = LocalDate.now().atStartOfDay();
        return postRepository.findByStatusAndCreatedAtAfter(PostService.STATUS_PUBLISHED, todayStart).stream()
                .sorted(Comparator
                        .comparingInt((Post post) -> safe(post.getHeatScore())).reversed()
                        .thenComparing((Post post) -> safe(post.getLikeCount()), Comparator.reverseOrder())
                        .thenComparing(Post::getCreatedAt, Comparator.nullsLast(Comparator.reverseOrder())))
                .limit(HOT_POST_LIMIT)
                .map(this::postSummary)
                .toList();
    }

    private Map<String, Object> postSummary(Post post) {
        Map<String, Object> entry = new LinkedHashMap<>();
        entry.put("id", post.getId());
        entry.put("title", post.getTitle());
        entry.put("heatScore", safe(post.getHeatScore()));
        entry.put("likeCount", safe(post.getLikeCount()));
        entry.put("commentCount", safe(post.getCommentCount()));
        entry.put("viewCount", safe(post.getViewCount()));
        entry.put("acceptedCommentId", post.getAcceptedCommentId());
        entry.put("createdAt", post.getCreatedAt());
        entry.put("section", post.getSection() == null ? null : post.getSection().getName());
        entry.put("author", post.getAuthor() == null ? null : post.getAuthor().getUsername());
        return entry;
    }

    private int safe(Integer value) {
        return value == null ? 0 : value;
    }

    private long pendingCount(ReportRepository repository) {
        return repository.findByStatusOrderByCreatedAtDesc(0, Pageable.ofSize(1)).getTotalElements();
    }

    private long pendingRedemptions() {
        return redemptionRequestRepository.findByStatusOrderByCreatedAtDesc(0, Pageable.ofSize(1)).getTotalElements();
    }
}
