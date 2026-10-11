package com.swjtu.forum.controller;

import com.swjtu.forum.dto.ApiResponse;
import com.swjtu.forum.entity.Badge;
import com.swjtu.forum.entity.UserBadge;
import com.swjtu.forum.service.BadgeService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequiredArgsConstructor
public class BadgeController {

    private final BadgeService badgeService;

    @GetMapping("/badges")
    public ApiResponse<List<Badge>> badges() {
        return ApiResponse.success(badgeService.listBadges());
    }

    @GetMapping("/users/{id}/badges")
    public ApiResponse<List<UserBadge>> userBadges(@PathVariable Long id) {
        return ApiResponse.success(badgeService.listUserBadges(id));
    }

    @GetMapping("/badges/me")
    public ApiResponse<List<UserBadge>> currentUserBadges(Authentication authentication) {
        return ApiResponse.success(badgeService.listCurrentUserBadges(authentication.getName()));
    }

    @PostMapping("/badges/check")
    public ApiResponse<List<UserBadge>> check(Authentication authentication) {
        return ApiResponse.success("徽章检查完成", badgeService.checkCurrentUserBadges(authentication.getName()));
    }
}
