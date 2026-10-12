package com.swjtu.forum.repository;

import com.swjtu.forum.entity.OperationLog;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface OperationLogRepository extends JpaRepository<OperationLog, Long> {
    Page<OperationLog> findAllByOrderByCreatedAtDesc(Pageable pageable);
    Optional<OperationLog> findByActionAndTargetTypeAndTargetId(String action, String targetType, Long targetId);
}
