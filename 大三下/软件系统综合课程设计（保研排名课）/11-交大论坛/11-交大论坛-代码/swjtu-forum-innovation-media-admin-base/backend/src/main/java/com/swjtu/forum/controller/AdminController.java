package com.swjtu.forum.controller;

import com.swjtu.forum.dto.ApiResponse;
import com.swjtu.forum.dto.AdminPostManageRequest;
import com.swjtu.forum.dto.BulkReportReviewResponse;
import com.swjtu.forum.dto.BulkReviewReportRequest;
import com.swjtu.forum.dto.PostModerationRequest;
import com.swjtu.forum.dto.RecommendationConfigRequest;
import com.swjtu.forum.dto.RecommendationPreviewResponse;
import com.swjtu.forum.dto.RedemptionRequestResponse;
import com.swjtu.forum.dto.RewardItemManageRequest;
import com.swjtu.forum.dto.ReviewRedemptionRequest;
import com.swjtu.forum.dto.ReviewReportRequest;
import com.swjtu.forum.dto.SectionManageRequest;
import com.swjtu.forum.entity.Comment;
import com.swjtu.forum.entity.OperationLog;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.RecommendationConfig;
import com.swjtu.forum.entity.Report;
import com.swjtu.forum.entity.RewardItem;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.service.AdminOpsService;
import com.swjtu.forum.service.GrowthDiscoveryService;
import com.swjtu.forum.service.ReportService;
import com.swjtu.forum.util.Pageables;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/admin")
@RequiredArgsConstructor
public class AdminController {

    private final AdminOpsService adminOpsService;
    private final GrowthDiscoveryService growthDiscoveryService;
    private final ReportService reportService;
    private final com.swjtu.forum.service.AnalyticsService analyticsService;

    @GetMapping("/posts/pending")
    @PreAuthorize("hasAnyRole('MODERATOR', 'ADMIN')")
    public ApiResponse<Page<Post>> getPendingPosts(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(adminOpsService.getPendingPosts(pageable));
    }

    @GetMapping("/posts")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<Page<Post>> getAllPosts(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(adminOpsService.listAllPosts(pageable));
    }

    @GetMapping("/reports")
    @PreAuthorize("hasAnyRole('MODERATOR', 'ADMIN')")
    public ApiResponse<Page<Report>> getReports(
            @RequestParam(required = false) Integer status,
            @RequestParam(required = false) String reason,
            @RequestParam(defaultValue = "priority") String sort,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(reportService.listReports(status, reason, sort, pageable));
    }

    @PatchMapping("/reports/{id}/review")
    @PreAuthorize("hasAnyRole('MODERATOR', 'ADMIN')")
    public ApiResponse<java.util.Map<String, Object>> reviewReport(
            @PathVariable Long id,
            @Valid @RequestBody ReviewReportRequest request,
            Authentication authentication) {
        Report report = reportService.reviewReport(id, request, authentication.getName());
        return ApiResponse.success(
                Boolean.TRUE.equals(request.getAccept()) ? "举报已采纳" : "举报已驳回",
                java.util.Map.of(
                        "id", report.getId(),
                        "status", report.getStatus(),
                        "reviewNote", report.getReviewNote() == null ? "" : report.getReviewNote()
                )
        );
    }

    @PatchMapping("/reports/review/bulk")
    @PreAuthorize("hasAnyRole('MODERATOR', 'ADMIN')")
    public ApiResponse<BulkReportReviewResponse> bulkReviewReports(
            @Valid @RequestBody BulkReviewReportRequest request,
            Authentication authentication) {
        BulkReportReviewResponse response = reportService.bulkReviewReports(request, authentication.getName());
        String message = Boolean.TRUE.equals(request.getAccept()) ? "举报批量采纳成功" : "举报批量驳回成功";
        return ApiResponse.success(message, response);
    }

    @PutMapping("/posts/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<Post> updatePost(
            @PathVariable Long id,
            @Valid @RequestBody AdminPostManageRequest request,
            Authentication authentication) {
        return ApiResponse.success("帖子更新成功", adminOpsService.updatePost(id, request, authentication.getName()));
    }

    @DeleteMapping("/posts/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<Void> deletePost(@PathVariable Long id, Authentication authentication) {
        adminOpsService.deletePost(id, authentication.getName());
        return ApiResponse.success("帖子已隐藏并保留审计数据", null);
    }

    @PatchMapping("/posts/{id}/status")
    @PreAuthorize("hasAnyRole('MODERATOR', 'ADMIN')")
    public ApiResponse<Post> moderatePost(
            @PathVariable Long id,
            @Valid @RequestBody PostModerationRequest request,
            Authentication authentication) {
        Post post = adminOpsService.moderatePostStatus(id, request.getStatus(), authentication.getName());
        return ApiResponse.success("帖子状态更新成功", post);
    }

    @PatchMapping("/comments/{id}/hide")
    @PreAuthorize("hasAnyRole('MODERATOR', 'ADMIN')")
    public ApiResponse<Comment> hideComment(@PathVariable Long id, Authentication authentication) {
        return ApiResponse.success("评论已隐藏", adminOpsService.hideComment(id, authentication.getName()));
    }

