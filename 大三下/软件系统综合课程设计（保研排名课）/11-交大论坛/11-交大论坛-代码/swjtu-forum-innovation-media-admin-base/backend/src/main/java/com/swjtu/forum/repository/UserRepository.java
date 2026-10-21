package com.swjtu.forum.repository;

import com.swjtu.forum.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByUsername(String username);
    Optional<User> findByEmail(String email);
    boolean existsByUsername(String username);
    boolean existsByEmail(String email);
    long countByRoleAndEnabledTrue(String role);
    long countByCreatedAtAfter(java.time.LocalDateTime time);
    long countByEnabledFalse();

    /**
     * Atomic conditional points deduction. Returns 1 when the user had enough
     * points, 0 otherwise. Combined with a transaction rollback this prevents
     * a user's points balance from going negative under concurrent spends.
     */
    @Modifying(flushAutomatically = true, clearAutomatically = true)
    @Query("UPDATE User u SET u.points = u.points - :cost WHERE u.id = :id AND u.points >= :cost")
    int deductPoints(@Param("id") Long id, @Param("cost") int cost);

    @Modifying(flushAutomatically = true, clearAutomatically = true)
    @Query("UPDATE User u SET u.points = u.points + :amount WHERE u.id = :id")
    int addPoints(@Param("id") Long id, @Param("amount") int amount);
}
