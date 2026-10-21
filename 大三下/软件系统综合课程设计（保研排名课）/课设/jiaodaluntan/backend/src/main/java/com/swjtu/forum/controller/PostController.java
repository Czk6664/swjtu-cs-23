package com.swjtu.forum.controller;

import com.swjtu.forum.dto.ApiResponse;
import com.swjtu.forum.dto.CommentRequest;
import com.swjtu.forum.dto.CreateReportRequest;
import com.swjtu.forum.dto.PostModerationRequest;
import com.swjtu.forum.dto.PostRequest;
import com.swjtu.forum.entity.Comment;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.Report;
import com.swjtu.forum.service.AnalyticsService;
import com.swjtu.forum.service.GrowthDiscoveryService;
import com.swjtu.forum.service.PostService;
import com.swjtu.forum.service.ReportService;
import com.swjtu.forum.util.Pageables;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/posts")
@RequiredArgsConstructor
public class PostController {

    private final PostService postService;
    private final GrowthDiscoveryService growthDiscoveryService;
    private final ReportService reportService;
    private final AnalyticsService analyticsService;

    @Value("${app.upload.dir:uploads}")
    private String uploadDir;

    @PostMapping("/image")
    public ApiResponse<Map<String, String>> uploadPostImage(@RequestParam("file") MultipartFile file) {
        try {
            if (file.isEmpty()) {
                return ApiResponse.error(400, "请选择一张图片");
            }

            if (file.getSize() > 8 * 1024 * 1024) {
                return ApiResponse.error(400, "图片大小不能超过 8MB");
            }

            String contentType = String.valueOf(file.getContentType()).toLowerCase(Locale.ROOT);
            String ext = switch (contentType) {
                case "image/jpeg", "image/jpg" -> ".jpg";
                case "image/png" -> ".png";
                default -> null;
            };
            if (ext == null) {
                return ApiResponse.error(400, "仅支持 PNG、JPG 图片");
            }

            String filename = UUID.randomUUID().toString().replace("-", "") + ext;
            Path postImageDir = Paths.get(uploadDir, "posts").toAbsolutePath().normalize();
            Files.createDirectories(postImageDir);
            Path target = postImageDir.resolve(filename).normalize();
            Files.copy(file.getInputStream(), target, StandardCopyOption.REPLACE_EXISTING);

            return ApiResponse.success("图片上传成功", Map.of("url", "/uploads/posts/" + filename));
        } catch (Exception e) {
            return ApiResponse.error(500, "图片上传失败: " + e.getMessage());
        }
    }

    @PostMapping
    public ApiResponse<Post> createPost(
            @Valid @RequestBody PostRequest request,
            Authentication authentication) {
        Post post = postService.createPost(request, authentication.getName());
        String message = post.getStatus() == PostService.STATUS_PENDING ? "帖子已提交，等待审核" : "发布成功";
        return ApiResponse.success(message, post);
    }

