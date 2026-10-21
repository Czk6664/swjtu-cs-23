package com.swjtu.forum.repository;

import com.swjtu.forum.entity.PointsHistory;
import com.swjtu.forum.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface PointsHistoryRepository extends JpaRepository<PointsHistory, Long> {
    Page<PointsHistory> findByUserOrderByCreatedAtDesc(User user, Pageable pageable);
    Optional<PointsHistory> findByUserAndChangeTypeAndNote(User user, String changeType, String note);
    void deleteByUser(User user);
}
