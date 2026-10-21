package com.swjtu.forum.repository;

import com.swjtu.forum.entity.Badge;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.entity.UserBadge;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface UserBadgeRepository extends JpaRepository<UserBadge, Long> {
    Optional<UserBadge> findByUserAndBadge(User user, Badge badge);

    List<UserBadge> findByUserOrderByEarnedAtDesc(User user);
}
