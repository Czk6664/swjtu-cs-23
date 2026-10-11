package com.swjtu.forum.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;
import lombok.Data;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Entity
@Table(name = "posts")
@Data
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
@EntityListeners(AuditingEntityListener.class)
public class Post {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User author;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "section_id", nullable = false)
    private Section section;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "circle_id")
    private Circle circle;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(length = 500)
    private String coverImage;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "post_images", joinColumns = @JoinColumn(name = "post_id"))
    @OrderColumn(name = "sort_order")
    @Column(name = "image_url", length = 500)
    private List<String> imageUrls = new ArrayList<>();

    private Integer viewCount = 0;

    private Integer likeCount = 0;

    private Integer commentCount = 0;

    private Integer collectCount = 0;

    private Integer heatScore = 0;

    private Long acceptedCommentId;

    @Column(nullable = false)
    private Integer status = 1; // 0-寰呭鏍? 1-姝ｅ父, 2-闅愯棌

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    private LocalDateTime updatedAt;

    @ManyToMany(fetch = FetchType.LAZY)
    @JoinTable(
        name = "post_tags",
        joinColumns = @JoinColumn(name = "post_id"),
        inverseJoinColumns = @JoinColumn(name = "tag_id")
    )
    private Set<Tag> tags = new HashSet<>();

    @Transient
    private Double recommendationScore;

    @Transient
    private List<String> recommendationReasons = new ArrayList<>();

    @Transient
    private Boolean likedByCurrentUser = false;

    @Transient
    private Boolean favoritedByCurrentUser = false;
}

