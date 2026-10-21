package com.swjtu.forum.repository;

import com.swjtu.forum.entity.DailyCheckIn;
import com.swjtu.forum.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.Optional;

public interface DailyCheckInRepository extends JpaRepository<DailyCheckIn, Long> {
    Optional<DailyCheckIn> findByUserAndCheckDate(User user, LocalDate checkDate);
    Page<DailyCheckIn> findByUserOrderByCheckDateDesc(User user, Pageable pageable);
    @Transactional
    void deleteByUser(User user);
}
