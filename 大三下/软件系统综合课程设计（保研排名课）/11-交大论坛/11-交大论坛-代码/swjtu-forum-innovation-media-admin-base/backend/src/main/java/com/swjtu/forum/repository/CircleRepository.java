package com.swjtu.forum.repository;

import com.swjtu.forum.entity.Circle;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface CircleRepository extends JpaRepository<Circle, Long> {
    Optional<Circle> findByName(String name);
    Optional<Circle> findBySlug(String slug);
    List<Circle> findAllByOrderByMemberCountDescPostCountDescCreatedAtDesc();
}
