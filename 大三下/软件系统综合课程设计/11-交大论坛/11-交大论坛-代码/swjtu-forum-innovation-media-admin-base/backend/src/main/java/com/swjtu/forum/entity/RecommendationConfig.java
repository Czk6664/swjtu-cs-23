package com.swjtu.forum.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Data;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

@Entity
@Table(name = "recommendation_configs")
@Data
@EntityListeners(AuditingEntityListener.class)
public class RecommendationConfig {

    @Id
    private Long id = 1L;

    @Column(nullable = false)
    private Integer tagWeight = 50;

    @Column(nullable = false)
    private Integer engagementWeight = 30;

    @Column(nullable = false)
    private Integer recencyWeight = 20;

    @Column(nullable = false)
    private Boolean explainabilityEnabled = true;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    private LocalDateTime updatedAt;
}