    @GetMapping
    public ApiResponse<Page<Post>> getPosts(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) Long sectionId) {
        Pageable pageable = Pageables.of(page, size);
        Page<Post> posts = sectionId == null
                ? postService.getPosts(pageable)
                : postService.getPostsBySection(sectionId, pageable);
        return ApiResponse.success(posts);
    }

    @GetMapping("/hot")
    public ApiResponse<Page<Post>> getHotPosts(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(postService.getHotPosts(pageable));
    }

    @GetMapping("/search")
    public ApiResponse<Page<Post>> searchPosts(
            @RequestParam String keyword,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(growthDiscoveryService.searchPosts(keyword, pageable));
    }

    @GetMapping("/trending-tags")
    public ApiResponse<java.util.List<Map<String, Object>>> trendingTags() {
        return ApiResponse.success(analyticsService.trendingTags());
    }

    @GetMapping("/hot-today")
    public ApiResponse<java.util.List<Map<String, Object>>> hotToday() {
        java.util.List<Map<String, Object>> today = analyticsService.hotPostsToday();
        return ApiResponse.success(today.isEmpty() ? analyticsService.hotPosts() : today);
    }

    @GetMapping("/recommend")
    public ApiResponse<Page<Post>> recommendPosts(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            Authentication authentication) {
        Pageable pageable = Pageables.of(page, size);
        if (authentication == null) {
            return ApiResponse.success(postService.getHotPosts(pageable));
        }
        return ApiResponse.success(growthDiscoveryService.recommendPosts(authentication.getName(), pageable));
    }

    @GetMapping("/mine")
    public ApiResponse<Page<Post>> getMyPosts(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            Authentication authentication) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(postService.getMyPosts(authentication.getName(), pageable));
    }

    @GetMapping("/by-user/{userId}")
    public ApiResponse<Page<Post>> getPublishedPostsByUser(
            @PathVariable Long userId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(postService.getPublishedPostsByUser(userId, pageable));
    }

    @GetMapping("/favorites")
    public ApiResponse<Page<Post>> getMyFavorites(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            Authentication authentication) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(postService.getMyFavoritePosts(authentication.getName(), pageable));
    }

    @GetMapping("/history")
    public ApiResponse<Page<Post>> getMyHistory(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            Authentication authentication) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(postService.getMyBrowseHistory(authentication.getName(), pageable));
    }

    @GetMapping("/mine/{id}")
    public ApiResponse<Post> getOwnedPost(@PathVariable Long id, Authentication authentication) {
        return ApiResponse.success(postService.getOwnedPost(authentication.getName(), id));
    }

    @PutMapping("/mine/{id}")
    public ApiResponse<Post> updateOwnedPost(
            @PathVariable Long id,
            @Valid @RequestBody PostRequest request,
            Authentication authentication) {
        Post post = postService.updateOwnedPost(id, request, authentication.getName());
        String message = post.getStatus() == PostService.STATUS_PENDING ? "帖子已更新，等待审核" : "帖子更新成功";
        return ApiResponse.success(message, post);
    }

    @PatchMapping("/mine/{id}/withdraw")
    public ApiResponse<Post> withdrawOwnedPost(@PathVariable Long id, Authentication authentication) {
        return ApiResponse.success("帖子已撤回，不再公开展示", postService.withdrawOwnedPost(id, authentication.getName()));
    }

    @GetMapping("/{id}")
    public ApiResponse<Post> getPost(@PathVariable Long id, Authentication authentication) {
        String username = authentication != null ? authentication.getName() : null;
        return ApiResponse.success(postService.getPostById(id, username));
    }

    @PostMapping("/{id}/like")
    public ApiResponse<Map<String, Object>> togglePostLike(@PathVariable Long id, Authentication authentication) {
        PostService.InteractionResult result = postService.togglePostLike(id, authentication.getName());
        String message = result.active() ? "点赞成功" : "已取消点赞";
        return ApiResponse.success(message, Map.of("liked", result.active(), "likeCount", result.count()));
    }

    @PostMapping("/{id}/favorite")
    public ApiResponse<Map<String, Object>> togglePostFavorite(@PathVariable Long id, Authentication authentication) {
        PostService.InteractionResult result = postService.togglePostFavorite(id, authentication.getName());
        String message = result.active() ? "收藏成功" : "已取消收藏";
        return ApiResponse.success(message, Map.of("favorited", result.active(), "collectCount", result.count()));
    }

    @PostMapping("/{id}/report")
    public ApiResponse<Report> createReport(
            @PathVariable Long id,
            @Valid @RequestBody CreateReportRequest request,
            Authentication authentication) {
        return ApiResponse.success("举报已提交", reportService.createPostReport(id, request, authentication.getName()));
    }

    @PostMapping("/{id}/not-interested")
    public ApiResponse<Void> notInterested(@PathVariable Long id, Authentication authentication) {
        growthDiscoveryService.markNotInterested(id, authentication.getName());
        return ApiResponse.success("已标记不感兴趣", null);
    }

    @PostMapping("/comments/{id}/like")
    public ApiResponse<Map<String, Object>> toggleCommentLike(@PathVariable Long id, Authentication authentication) {
        PostService.InteractionResult result = postService.toggleCommentLike(id, authentication.getName());
        String message = result.active() ? "评论点赞成功" : "已取消评论点赞";
        return ApiResponse.success(message, Map.of("liked", result.active(), "likeCount", result.count()));
    }

    @GetMapping("/{id}/comments")
    public ApiResponse<Page<Comment>> getComments(
            @PathVariable Long id,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            Authentication authentication) {
        Pageable pageable = Pageables.of(page, size);
        String username = authentication != null ? authentication.getName() : null;
        return ApiResponse.success(postService.getComments(id, pageable, username));
    }

    @GetMapping("/comments/{id}/replies")
    public ApiResponse<java.util.List<Comment>> getReplies(@PathVariable Long id, Authentication authentication) {
        String username = authentication != null ? authentication.getName() : null;
        return ApiResponse.success(postService.getReplies(id, username));
    }

    @PostMapping("/{id}/comments")
    public ApiResponse<Comment> createComment(
            @PathVariable Long id,
            @Valid @RequestBody CommentRequest request,
            Authentication authentication) {
        Comment comment = postService.createComment(id, request, authentication.getName());
        return ApiResponse.success("评论成功", comment);
    }

    @PostMapping("/{postId}/comments/{commentId}/accept")
    public ApiResponse<Comment> acceptComment(
            @PathVariable Long postId,
            @PathVariable Long commentId,
            Authentication authentication) {
        return ApiResponse.success("已采纳最佳答案", postService.acceptComment(postId, commentId, authentication.getName()));
    }

    @DeleteMapping("/{postId}/comments/{commentId}/accept")
    public ApiResponse<Comment> cancelAcceptedComment(
            @PathVariable Long postId,
            @PathVariable Long commentId,
            Authentication authentication) {
        return ApiResponse.success("已取消采纳", postService.cancelAcceptedComment(postId, commentId, authentication.getName()));
    }

    @PatchMapping("/{id}/status")
    @PreAuthorize("hasAnyRole('MODERATOR', 'ADMIN')")
    public ApiResponse<Post> updatePostStatus(
            @PathVariable Long id,
            @Valid @RequestBody PostModerationRequest request,
            Authentication authentication) {
        return ApiResponse.success("状态更新成功", postService.updatePostStatus(id, request.getStatus(), authentication.getName()));
    }
}
