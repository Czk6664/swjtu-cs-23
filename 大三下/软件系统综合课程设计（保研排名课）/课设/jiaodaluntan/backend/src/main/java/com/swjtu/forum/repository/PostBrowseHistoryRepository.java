package com.swjtu.forum.repository;

import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.PostBrowseHistory;
import com.swjtu.forum.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface PostBrowseHistoryRepository extends JpaRepository<PostBrowseHistory, Long> {

    Optional<PostBrowseHistory> findByUserAndPost(User user, Post post);

    Page<PostBrowseHistory> findByUserOrderByLastViewedAtDesc(User user, Pageable pageable);

    void deleteByUser(User user);
}
