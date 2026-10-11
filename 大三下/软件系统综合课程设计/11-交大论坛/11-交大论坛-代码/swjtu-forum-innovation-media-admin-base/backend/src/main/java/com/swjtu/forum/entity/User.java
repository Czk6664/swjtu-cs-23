package com.swjtu.forum.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;
import lombok.Data;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;

@Entity
@Table(name = "users")
@Data
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
@EntityListeners(AuditingEntityListener.class)
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false, length = 50)
    private String username;

    @Column(nullable = false)
    @JsonIgnore
    private String password;

    @Column(unique = true, nullable = false, length = 100)
    private String email;

    @Column(length = 20)
    private String studentId;

    @Column(length = 50)
    private String college;

    @Column(length = 50)
    private String major;

    @Column(length = 100)
    private String campusEmail;

    @Column(nullable = false, length = 20)
    private String campusIdentityStatus = "UNVERIFIED";

    @Column(nullable = false)
    private Boolean campusVerified = false;

    @Column(length = 200)
    private String campusVerificationMessage;

    private LocalDateTime campusVerifiedAt;

    private LocalDateTime campusProfileSyncedAt;

    @Column(length = 200)
    private String avatar;

    @Column(length = 500)
    private String bio;

    private Integer level = 1;

    private Integer exp = 0;

    private Integer points = 0;

    private Integer consecutiveDays = 0;

    @Column(nullable = false)
    private String role = "USER";

    @Column(nullable = false)
    private Boolean enabled = true;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    private LocalDateTime updatedAt;

    @ManyToMany(fetch = FetchType.EAGER)
    @JoinTable(
        name = "user_tags",
        joinColumns = @JoinColumn(name = "user_id"),
        inverseJoinColumns = @JoinColumn(name = "tag_id")
    )
    private Set<Tag> tags = new HashSet<>();
}
