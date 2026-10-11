package com.swjtu.forum.controller;

import com.swjtu.forum.dto.ApiResponse;
import com.swjtu.forum.dto.InterestTagsRequest;
import com.swjtu.forum.dto.RedemptionRequestResponse;
import com.swjtu.forum.entity.DailyCheckIn;
import com.swjtu.forum.entity.PointsHistory;
import com.swjtu.forum.entity.RedemptionRequest;
import com.swjtu.forum.entity.RewardItem;
import com.swjtu.forum.entity.Tag;
import com.swjtu.forum.service.GrowthDiscoveryService;
import com.swjtu.forum.util.Pageables;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Set;

@RestController
@RequestMapping("/growth")
@RequiredArgsConstructor
public class GrowthController {

    private final GrowthDiscoveryService growthDiscoveryService;

    @PostMapping("/interests")
    public ApiResponse<Set<Tag>> updateInterests(@RequestBody InterestTagsRequest request, Authentication authentication) {
        return ApiResponse.success("兴趣标签已更新",
                growthDiscoveryService.updateInterests(authentication.getName(), request.getTags()));
    }

    @PostMapping("/check-in")
    public ApiResponse<DailyCheckIn> checkIn(Authentication authentication) {
        return ApiResponse.success("签到成功", growthDiscoveryService.checkIn(authentication.getName()));
    }

    @GetMapping("/check-ins")
    public ApiResponse<Page<DailyCheckIn>> checkInHistory(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            Authentication authentication) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(growthDiscoveryService.getCheckInHistory(authentication.getName(), pageable));
    }

    @GetMapping("/points-history")
    public ApiResponse<Page<PointsHistory>> pointsHistory(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            Authentication authentication) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(growthDiscoveryService.getPointsHistory(authentication.getName(), pageable));
    }

    @GetMapping("/rewards")
    public ApiResponse<List<RewardItem>> rewards() {
        return ApiResponse.success(growthDiscoveryService.listActiveRewards());
    }

    @PostMapping("/rewards/{id}/redeem")
    public ApiResponse<RedemptionRequestResponse> redeem(@PathVariable Long id, Authentication authentication) {
        RedemptionRequest saved = growthDiscoveryService.redeem(id, authentication.getName());
        return ApiResponse.success("兑换申请已提交", RedemptionRequestResponse.from(saved));
    }

    @GetMapping("/achievements")
    public ApiResponse<java.util.Map<String, Object>> achievements(Authentication authentication) {
        return ApiResponse.success(growthDiscoveryService.achievements(authentication.getName()));
    }

    @GetMapping("/redemptions")
    public ApiResponse<Page<RedemptionRequestResponse>> myRedemptions(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            Authentication authentication) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(growthDiscoveryService.myRedemptions(authentication.getName(), pageable)
                .map(RedemptionRequestResponse::from));
    }
}