    @PatchMapping("/comments/{id}/restore")
    @PreAuthorize("hasAnyRole('MODERATOR', 'ADMIN')")
    public ApiResponse<Comment> restoreComment(@PathVariable Long id, Authentication authentication) {
        return ApiResponse.success("评论已恢复", adminOpsService.restoreComment(id, authentication.getName()));
    }

    @GetMapping("/users")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<Page<User>> listUsers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(adminOpsService.listUsers(pageable));
    }

    @PatchMapping("/users/{id}/ban")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<User> banUser(@PathVariable Long id, Authentication authentication) {
        return ApiResponse.success("用户已封禁", adminOpsService.banUser(id, authentication.getName()));
    }

    @PatchMapping("/users/{id}/unban")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<User> unbanUser(@PathVariable Long id, Authentication authentication) {
        return ApiResponse.success("用户已解除封禁", adminOpsService.unbanUser(id, authentication.getName()));
    }

    @PostMapping("/sections")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<Section> createSection(
            @Valid @RequestBody SectionManageRequest request,
            Authentication authentication) {
        return ApiResponse.success("版块创建成功", adminOpsService.createSection(request, authentication.getName()));
    }

    @PutMapping("/sections/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<Section> updateSection(
            @PathVariable Long id,
            @Valid @RequestBody SectionManageRequest request,
            Authentication authentication) {
        return ApiResponse.success("版块更新成功", adminOpsService.updateSection(id, request, authentication.getName()));
    }

    @DeleteMapping("/sections/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<Void> deleteSection(@PathVariable Long id, Authentication authentication) {
        adminOpsService.deleteSection(id, authentication.getName());
        return ApiResponse.success("版块删除成功", null);
    }

    @GetMapping("/logs")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<Page<OperationLog>> getLogs(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(adminOpsService.getLogs(pageable));
    }

    @GetMapping("/redemptions/pending")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<Page<RedemptionRequestResponse>> pendingRedemptions(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(growthDiscoveryService.pendingRedemptions(pageable)
                .map(RedemptionRequestResponse::from));
    }

    @GetMapping("/rewards")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<java.util.List<RewardItem>> listRewardItems() {
        return ApiResponse.success(growthDiscoveryService.listAllRewardsForAdmin());
    }

    @PostMapping("/rewards")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<RewardItem> createRewardItem(@Valid @RequestBody RewardItemManageRequest request) {
        return ApiResponse.success("积分商品已创建", growthDiscoveryService.createRewardItem(request));
    }

    @PutMapping("/rewards/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<RewardItem> updateRewardItem(
            @PathVariable Long id,
            @Valid @RequestBody RewardItemManageRequest request) {
        return ApiResponse.success("积分商品已更新", growthDiscoveryService.updateRewardItem(id, request));
    }

    @PatchMapping("/rewards/{id}/status")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<RewardItem> updateRewardStatus(
            @PathVariable Long id,
            @RequestParam Integer status) {
        String message = Integer.valueOf(1).equals(status) ? "积分商品已上架" : "积分商品已下架";
        return ApiResponse.success(message, growthDiscoveryService.updateRewardStatus(id, status == null ? -1 : status));
    }

    @PatchMapping("/redemptions/{id}/review")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<RedemptionRequestResponse> reviewRedemption(
            @PathVariable Long id,
            @RequestBody ReviewRedemptionRequest request) {
        boolean approve = Boolean.TRUE.equals(request.getApprove());
        String message = approve ? "兑换申请已通过" : "兑换申请已驳回";
        return ApiResponse.success(message,
                RedemptionRequestResponse.from(growthDiscoveryService.reviewRedemption(id, approve, request.getNote())));
    }

    @GetMapping("/reports/summary")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<java.util.Map<String, Object>> reportSummary() {
        return ApiResponse.success(growthDiscoveryService.reportSummary());
    }

    @GetMapping("/analytics")
    @PreAuthorize("hasAnyRole('MODERATOR', 'ADMIN')")
    public ApiResponse<java.util.Map<String, Object>> analytics(
            @RequestParam(defaultValue = "7") int days) {
        return ApiResponse.success(analyticsService.dashboard(days));
    }

    @GetMapping("/analytics/report")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<java.util.Map<String, Object>> analyticsReport() {
        return ApiResponse.success(analyticsService.dashboardReport());
    }

    @GetMapping("/recommendations/config")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<RecommendationConfig> getRecommendationConfig() {
        return ApiResponse.success(growthDiscoveryService.getRecommendationConfig());
    }

    @PutMapping("/recommendations/config")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<RecommendationConfig> updateRecommendationConfig(@Valid @RequestBody RecommendationConfigRequest request) {
        return ApiResponse.success("推荐策略已更新", growthDiscoveryService.updateRecommendationConfig(request));
    }

    @GetMapping("/recommendations/preview")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<RecommendationPreviewResponse> previewRecommendations(
            @RequestParam(required = false) String username,
            @RequestParam(defaultValue = "10") int size) {
        return ApiResponse.success(growthDiscoveryService.previewRecommendations(username, size));
    }
}
