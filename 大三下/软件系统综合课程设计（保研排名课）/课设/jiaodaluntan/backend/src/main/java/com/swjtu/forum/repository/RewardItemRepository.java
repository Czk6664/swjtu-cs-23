package com.swjtu.forum.repository;

import com.swjtu.forum.entity.RewardItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface RewardItemRepository extends JpaRepository<RewardItem, Long> {
    List<RewardItem> findByStatusOrderByCostPointsAsc(Integer status);
    Optional<RewardItem> findByName(String name);

    /**
     * Atomic conditional stock decrement. Returns the number of rows updated:
     * 1 when stock was available, 0 when stock was already depleted. Prevents
     * overselling under concurrent redemption (check-then-act race).
     */
    @Modifying(flushAutomatically = true, clearAutomatically = true)
    @Query("UPDATE RewardItem r SET r.stock = r.stock - 1 WHERE r.id = :id AND r.stock > 0")
    int decrementStock(@Param("id") Long id);

    @Modifying(flushAutomatically = true, clearAutomatically = true)
    @Query("UPDATE RewardItem r SET r.stock = r.stock + 1 WHERE r.id = :id")
    int incrementStock(@Param("id") Long id);
}
