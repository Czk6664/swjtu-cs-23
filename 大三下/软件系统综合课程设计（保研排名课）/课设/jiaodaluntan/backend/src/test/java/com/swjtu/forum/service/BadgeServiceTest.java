package com.swjtu.forum.service;

import com.swjtu.forum.entity.Badge;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.entity.UserBadge;
import com.swjtu.forum.repository.BadgeRepository;
import com.swjtu.forum.repository.CommentRepository;
import com.swjtu.forum.repository.PostFavoriteRepository;
import com.swjtu.forum.repository.PostRepository;
import com.swjtu.forum.repository.SectionRepository;
import com.swjtu.forum.repository.UserBadgeRepository;
import com.swjtu.forum.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class BadgeServiceTest {

    @Mock
    private BadgeRepository badgeRepository;
    @Mock
    private UserBadgeRepository userBadgeRepository;
    @Mock
    private UserRepository userRepository;
    @Mock
    private PostRepository postRepository;
    @Mock
    private CommentRepository commentRepository;
    @Mock
    private PostFavoriteRepository postFavoriteRepository;
    @Mock
    private SectionRepository sectionRepository;
    @Mock
    private UserService userService;

    private BadgeService badgeService;

    @BeforeEach
    void setUp() {
        badgeService = new BadgeService(
                badgeRepository,
                userBadgeRepository,
                userRepository,
                postRepository,
                commentRepository,
                postFavoriteRepository,
                sectionRepository,
                userService
        );
    }

    @Test
    void grantByCodeDoesNotDuplicateExistingUserBadge() {
        User user = new User();
        user.setId(1L);
        user.setUsername("alice");

        Badge badge = new Badge();
        badge.setId(2L);
        badge.setCode("helpful_star");
        badge.setName("互助之星");

        LocalDateTime firstEarnedAt = LocalDateTime.of(2026, 6, 8, 10, 0);
        UserBadge saved = new UserBadge();
        saved.setId(3L);
        saved.setUser(user);
        saved.setBadge(badge);
        saved.setEarnedAt(firstEarnedAt);

        when(badgeRepository.findByCode("helpful_star")).thenReturn(Optional.of(badge));
        when(userBadgeRepository.findByUserAndBadge(user, badge))
                .thenReturn(Optional.empty())
                .thenReturn(Optional.of(saved));
        when(userBadgeRepository.save(org.mockito.ArgumentMatchers.any(UserBadge.class))).thenReturn(saved);

        Optional<UserBadge> firstGrant = badgeService.grantByCode(user, "helpful_star");
        Optional<UserBadge> duplicateGrant = badgeService.grantByCode(user, "helpful_star");

        assertThat(firstGrant).contains(saved);
        assertThat(duplicateGrant).isEmpty();
        assertThat(saved.getEarnedAt()).isEqualTo(firstEarnedAt);
        verify(userBadgeRepository).save(org.mockito.ArgumentMatchers.any(UserBadge.class));
    }
}
