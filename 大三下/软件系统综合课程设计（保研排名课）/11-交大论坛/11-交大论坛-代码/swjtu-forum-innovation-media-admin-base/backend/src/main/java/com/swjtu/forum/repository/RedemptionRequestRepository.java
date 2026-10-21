package com.swjtu.forum.repository;

import com.swjtu.forum.entity.RedemptionRequest;
import com.swjtu.forum.entity.RewardItem;
import com.swjtu.forum.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

public interface RedemptionRequestRepository extends JpaRepository<RedemptionRequest, Long> {
    @EntityGraph(attributePaths = {"user", "reward"})
    Page<RedemptionRequest> findByUserOrderByCreatedAtDesc(User user, Pageable pageable);

    @EntityGraph(attributePaths = {"user", "reward"})
    Page<RedemptionRequest> findByStatusOrderByCreatedAtDesc(Integer status, Pageable pageable);

    Optional<RedemptionRequest> findByUserAndRewardAndStatus(User user, RewardItem rewardItem, Integer status);

    @Query("select r from RedemptionRequest r join fetch r.user join fetch r.reward where r.id = :id")
    Optional<RedemptionRequest> findByIdWithAssociations(@Param("id") Long id);

    void deleteByUser(User user);
}
