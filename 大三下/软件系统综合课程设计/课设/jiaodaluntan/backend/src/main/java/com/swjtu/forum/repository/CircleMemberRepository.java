package com.swjtu.forum.repository;

import com.swjtu.forum.entity.Circle;
import com.swjtu.forum.entity.CircleMember;
import com.swjtu.forum.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface CircleMemberRepository extends JpaRepository<CircleMember, Long> {
    Optional<CircleMember> findByCircleAndUser(Circle circle, User user);
    boolean existsByCircleAndUser(Circle circle, User user);
    long countByCircle(Circle circle);
    void deleteByCircleAndUser(Circle circle, User user);
}
