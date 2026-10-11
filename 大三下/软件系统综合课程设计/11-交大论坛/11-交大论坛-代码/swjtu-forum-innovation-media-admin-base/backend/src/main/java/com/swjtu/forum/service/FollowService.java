package com.swjtu.forum.service;

import com.swjtu.forum.entity.Notification;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.entity.UserFollow;
import com.swjtu.forum.exception.ApiException;
import com.swjtu.forum.exception.NotFoundException;
import com.swjtu.forum.repository.UserFollowRepository;
import com.swjtu.forum.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Social graph operations: follow / unfollow and the counters and ids used by
 * the recommendation engine and profile pages.
 */
@Service
@RequiredArgsConstructor
public class FollowService {

    private final UserFollowRepository userFollowRepository;
    private final UserRepository userRepository;
    private final NotificationService notificationService;

    @Transactional
    public Map<String, Object> follow(Long targetUserId, String username) {
        User follower = requireUser(username);
        User target = userRepository.findById(targetUserId)
                .orElseThrow(() -> new NotFoundException("用户不存在"));
        if (follower.getId().equals(target.getId())) {
            throw new ApiException(400, "不能关注自己");
        }
        if (!userFollowRepository.existsByFollowerAndFollowing(follower, target)) {
            UserFollow follow = new UserFollow();
            follow.setFollower(follower);
            follow.setFollowing(target);
            try {
                userFollowRepository.saveAndFlush(follow);
                notificationService.notifyOther(target, follower, Notification.TYPE_SYSTEM,
                        "你有了新粉丝", follower.getUsername() + " 关注了你", follower.getId(), "USER");
            } catch (DataIntegrityViolationException ignored) {
                // Concurrent duplicate follow — the unique constraint makes this idempotent.
            }
        }
        return stats(target, follower);
    }

    @Transactional
    public Map<String, Object> unfollow(Long targetUserId, String username) {
        User follower = requireUser(username);
        User target = userRepository.findById(targetUserId)
                .orElseThrow(() -> new NotFoundException("用户不存在"));
        userFollowRepository.findByFollowerAndFollowing(follower, target)
                .ifPresent(userFollowRepository::delete);
        return stats(target, follower);
    }

    @Transactional(readOnly = true)
    public Map<String, Object> followStats(Long targetUserId, String username) {
        User target = userRepository.findById(targetUserId)
                .orElseThrow(() -> new NotFoundException("用户不存在"));
        User viewer = username == null ? null : userRepository.findByUsername(username).orElse(null);
        return stats(target, viewer);
    }

    @Transactional(readOnly = true)
    public Page<UserFollow> following(String username, Pageable pageable) {
        return userFollowRepository.findByFollowerOrderByCreatedAtDesc(requireUser(username), pageable);
    }

    @Transactional(readOnly = true)
    public Page<UserFollow> followers(String username, Pageable pageable) {
        return userFollowRepository.findByFollowingOrderByCreatedAtDesc(requireUser(username), pageable);
    }

    @Transactional(readOnly = true)
    public List<Long> followingIds(User follower) {
        return userFollowRepository.findFollowingIds(follower);
    }

    private Map<String, Object> stats(User target, User viewer) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("userId", target.getId());
        result.put("followers", userFollowRepository.countByFollowing(target));
        result.put("following", userFollowRepository.countByFollower(target));
        result.put("isFollowing", viewer != null
                && !viewer.getId().equals(target.getId())
                && userFollowRepository.existsByFollowerAndFollowing(viewer, target));
        return result;
    }

    private User requireUser(String username) {
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new NotFoundException("用户不存在"));
    }
}
