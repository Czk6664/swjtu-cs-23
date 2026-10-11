package com.swjtu.forum.service;

import com.swjtu.forum.entity.Badge;
import com.swjtu.forum.entity.DailyCheckIn;
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
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class DemoSeedServiceTest {

    @Mock
    private UserRepository userRepository;
    @Mock
    private SectionRepository sectionRepository;
    @Mock
    private TagRepository tagRepository;
    @Mock
    private PostRepository postRepository;
    @Mock
    private CommentRepository commentRepository;
    @Mock
    private PostLikeRepository postLikeRepository;
    @Mock
    private PostFavoriteRepository postFavoriteRepository;
    @Mock
    private PostBrowseHistoryRepository postBrowseHistoryRepository;
    @Mock
    private PointsHistoryRepository pointsHistoryRepository;
    @Mock
    private RewardItemRepository rewardItemRepository;
    @Mock
    private RedemptionRequestRepository redemptionRequestRepository;
    @Mock
    private OperationLogRepository operationLogRepository;
    @Mock
    private DailyCheckInRepository dailyCheckInRepository;
    @Mock
    private BadgeRepository badgeRepository;
    @Mock
    private UserBadgeRepository userBadgeRepository;
    @Mock
    private BadgeService badgeService;
    @Mock
    private PasswordEncoder passwordEncoder;

    @InjectMocks
    private DemoSeedService demoSeedService;

    @BeforeEach
    void setUp() {
        lenient().when(passwordEncoder.encode("demo-password")).thenReturn("ENCODED");
        lenient().when(userRepository.findByUsername(any())).thenReturn(Optional.empty());
        lenient().when(sectionRepository.findByName(any())).thenAnswer(invocation -> {
            String name = invocation.getArgument(0);
            Section section = new Section();
            section.setId((long) name.hashCode());
            section.setName(name);
            section.setPostCount(0);
            return Optional.of(section);
        });
        lenient().when(tagRepository.findByName(any())).thenAnswer(invocation -> {
            String name = invocation.getArgument(0);
            Tag tag = new Tag();
            tag.setId((long) name.hashCode());
            tag.setName(name);
            return Optional.of(tag);
        });
        lenient().when(postRepository.findByTitle(any())).thenReturn(Optional.empty());
        lenient().when(userRepository.save(any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));
        lenient().when(postRepository.save(any(Post.class))).thenAnswer(invocation -> invocation.getArgument(0));
        lenient().when(rewardItemRepository.save(any(RewardItem.class))).thenAnswer(invocation -> invocation.getArgument(0));
        lenient().when(badgeRepository.findByCode(any())).thenAnswer(invocation -> {
            String code = invocation.getArgument(0);
            Badge badge = new Badge();
            badge.setCode(code);
            badge.setName(code);
            return Optional.of(badge);
        });
        lenient().when(userBadgeRepository.findByUserAndBadge(any(User.class), any(Badge.class))).thenReturn(Optional.empty());
        lenient().when(userBadgeRepository.save(any(UserBadge.class))).thenAnswer(invocation -> invocation.getArgument(0));
    }

    @Test
    void seedCoreDemoDataCreatesStableAnchorsOnlyOnce() {
        when(userRepository.findByUsername("demo_guest_anchor")).thenReturn(Optional.empty());
        when(userRepository.findByUsername("demo_student_anchor")).thenReturn(Optional.empty());
        when(userRepository.findByUsername("demo_admin_anchor")).thenReturn(Optional.empty());
        when(postRepository.findByTitle("【演示】校园热帖：春季社团市集逛展指南")).thenReturn(Optional.empty());
        when(rewardItemRepository.findByName("【演示】校园咖啡兑换券")).thenReturn(Optional.empty());

        demoSeedService.seedCoreDemoData();

        verify(userRepository, times(3)).save(any(User.class));
        verify(postRepository).save(any(Post.class));
        verify(rewardItemRepository).save(any(RewardItem.class));
    }

    @Test
    void seedCoreDemoDataUpdatesExistingAnchorsInsteadOfDuplicating() {
        User student = new User();
        student.setUsername("demo_student_anchor");
        student.setRole("USER");
        student.setPoints(0);
        student.setExp(0);

        Post post = new Post();
        post.setTitle("【演示】校园热帖：春季社团市集逛展指南");

        RewardItem reward = new RewardItem();
        reward.setName("【演示】校园咖啡兑换券");

        when(userRepository.findByUsername("demo_guest_anchor")).thenReturn(Optional.of(new User()));
        when(userRepository.findByUsername("demo_student_anchor")).thenReturn(Optional.of(student));
        when(userRepository.findByUsername("demo_admin_anchor")).thenReturn(Optional.of(new User()));
        when(postRepository.findByTitle("【演示】校园热帖：春季社团市集逛展指南")).thenReturn(Optional.of(post));
        when(rewardItemRepository.findByName("【演示】校园咖啡兑换券")).thenReturn(Optional.of(reward));

        demoSeedService.seedCoreDemoData();

        verify(userRepository, never()).save(any(User.class));
        verify(postRepository, never()).save(any(Post.class));
        verify(rewardItemRepository, never()).save(any(RewardItem.class));
        assertThat(student.getRole()).isEqualTo("USER");
    }

    @Test
    void seedCreatesCrossPageScenarioArtifacts() {
        User student = new User();
        student.setUsername("demo_student_anchor");
        student.setRole("USER");
        student.setPoints(260);
        student.setExp(180);

        User admin = new User();
        admin.setUsername("demo_admin_anchor");
        admin.setRole("ADMIN");

        when(userRepository.findByUsername("demo_guest_anchor")).thenReturn(Optional.of(new User()));
        when(userRepository.findByUsername("demo_student_anchor")).thenReturn(Optional.of(student));
        when(userRepository.findByUsername("demo_admin_anchor")).thenReturn(Optional.of(admin));
        when(postRepository.findByTitle("【演示】校园热帖：春季社团市集逛展指南")).thenReturn(Optional.of(existingPost("【演示】校园热帖：春季社团市集逛展指南")));
        when(postRepository.findByTitle("【演示】成长中心：四月签到打卡交流帖")).thenReturn(Optional.empty());
        when(postRepository.findByTitle("【演示】待审核：宿舍二手交易注意事项合集")).thenReturn(Optional.empty());
        when(postRepository.findByTitle("【演示】后台复盘：本周内容治理值班记录")).thenReturn(Optional.empty());
        when(rewardItemRepository.findByName("【演示】校园咖啡兑换券")).thenReturn(Optional.of(existingReward("【演示】校园咖啡兑换券")));
        when(rewardItemRepository.findByName("【演示】图书馆自习室优先券")).thenReturn(Optional.empty());
        when(commentRepository.findByPostAndAuthorAndContent(any(Post.class), any(User.class), any())).thenReturn(Optional.empty());
        when(postFavoriteRepository.findByUserAndPost(any(User.class), any(Post.class))).thenReturn(Optional.empty());
        when(postBrowseHistoryRepository.findByUserAndPost(any(User.class), any(Post.class))).thenReturn(Optional.empty());
        when(pointsHistoryRepository.findByUserAndChangeTypeAndNote(any(User.class), any(), any())).thenReturn(Optional.empty());
        when(redemptionRequestRepository.findByUserAndRewardAndStatus(any(User.class), any(RewardItem.class), any())).thenReturn(Optional.empty());
        when(operationLogRepository.findByActionAndTargetTypeAndTargetId(any(), any(), any())).thenReturn(Optional.empty());

        demoSeedService.seed();

        verify(postFavoriteRepository).deleteByUser(student);
        verify(postBrowseHistoryRepository).deleteByUser(student);
        verify(pointsHistoryRepository).deleteByUser(student);
        verify(redemptionRequestRepository).deleteByUser(student);
        verify(commentRepository, never()).deleteByAuthor(student);
        verify(dailyCheckInRepository).deleteByUser(student);
        verify(userRepository).save(student);
        verify(postRepository, times(39)).save(any(Post.class));
        verify(commentRepository, times(47)).save(any());
        verify(postFavoriteRepository, times(13)).save(any(PostFavorite.class));
        verify(postBrowseHistoryRepository, times(13)).save(any(PostBrowseHistory.class));
        verify(pointsHistoryRepository, times(13)).save(any(PointsHistory.class));
        verify(redemptionRequestRepository).save(any(RedemptionRequest.class));
        verify(operationLogRepository, times(2)).save(any());
        verify(userBadgeRepository, times(39)).save(any(UserBadge.class));
    }

    @Test
    void seedResetsExistingScenarioArtifactsThenRecreatesStableStudentState() {
        User student = new User();
        student.setUsername("demo_student_anchor");
        student.setRole("USER");
        student.setPoints(120);
        student.setExp(75);
        student.setConsecutiveDays(4);

        User admin = new User();
        admin.setUsername("demo_admin_anchor");
        admin.setRole("ADMIN");

        Post hotPost = existingPost("【演示】校园热帖：春季社团市集逛展指南");
        Post growthPost = existingPost("【演示】成长中心：四月签到打卡交流帖");
        Post pendingPost = existingPost("【演示】待审核：宿舍二手交易注意事项合集");
        Post opsPost = existingPost("【演示】后台复盘：本周内容治理值班记录");
        RewardItem coffee = existingReward("【演示】校园咖啡兑换券");
        RewardItem library = existingReward("【演示】图书馆自习室优先券");

        when(userRepository.findByUsername("demo_guest_anchor")).thenReturn(Optional.of(new User()));
        when(userRepository.findByUsername("demo_student_anchor")).thenReturn(Optional.of(student));
        when(userRepository.findByUsername("demo_admin_anchor")).thenReturn(Optional.of(admin));
        when(postRepository.findByTitle("【演示】校园热帖：春季社团市集逛展指南")).thenReturn(Optional.of(hotPost));
        when(postRepository.findByTitle("【演示】成长中心：四月签到打卡交流帖")).thenReturn(Optional.of(growthPost));
        when(postRepository.findByTitle("【演示】待审核：宿舍二手交易注意事项合集")).thenReturn(Optional.of(pendingPost));
        when(postRepository.findByTitle("【演示】后台复盘：本周内容治理值班记录")).thenReturn(Optional.of(opsPost));
        when(rewardItemRepository.findByName("【演示】校园咖啡兑换券")).thenReturn(Optional.of(coffee));
        when(rewardItemRepository.findByName("【演示】图书馆自习室优先券")).thenReturn(Optional.of(library));
        when(commentRepository.findByPostAndAuthorAndContent(any(Post.class), any(User.class), any())).thenReturn(Optional.empty());
        when(postFavoriteRepository.findByUserAndPost(any(User.class), any(Post.class))).thenReturn(Optional.empty());
        when(postBrowseHistoryRepository.findByUserAndPost(any(User.class), any(Post.class))).thenReturn(Optional.empty());
        when(pointsHistoryRepository.findByUserAndChangeTypeAndNote(any(User.class), any(), any())).thenReturn(Optional.empty());
        when(redemptionRequestRepository.findByUserAndRewardAndStatus(any(User.class), any(RewardItem.class), any())).thenReturn(Optional.empty());
        when(operationLogRepository.findByActionAndTargetTypeAndTargetId(any(), any(), any())).thenReturn(Optional.of(new com.swjtu.forum.entity.OperationLog()));

        demoSeedService.seed();

        assertThat(student.getPoints()).isEqualTo(260);
        assertThat(student.getExp()).isEqualTo(180);
        assertThat(student.getConsecutiveDays()).isEqualTo(0);
        verify(postFavoriteRepository).deleteByUser(student);
        verify(postBrowseHistoryRepository).deleteByUser(student);
        verify(pointsHistoryRepository).deleteByUser(student);
        verify(redemptionRequestRepository).deleteByUser(student);
        verify(commentRepository, never()).deleteByAuthor(student);
        verify(dailyCheckInRepository).deleteByUser(student);
        verify(postFavoriteRepository, times(13)).save(any(PostFavorite.class));
        verify(postBrowseHistoryRepository, times(13)).save(any(PostBrowseHistory.class));
        verify(pointsHistoryRepository, times(13)).save(any(PointsHistory.class));
        verify(redemptionRequestRepository).save(any(RedemptionRequest.class));
        verify(commentRepository, times(47)).save(any());
    }

    private Post existingPost(String title) {
        Post post = new Post();
        post.setTitle(title);
        return post;
    }

    private RewardItem existingReward(String name) {
        RewardItem rewardItem = new RewardItem();
        rewardItem.setName(name);
        return rewardItem;
    }
}
