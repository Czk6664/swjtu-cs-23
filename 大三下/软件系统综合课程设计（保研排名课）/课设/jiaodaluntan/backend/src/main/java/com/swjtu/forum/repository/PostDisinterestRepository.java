package com.swjtu.forum.repository;

import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.PostDisinterest;
import com.swjtu.forum.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Collection;
import java.util.Set;

public interface PostDisinterestRepository extends JpaRepository<PostDisinterest, Long> {
    boolean existsByUserAndPost(User user, Post post);

    @Query("select record.post.id from PostDisinterest record where record.user = :user and record.post.id in :postIds")
    Set<Long> findPostIdsByUserAndPostIdIn(@Param("user") User user, @Param("postIds") Collection<Long> postIds);
}
