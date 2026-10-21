package com.swjtu.forum.service;

import com.swjtu.forum.entity.User;
import com.swjtu.forum.entity.UserFollow;
import com.swjtu.forum.exception.ApiException;
import com.swjtu.forum.repository.UserFollowRepository;
import com.swjtu.forum.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Map;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class FollowServiceTest {

    @Mock
    private UserFollowRepository userFollowRepository;
    @Mock
    private UserRepository userRepository;
    @Mock
    private NotificationService notificationService;

    private FollowService followService;
    private User alice;
    private User bob;

    @BeforeEach
    void setUp() {
        followService = new FollowService(userFollowRepository, userRepository, notificationService);
        alice = user(1L, "alice");
        bob = user(2L, "bob");
    }

    @Test
    void followingYourselfIsRejected() {
        when(userRepository.findByUsername("alice")).thenReturn(Optional.of(alice));
        when(userRepository.findById(1L)).thenReturn(Optional.of(alice));

        assertThatThrownBy(() -> followService.follow(1L, "alice"))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("不能关注自己");
        verify(userFollowRepository, never()).saveAndFlush(any());
    }

    @Test
    void followCreatesEdgeAndNotifiesTarget() {
        when(userRepository.findByUsername("alice")).thenReturn(Optional.of(alice));
        when(userRepository.findById(2L)).thenReturn(Optional.of(bob));
        when(userFollowRepository.existsByFollowerAndFollowing(alice, bob)).thenReturn(false);
        when(userFollowRepository.countByFollowing(bob)).thenReturn(1L);
        when(userFollowRepository.countByFollower(bob)).thenReturn(0L);

        Map<String, Object> stats = followService.follow(2L, "alice");

        verify(userFollowRepository).saveAndFlush(any(UserFollow.class));
        verify(notificationService).notifyOther(any(), any(), any(), any(), any(), any(), any());
        assertThat(stats.get("followers")).isEqualTo(1L);
    }

    @Test
    void followIsIdempotentWhenAlreadyFollowing() {
        when(userRepository.findByUsername("alice")).thenReturn(Optional.of(alice));
        when(userRepository.findById(2L)).thenReturn(Optional.of(bob));
        when(userFollowRepository.existsByFollowerAndFollowing(alice, bob)).thenReturn(true);

        followService.follow(2L, "alice");

        verify(userFollowRepository, never()).saveAndFlush(any());
    }

    @Test
    void unfollowDeletesExistingEdge() {
        UserFollow edge = new UserFollow();
        when(userRepository.findByUsername("alice")).thenReturn(Optional.of(alice));
        when(userRepository.findById(2L)).thenReturn(Optional.of(bob));
        when(userFollowRepository.findByFollowerAndFollowing(alice, bob)).thenReturn(Optional.of(edge));

        followService.unfollow(2L, "alice");

        verify(userFollowRepository).delete(edge);
    }

    private User user(Long id, String username) {
        User user = new User();
        user.setId(id);
        user.setUsername(username);
        return user;
    }
}
