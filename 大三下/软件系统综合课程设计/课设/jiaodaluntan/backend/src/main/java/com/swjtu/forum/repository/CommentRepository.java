package com.swjtu.forum.repository;

import com.swjtu.forum.entity.Comment;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface CommentRepository extends JpaRepository<Comment, Long> {
    Page<Comment> findByPostAndParentIsNullOrderByCreatedAtDesc(Post post, Pageable pageable);
    Page<Comment> findByPostAndParentIsNullAndStatusOrderByCreatedAtDesc(Post post, Integer status, Pageable pageable);
    Optional<Comment> findByPostAndAuthorAndContent(Post post, User author, String content);
    Optional<Comment> findByPostAndAcceptedTrue(Post post);
    List<Comment> findByParentOrderByCreatedAtAsc(Comment parent);
    List<Comment> findByParentAndStatusOrderByCreatedAtAsc(Comment parent, Integer status);
    long countByPost(Post post);
    long countByPostAndStatus(Post post, Integer status);
    long countByAuthor(User author);
    long countByAuthorAndAcceptedTrue(User author);
    long countByCreatedAtAfter(LocalDateTime time);
    long countByCreatedAtBetween(LocalDateTime start, LocalDateTime end);
    @Query("SELECT DISTINCT c.author.id FROM Comment c WHERE c.createdAt BETWEEN :start AND :end")
    List<Long> findDistinctAuthorIdsByCreatedAtBetween(@Param("start") LocalDateTime start, @Param("end") LocalDateTime end);
    void deleteByAuthor(User author);
}
