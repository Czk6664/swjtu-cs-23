package com.swjtu.forum.repository;

import com.swjtu.forum.entity.Section;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface SectionRepository extends JpaRepository<Section, Long> {
    Optional<Section> findByName(String name);
    List<Section> findAllByOrderBySortOrderAsc();
}
