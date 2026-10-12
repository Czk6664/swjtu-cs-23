package com.swjtu.forum.entity;

import jakarta.persistence.*;
import lombok.Data;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "daily_checkins", uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "check_date"}))
@Data
@EntityListeners(AuditingEntityListener.class)
public class DailyCheckIn {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id")
    private User user;

    @Column(name = "check_date", nullable = false)
    private LocalDate checkDate;

    @Column(nullable = false)
    private Integer gainedPoints = 0;

    @Column(nullable = false)
    private Integer gainedExp = 0;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
