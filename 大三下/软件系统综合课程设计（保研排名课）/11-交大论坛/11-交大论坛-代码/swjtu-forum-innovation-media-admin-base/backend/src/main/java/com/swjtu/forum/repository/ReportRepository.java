package com.swjtu.forum.repository;

import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.Report;
import com.swjtu.forum.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

public interface ReportRepository extends JpaRepository<Report, Long>, JpaSpecificationExecutor<Report> {
    boolean existsByReporterAndPostAndStatus(User reporter, Post post, Integer status);
    Page<Report> findByStatusOrderByCreatedAtDesc(Integer status, Pageable pageable);
    Page<Report> findAllByOrderByCreatedAtDesc(Pageable pageable);
}
