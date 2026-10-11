package com.swjtu.forum.repository;

import com.swjtu.forum.entity.Circle;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface PostRepository extends JpaRepository<Post, Long> {
    Page<Post> findAllByOrderByCreatedAtDesc(Pageable pageable);

    long countByCreatedAtAfter(LocalDateTime time);

    long countByCreatedAtBetween(LocalDateTime start, LocalDateTime end);

    @Query("SELECT DISTINCT p.author.id FROM Post p WHERE p.createdAt BETWEEN :start AND :end")
    List<Long> findDistinctAuthorIdsByCreatedAtBetween(@Param("start") LocalDateTime start, @Param("end") LocalDateTime end);

    long countByStatus(Integer status);

    List<Post> findByStatusAndCreatedAtAfter(Integer status, LocalDateTime time);

    Page<Post> findByStatusOrderByCreatedAtDesc(Integer status, Pageable pageable);

    Page<Post> findBySectionAndStatusOrderByCreatedAtDesc(Section section, Integer status, Pageable pageable);

    Page<Post> findByCircleAndStatusOrderByCreatedAtDesc(Circle circle, Integer status, Pageable pageable);

    Page<Post> findByAuthorOrderByCreatedAtDesc(User author, Pageable pageable);

    Page<Post> findByAuthorAndStatusOrderByCreatedAtDesc(User author, Integer status, Pageable pageable);

    Optional<Post> findByIdAndAuthor(Long id, User author);

    Optional<Post> findByTitle(String title);

    Optional<Post> findByIdAndStatus(Long id, Integer status);

    long countBySection(Section section);

    long countBySectionAndStatus(Section section, Integer status);

    long countByAuthor(User author);

    long countByAuthorAndStatus(User author, Integer status);

    long countByAuthorAndSectionAndStatus(User author, Section section, Integer status);

    @Query("SELECT COALESCE(SUM(p.likeCount), 0) FROM Post p WHERE p.author = :author")
    long sumLikesReceived(@Param("author") User author);

    @Query("SELECT p FROM Post p WHERE p.status = :status AND (LOWER(p.title) LIKE LOWER(CONCAT('%', :keyword, '%')) OR LOWER(p.content) LIKE LOWER(CONCAT('%', :keyword, '%'))) ORDER BY p.createdAt DESC")
    Page<Post> searchPublished(@Param("status") Integer status, @Param("keyword") String keyword, Pageable pageable);

    /**
     * Broader search that also matches the author's username and any tag name, so a query
     * like "Java" or an author handle surfaces relevant posts, not just title/body hits.
     */
    @Query("SELECT DISTINCT p FROM Post p LEFT JOIN p.tags t WHERE p.status = :status AND ("
            + "LOWER(p.title) LIKE LOWER(CONCAT('%', :keyword, '%')) OR "
            + "LOWER(p.content) LIKE LOWER(CONCAT('%', :keyword, '%')) OR "
            + "LOWER(p.author.username) LIKE LOWER(CONCAT('%', :keyword, '%')) OR "
            + "LOWER(t.name) LIKE LOWER(CONCAT('%', :keyword, '%'))) "
            + "ORDER BY p.heatScore DESC, p.createdAt DESC")
    Page<Post> searchPublishedExtended(@Param("status") Integer status, @Param("keyword") String keyword, Pageable pageable);

    @Query("SELECT DISTINCT p FROM Post p LEFT JOIN p.tags t WHERE p.status = 1 AND (t.id IN :tagIds OR :tagIdsEmpty = true) ORDER BY p.heatScore DESC, p.createdAt DESC")
    Page<Post> recommendByTagIds(@Param("tagIds") java.util.Collection<Long> tagIds, @Param("tagIdsEmpty") boolean tagIdsEmpty, Pageable pageable);

    @Query("SELECT p FROM Post p WHERE p.status = 1 ORDER BY p.heatScore DESC, p.likeCount DESC, p.createdAt DESC")
    Page<Post> findHotPosts(Pageable pageable);

    @Query("SELECT p FROM Post p WHERE p.status = 1 AND p.author.id IN :authorIds ORDER BY p.createdAt DESC")
    Page<Post> findPublishedByAuthorIds(@Param("authorIds") java.util.Collection<Long> authorIds, Pageable pageable);
}
