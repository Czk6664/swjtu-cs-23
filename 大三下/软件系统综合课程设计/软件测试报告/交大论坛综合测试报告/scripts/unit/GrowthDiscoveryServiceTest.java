package com.swjtu.forum.service;

import com.swjtu.forum.dto.RecommendationConfigRequest;
import com.swjtu.forum.entity.DailyCheckIn;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.PointsHistory;
import com.swjtu.forum.entity.RecommendationConfig;
import com.swjtu.forum.entity.RedemptionRequest;
import com.swjtu.forum.entity.RewardItem;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.entity.Tag;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.exception.ApiException;
import com.swjtu.forum.repository.CommentRepository;
import com.swjtu.forum.repository.DailyCheckInRepository;
import com.swjtu.forum.repository.PointsHistoryRepository;
import com.swjtu.forum.repository.PostDisinterestRepository;
import com.swjtu.forum.repository.PostRepository;
import com.swjtu.forum.repository.RecommendationConfigRepository;
import com.swjtu.forum.repository.RedemptionRequestRepository;
import com.swjtu.forum.repository.RewardItemRepository;
import com.swjtu.forum.repository.TagRepository;
import com.swjtu.forum.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.dao.DataIntegrityViolationException;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class GrowthDiscoveryServiceTest {

    @Mock
    private PostRepository postRepository;
    @Mock
    private PostDisinterestRepository postDisinterestRepository;
    @Mock
    private DailyCheckInRepository dailyCheckInRepository;
    @Mock
    private PointsHistoryRepository pointsHistoryRepository;
    @Mock
    private RewardItemRepository rewardItemRepository;
    @Mock
    private RedemptionRequestRepository redemptionRequestRepository;
    @Mock
    private TagRepository tagRepository;
    @Mock
    private UserRepository userRepository;
    @Mock
    private CommentRepository commentRepository;
    @Mock
    private RecommendationConfigRepository recommendationConfigRepository;
    @Mock
    private NotificationService notificationService;
    @Mock
    private com.swjtu.forum.repository.UserFollowRepository userFollowRepository;
    @Mock
    private BadgeService badgeService;

    private GrowthDiscoveryService growthDiscoveryService;
    private StubUserService userService;
    private User user;
    private Tag javaTag;

    @BeforeEach
    void setUp() {
        userService = new StubUserService();
        growthDiscoveryService = new GrowthDiscoveryService(
                userService,
                postRepository,
                postDisinterestRepository,
                dailyCheckInRepository,
                pointsHistoryRepository,
                rewardItemRepository,
                redemptionRequestRepository,
                tagRepository,
                userRepository,
                commentRepository,
                recommendationConfigRepository,
                notificationService,
                userFollowRepository,
                badgeService
        );

        javaTag = new Tag();
        javaTag.setId(1L);
        javaTag.setName("Java");

        user = new User();
        user.setId(10L);
        user.setUsername("alice");
        user.setTags(Set.of(javaTag));
        userService.setUser(user);
    }

    @Test
    void recommendPostsAddsExplainabilityReasonsFromWeightedSignals() {
        RecommendationConfig config = new RecommendationConfig();
        config.setId(1L);
        config.setTagWeight(60);
        config.setEngagementWeight(25);
        config.setRecencyWeight(15);
        config.setExplainabilityEnabled(true);

        when(recommendationConfigRepository.findById(1L)).thenReturn(java.util.Optional.of(config));

        Post matched = buildPost(1L, "Java 帖子", 20, 5, 3, 1, 100, LocalDateTime.now().minusHours(3), Set.of(javaTag));
        Post fresh = buildPost(2L, "新帖子", 2, 0, 0, 0, 10, LocalDateTime.now().minusHours(1), Set.of());

        when(postRepository.findHotPosts(any(PageRequest.class))).thenReturn(new PageImpl<>(List.of(matched, fresh)));
        when(postRepository.findByStatusOrderByCreatedAtDesc(any(Integer.class), any(PageRequest.class))).thenReturn(new PageImpl<>(List.of(fresh, matched)));
        when(postRepository.recommendByTagIds(any(), any(Boolean.class), any(PageRequest.class))).thenReturn(new PageImpl<>(List.of(matched)));
        when(postDisinterestRepository.findPostIdsByUserAndPostIdIn(eq(user), any())).thenReturn(Set.of());

        List<Post> result = growthDiscoveryService.recommendPosts("alice", PageRequest.of(0, 10)).getContent();

        assertThat(result).isNotEmpty();
        assertThat(result.get(0).getTitle()).isEqualTo("Java 帖子");
        assertThat(result.get(0).getRecommendationReasons()).contains("匹配你的兴趣标签", "近期互动热度较高");
        assertThat(result.get(0).getRecommendationScore()).isNotNull();
        verify(postDisinterestRepository, never()).existsByUserAndPost(any(User.class), any(Post.class));
    }

    @Test
    void recommendPostsFiltersIgnoredPostsWithOneBatchLookup() {
        RecommendationConfig config = new RecommendationConfig();
        config.setId(1L);
        config.setTagWeight(60);
        config.setEngagementWeight(25);
        config.setRecencyWeight(15);
        config.setExplainabilityEnabled(false);

        when(recommendationConfigRepository.findById(1L)).thenReturn(java.util.Optional.of(config));

        Post matched = buildPost(1L, "Java 帖子", 20, 5, 3, 1, 100, LocalDateTime.now().minusHours(3), Set.of(javaTag));
        Post ignored = buildPost(2L, "不感兴趣帖子", 30, 5, 3, 1, 100, LocalDateTime.now().minusHours(1), Set.of(javaTag));

        when(postRepository.findHotPosts(any(PageRequest.class))).thenReturn(new PageImpl<>(List.of(matched, ignored)));
        when(postRepository.findByStatusOrderByCreatedAtDesc(any(Integer.class), any(PageRequest.class))).thenReturn(new PageImpl<>(List.of(ignored, matched)));
        when(postRepository.recommendByTagIds(any(), any(Boolean.class), any(PageRequest.class))).thenReturn(new PageImpl<>(List.of(matched, ignored)));
        when(postDisinterestRepository.findPostIdsByUserAndPostIdIn(eq(user), any())).thenReturn(Set.of(ignored.getId()));

        List<Post> result = growthDiscoveryService.recommendPosts("alice", PageRequest.of(0, 10)).getContent();

        assertThat(result).extracting(Post::getId).containsExactly(matched.getId());
        verify(postDisinterestRepository, never()).existsByUserAndPost(any(User.class), any(Post.class));
    }

    @Test
    void updateRecommendationConfigRejectsWeightsNotSummingToHundred() {
        RecommendationConfigRequest request = new RecommendationConfigRequest();
        request.setTagWeight(40);
        request.setEngagementWeight(40);
        request.setRecencyWeight(10);
        request.setExplainabilityEnabled(true);

        assertThatThrownBy(() -> growthDiscoveryService.updateRecommendationConfig(request))
                .isInstanceOf(ApiException.class)
                .hasMessage("推荐因子权重总和必须为 100");

        verify(recommendationConfigRepository, never()).save(any(RecommendationConfig.class));
    }

    @Test
    void searchPostsTreatsHostileKeywordAsBoundQueryData() {
        String hostileKeyword = "' OR 1=1 -- <script>alert(1)</script>";
        PageRequest pageable = PageRequest.of(0, 20);

        when(postRepository.searchPublishedExtended(eq(PostService.STATUS_PUBLISHED), eq(hostileKeyword), eq(pageable)))
                .thenReturn(new PageImpl<>(List.of(), pageable, 0));

        assertThat(growthDiscoveryService.searchPosts("  " + hostileKeyword + "  ", pageable).getContent()).isEmpty();

        verify(postRepository).searchPublishedExtended(PostService.STATUS_PUBLISHED, hostileKeyword, pageable);
    }

    @Test
    void checkInRejectsWhenTodayRecordAlreadyExists() {
        LocalDate today = LocalDate.now();
        DailyCheckIn existing = new DailyCheckIn();
        existing.setUser(user);
        existing.setCheckDate(today);

        when(dailyCheckInRepository.findByUserAndCheckDate(user, today)).thenReturn(Optional.of(existing));

        assertThatThrownBy(() -> growthDiscoveryService.checkIn("alice"))
                .isInstanceOf(ApiException.class)
                .hasMessage("今日已签到");

        verify(dailyCheckInRepository, never()).saveAndFlush(any(DailyCheckIn.class));
    }

    @Test
    void checkInTranslatesUniqueConstraintRaceToDuplicateMessage() {
        LocalDate today = LocalDate.now();
        when(dailyCheckInRepository.findByUserAndCheckDate(user, today)).thenReturn(Optional.empty());
        when(dailyCheckInRepository.saveAndFlush(any(DailyCheckIn.class)))
                .thenThrow(new DataIntegrityViolationException("duplicate check-in"));

        assertThatThrownBy(() -> growthDiscoveryService.checkIn("alice"))
                .isInstanceOf(ApiException.class)
                .hasMessage("今日已签到");

        verify(userRepository, never()).save(any(User.class));
        verify(pointsHistoryRepository, never()).save(any(PointsHistory.class));
    }

    @Test
    void checkInAwardsPointsAndResetsConsecutiveDaysWithoutYesterday() {
        LocalDate today = LocalDate.now();
        DailyCheckIn savedRecord = new DailyCheckIn();
        savedRecord.setUser(user);
        savedRecord.setCheckDate(today);
        user.setPoints(7);
        user.setExp(3);
        user.setConsecutiveDays(4);

        when(dailyCheckInRepository.findByUserAndCheckDate(user, today)).thenReturn(Optional.empty());
        when(dailyCheckInRepository.saveAndFlush(any(DailyCheckIn.class))).thenReturn(savedRecord);
        when(dailyCheckInRepository.findByUserAndCheckDate(user, today.minusDays(1))).thenReturn(Optional.empty());

        DailyCheckIn result = growthDiscoveryService.checkIn("alice");

        assertThat(result).isEqualTo(savedRecord);
        assertThat(user.getPoints()).isEqualTo(17);
        assertThat(user.getExp()).isEqualTo(8);
        assertThat(user.getConsecutiveDays()).isEqualTo(1);
        verify(userRepository).save(user);
        verify(badgeService).checkUserBadges(user);

        ArgumentCaptor<PointsHistory> historyCaptor = ArgumentCaptor.forClass(PointsHistory.class);
        verify(pointsHistoryRepository).save(historyCaptor.capture());
        assertThat(historyCaptor.getValue().getChangeType()).isEqualTo("CHECK_IN");
        assertThat(historyCaptor.getValue().getPointsDelta()).isEqualTo(10);
        assertThat(historyCaptor.getValue().getExpDelta()).isEqualTo(5);
    }

    @Test
    void checkInIncrementsConsecutiveDaysWhenYesterdayExists() {
        LocalDate today = LocalDate.now();
        DailyCheckIn savedRecord = new DailyCheckIn();
        DailyCheckIn yesterday = new DailyCheckIn();
        user.setConsecutiveDays(2);

        when(dailyCheckInRepository.findByUserAndCheckDate(user, today)).thenReturn(Optional.empty());
        when(dailyCheckInRepository.saveAndFlush(any(DailyCheckIn.class))).thenReturn(savedRecord);
        when(dailyCheckInRepository.findByUserAndCheckDate(user, today.minusDays(1))).thenReturn(Optional.of(yesterday));

        growthDiscoveryService.checkIn("alice");

        assertThat(user.getConsecutiveDays()).isEqualTo(3);
    }

    @Test
    void redeemRejectsWhenStockDepleted() {
        RewardItem reward = reward(5L, "限量周边", 100);
        when(rewardItemRepository.findById(5L)).thenReturn(java.util.Optional.of(reward));
        when(rewardItemRepository.decrementStock(5L)).thenReturn(0);

        assertThatThrownBy(() -> growthDiscoveryService.redeem(5L, "alice"))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("库存不足");

        verify(userRepository, never()).deductPoints(any(), org.mockito.ArgumentMatchers.anyInt());
    }

    @Test
    void redeemRejectsWhenPointsInsufficient() {
        RewardItem reward = reward(5L, "限量周边", 100);
        when(rewardItemRepository.findById(5L)).thenReturn(java.util.Optional.of(reward));
        when(rewardItemRepository.decrementStock(5L)).thenReturn(1);
        when(userRepository.deductPoints(10L, 100)).thenReturn(0);

        assertThatThrownBy(() -> growthDiscoveryService.redeem(5L, "alice"))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("积分不足");
    }

    @Test
    void redeemDeductsPointsAtomicallyAndRecordsHistory() {
        RewardItem reward = reward(5L, "限量周边", 100);
        when(rewardItemRepository.findById(5L)).thenReturn(java.util.Optional.of(reward));
        when(rewardItemRepository.decrementStock(5L)).thenReturn(1);
        when(userRepository.deductPoints(10L, 100)).thenReturn(1);

        User fresh = new User();
        fresh.setId(10L);
        fresh.setUsername("alice");
        fresh.setPoints(50);
        fresh.setExp(20);
        when(userRepository.findById(10L)).thenReturn(java.util.Optional.of(fresh));
        when(redemptionRequestRepository.save(any(RedemptionRequest.class))).thenAnswer(i -> i.getArgument(0));

        RedemptionRequest saved = growthDiscoveryService.redeem(5L, "alice");

        assertThat(saved.getStatus()).isEqualTo(0);
        assertThat(saved.getPointsCost()).isEqualTo(100);
        verify(rewardItemRepository).decrementStock(5L);
        verify(userRepository).deductPoints(10L, 100);
        verify(pointsHistoryRepository).save(any());
    }

    private RewardItem reward(Long id, String name, int cost) {
        RewardItem reward = new RewardItem();
        reward.setId(id);
        reward.setName(name);
        reward.setCostPoints(cost);
        reward.setStatus(1);
        reward.setStock(3);
        return reward;
    }

    private Post buildPost(Long id, String title, int heat, int likes, int comments, int collects, int views, LocalDateTime createdAt, Set<Tag> tags) {
        Post post = new Post();
        post.setId(id);
        post.setTitle(title);
        post.setHeatScore(heat);
        post.setLikeCount(likes);
        post.setCommentCount(comments);
        post.setCollectCount(collects);
        post.setViewCount(views);
        post.setCreatedAt(createdAt);
        post.setTags(tags);

        Section section = new Section();
        section.setId(20L);
        section.setName("课程讨论");
        post.setSection(section);

        User author = new User();
        author.setId(30L);
        author.setUsername("author");
        post.setAuthor(author);
        return post;
    }

    private static class StubUserService extends UserService {
        private User user;

        StubUserService() {
            super(null, null, null, null, null, null);
        }

        void setUser(User user) {
            this.user = user;
        }

        @Override
        public User getUserByUsername(String username) {
            return user;
        }
    }
}
