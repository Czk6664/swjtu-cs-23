package com.swjtu.forum.security;

import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * In-memory brute-force guard for the login endpoint. Tracks consecutive failed
 * attempts per key (username) and temporarily locks the account after too many
 * failures within a sliding window. No external dependency (Redis) required, which
 * keeps the zero-config local profile working out of the box.
 */
@Service
public class LoginAttemptService {

    private static final int MAX_ATTEMPTS = 5;
    private static final Duration LOCK_DURATION = Duration.ofMinutes(5);

    private final Map<String, Attempt> attempts = new ConcurrentHashMap<>();

    public boolean isBlocked(String key) {
        Attempt attempt = attempts.get(normalize(key));
        if (attempt == null) {
            return false;
        }
        if (attempt.count < MAX_ATTEMPTS) {
            return false;
        }
        boolean stillLocked = Instant.now().isBefore(attempt.lastFailure.plus(LOCK_DURATION));
        if (!stillLocked) {
            attempts.remove(normalize(key));
        }
        return stillLocked;
    }

    public void recordFailure(String key) {
        attempts.compute(normalize(key), (k, existing) -> {
            Instant now = Instant.now();
            if (existing == null || now.isAfter(existing.lastFailure.plus(LOCK_DURATION))) {
                return new Attempt(1, now);
            }
            return new Attempt(existing.count + 1, now);
        });
    }

    public void recordSuccess(String key) {
        attempts.remove(normalize(key));
    }

    private String normalize(String key) {
        return key == null ? "" : key.trim().toLowerCase();
    }

    private record Attempt(int count, Instant lastFailure) {
    }
}
