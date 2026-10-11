package com.swjtu.forum.repository;

import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.PostFavorite;
import com.swjtu.forum.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDateTime;
import java.util.Optional;

public interface PostFavoriteRepository extends JpaRepository<PostFavorite, Long> {
    Optional<PostFavorite> findByUserAndPost(User user, Post post);

    Page<PostFavorite> findByUserOrderByCreatedAtDesc(User user, Pageable pageable);

    long countByUser(User user);

    long countByCreatedAtAfter(LocalDateTime time);

    void deleteByUser(User user);
}
