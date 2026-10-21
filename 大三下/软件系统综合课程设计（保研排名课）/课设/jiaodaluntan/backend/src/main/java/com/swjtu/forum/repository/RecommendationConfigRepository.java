package com.swjtu.forum.repository;

import com.swjtu.forum.entity.RecommendationConfig;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface RecommendationConfigRepository extends JpaRepository<RecommendationConfig, Long> {
}
