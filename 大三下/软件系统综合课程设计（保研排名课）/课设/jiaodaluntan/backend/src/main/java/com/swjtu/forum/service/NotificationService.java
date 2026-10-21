package com.swjtu.forum.service;

import com.swjtu.forum.entity.Notification;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.exception.NotFoundException;
import com.swjtu.forum.repository.NotificationRepository;
import com.swjtu.forum.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Central entry point for creating and reading in-app notifications. Domain
 * services call the {@code notify*} helpers as side effects of their own writes;
 * a notification never blocks the originating action and is skipped when the
 * recipient would be notifying themselves.
 */
@Service
@RequiredArgsConstructor
public class NotificationService {

    private final NotificationRepository notificationRepository;
    private final UserRepository userRepository;

    @Transactional
    public void notify(User recipient, String type, String title, String content,
                       Long targetId, String targetType) {
        if (recipient == null) {
            return;
        }
        Notification notification = new Notification();
        notification.setRecipient(recipient);
        notification.setType(type);
        notification.setTitle(title);
        notification.setContent(content);
        notification.setTargetId(targetId);
        notification.setTargetType(targetType);
        notification.setIsRead(false);
        notificationRepository.save(notification);
    }

    /** Same as {@link #notify} but skips self-directed notifications (e.g. liking your own post). */
    @Transactional
    public void notifyOther(User recipient, User actor, String type, String title, String content,
                            Long targetId, String targetType) {
        if (recipient == null || (actor != null && recipient.getId() != null
                && recipient.getId().equals(actor.getId()))) {
            return;
        }
        notify(recipient, type, title, content, targetId, targetType);
    }

    @Transactional(readOnly = true)
    public Page<Notification> list(String username, Boolean unreadOnly, Pageable pageable) {
        User recipient = requireUser(username);
        if (Boolean.TRUE.equals(unreadOnly)) {
            return notificationRepository.findByRecipientAndIsReadOrderByCreatedAtDesc(recipient, false, pageable);
        }
        return notificationRepository.findByRecipientOrderByCreatedAtDesc(recipient, pageable);
    }

    @Transactional(readOnly = true)
    public long unreadCount(String username) {
        return notificationRepository.countByRecipientAndIsReadFalse(requireUser(username));
    }

    @Transactional
    public Notification markRead(Long id, String username) {
        User recipient = requireUser(username);
        Notification notification = notificationRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("通知不存在"));
        if (notification.getRecipient() == null
                || !notification.getRecipient().getId().equals(recipient.getId())) {
            // Do not leak existence of another user's notification.
            throw new NotFoundException("通知不存在");
        }
        notification.setIsRead(true);
        return notificationRepository.save(notification);
    }

    @Transactional
    public int markAllRead(String username) {
        return notificationRepository.markAllRead(requireUser(username));
    }

    private User requireUser(String username) {
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new NotFoundException("用户不存在"));
    }
}
