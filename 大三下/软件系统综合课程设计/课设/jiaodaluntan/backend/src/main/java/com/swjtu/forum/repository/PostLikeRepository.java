package com.swjtu.forum.repository;

import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.PostLike;
import com.swjtu.forum.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDateTime;
import java.util.Optional;

public interface PostLikeRepository extends JpaRepository<PostLike, Long> {
    Optional<PostLike> findByUserAndPost(User user, Post post);

    long countByCreatedAtAfter(LocalDateTime time);
}
