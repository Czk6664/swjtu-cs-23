package com.swjtu.forum.repository;

import com.swjtu.forum.entity.Report;
import com.swjtu.forum.entity.ReportReviewLog;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ReportReviewLogRepository extends JpaRepository<ReportReviewLog, Long> {
    List<ReportReviewLog> findByReportOrderByCreatedAtDesc(Report report);
}
