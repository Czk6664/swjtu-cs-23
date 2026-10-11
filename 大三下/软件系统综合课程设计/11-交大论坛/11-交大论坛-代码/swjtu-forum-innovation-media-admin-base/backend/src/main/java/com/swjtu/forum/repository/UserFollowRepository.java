package com.swjtu.forum.repository;

import com.swjtu.forum.entity.User;
import com.swjtu.forum.entity.UserFollow;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface UserFollowRepository extends JpaRepository<UserFollow, Long> {

    Optional<UserFollow> findByFollowerAndFollowing(User follower, User following);

    boolean existsByFollowerAndFollowing(User follower, User following);

    long countByFollower(User follower);

    long countByFollowing(User following);

    Page<UserFollow> findByFollowerOrderByCreatedAtDesc(User follower, Pageable pageable);

    Page<UserFollow> findByFollowingOrderByCreatedAtDesc(User following, Pageable pageable);

    @Query("SELECT f.following.id FROM UserFollow f WHERE f.follower = :follower")
    List<Long> findFollowingIds(@Param("follower") User follower);
}
