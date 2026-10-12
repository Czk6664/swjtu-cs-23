package com.swjtu.forum.entity;

import jakarta.persistence.*;
import lombok.Data;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

@Entity
@Table(name = "redemption_requests")
@Data
@EntityListeners(AuditingEntityListener.class)
public class RedemptionRequest {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id")
    private User user;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "reward_id")
    private RewardItem reward;

    @Column(nullable = false)
    private Integer pointsCost = 0;

    @Column(nullable = false)
    private Integer status = 0; // 0-pending,1-approved,2-rejected

    @Column(length = 300)
    private String reviewNote;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    private LocalDateTime updatedAt;
}
