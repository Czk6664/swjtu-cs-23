package com.swjtu.forum.controller;

import com.swjtu.forum.dto.ApiResponse;
import com.swjtu.forum.entity.Notification;
import com.swjtu.forum.service.NotificationService;
import com.swjtu.forum.util.Pageables;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/notifications")
@RequiredArgsConstructor
public class NotificationController {

    private final NotificationService notificationService;

    @GetMapping
    public ApiResponse<Page<Notification>> list(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) Boolean unreadOnly,
            Authentication authentication) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(notificationService.list(authentication.getName(), unreadOnly, pageable));
    }

    @GetMapping("/unread-count")
    public ApiResponse<Map<String, Object>> unreadCount(Authentication authentication) {
        long count = notificationService.unreadCount(authentication.getName());
        return ApiResponse.success(Map.of("unread", count));
    }

    @PatchMapping("/{id}/read")
    public ApiResponse<Notification> markRead(@PathVariable Long id, Authentication authentication) {
        return ApiResponse.success("已读", notificationService.markRead(id, authentication.getName()));
    }

    @PatchMapping("/read-all")
    public ApiResponse<Map<String, Object>> markAllRead(Authentication authentication) {
        int updated = notificationService.markAllRead(authentication.getName());
        return ApiResponse.success("全部已读", Map.of("updated", updated));
    }
}
