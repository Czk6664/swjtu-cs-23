package com.swjtu.forum.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;
import lombok.Data;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

/**
 * A per-user in-app notification. Created by domain events (a reply to your post,
 * a moderation decision on your report, a level-up, a redemption review) and read
 * through the notification center.
 */
@Entity
@Table(
        name = "notifications",
        indexes = {
                @Index(name = "idx_notification_recipient", columnList = "recipient_id"),
                @Index(name = "idx_notification_recipient_read", columnList = "recipient_id, is_read")
        }
)
@Data
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
@EntityListeners(AuditingEntityListener.class)
public class Notification {

    public static final String TYPE_COMMENT = "COMMENT";
    public static final String TYPE_REPLY = "REPLY";
    public static final String TYPE_REPORT = "REPORT";
    public static final String TYPE_LEVEL_UP = "LEVEL_UP";
    public static final String TYPE_REDEMPTION = "REDEMPTION";
    public static final String TYPE_SYSTEM = "SYSTEM";

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "recipient_id", nullable = false)
    @JsonIgnore
    private User recipient;

    @Column(nullable = false, length = 30)
    private String type;

    @Column(nullable = false, length = 120)
    private String title;

    @Column(length = 500)
    private String content;

    /** Optional id of the related entity (e.g. post id) so the frontend can deep-link. */
    private Long targetId;

    /** Optional target type (POST/COMMENT/...) describing what targetId points to. */
    @Column(length = 30)
    private String targetType;

    @Column(name = "is_read", nullable = false)
    private Boolean isRead = false;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
