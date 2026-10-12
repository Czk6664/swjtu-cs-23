package com.swjtu.forum.service;

import com.swjtu.forum.entity.Notification;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.exception.NotFoundException;
import com.swjtu.forum.repository.NotificationRepository;
import com.swjtu.forum.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class NotificationServiceTest {

    @Mock
    private NotificationRepository notificationRepository;
    @Mock
    private UserRepository userRepository;

    private NotificationService notificationService;
    private User alice;
    private User bob;

    @BeforeEach
    void setUp() {
        notificationService = new NotificationService(notificationRepository, userRepository);
        alice = user(1L, "alice");
        bob = user(2L, "bob");
    }

    @Test
    void notifyOtherSkipsSelfDirectedNotification() {
        notificationService.notifyOther(alice, alice, Notification.TYPE_COMMENT, "t", "c", 9L, "POST");
        verify(notificationRepository, never()).save(any());
    }

    @Test
    void notifyOtherCreatesNotificationForDifferentRecipient() {
        notificationService.notifyOther(alice, bob, Notification.TYPE_COMMENT, "新评论", "bob 评论了你的帖子", 9L, "POST");

        ArgumentCaptor<Notification> captor = ArgumentCaptor.forClass(Notification.class);
        verify(notificationRepository).save(captor.capture());
        Notification saved = captor.getValue();
        assertThat(saved.getRecipient()).isEqualTo(alice);
        assertThat(saved.getType()).isEqualTo(Notification.TYPE_COMMENT);
        assertThat(saved.getIsRead()).isFalse();
        assertThat(saved.getTargetId()).isEqualTo(9L);
    }

    @Test
    void markReadRejectsAnotherUsersNotification() {
        Notification foreign = new Notification();
        foreign.setId(5L);
        foreign.setRecipient(bob);
        when(userRepository.findByUsername("alice")).thenReturn(Optional.of(alice));
        when(notificationRepository.findById(5L)).thenReturn(Optional.of(foreign));

        assertThatThrownBy(() -> notificationService.markRead(5L, "alice"))
                .isInstanceOf(NotFoundException.class);
        verify(notificationRepository, never()).save(any());
    }

    @Test
    void markReadSetsReadFlagForOwner() {
        Notification own = new Notification();
        own.setId(6L);
        own.setRecipient(alice);
        own.setIsRead(false);
        when(userRepository.findByUsername("alice")).thenReturn(Optional.of(alice));
        when(notificationRepository.findById(6L)).thenReturn(Optional.of(own));
        when(notificationRepository.save(any(Notification.class))).thenAnswer(i -> i.getArgument(0));

        Notification result = notificationService.markRead(6L, "alice");

        assertThat(result.getIsRead()).isTrue();
    }

    private User user(Long id, String username) {
        User user = new User();
        user.setId(id);
        user.setUsername(username);
        return user;
    }
}
