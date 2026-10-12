package com.swjtu.forum.repository;

import com.swjtu.forum.entity.Comment;
import com.swjtu.forum.entity.CommentLike;
import com.swjtu.forum.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface CommentLikeRepository extends JpaRepository<CommentLike, Long> {
    Optional<CommentLike> findByUserAndComment(User user, Comment comment);
}
