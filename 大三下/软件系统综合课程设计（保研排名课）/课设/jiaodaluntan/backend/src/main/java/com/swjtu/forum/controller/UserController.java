package com.swjtu.forum.controller;

import com.swjtu.forum.dto.ApiResponse;
import com.swjtu.forum.dto.CampusIdentityVerificationResult;
import com.swjtu.forum.dto.CampusIdentityVerifyRequest;
import com.swjtu.forum.dto.UserProfileUpdateRequest;
import com.swjtu.forum.dto.UserProfileCompatUpdateRequest;
import com.swjtu.forum.dto.UserTagsUpdateRequest;
import com.swjtu.forum.entity.Tag;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.entity.UserFollow;
import com.swjtu.forum.service.FollowService;
import com.swjtu.forum.service.UserService;
import com.swjtu.forum.util.Pageables;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;
    private final FollowService followService;

    @Value("${app.upload.dir:uploads}")
    private String uploadDir;

    @GetMapping("/{id}")
    public ApiResponse<Map<String, Object>> getPublicProfile(@PathVariable Long id) {
        return ApiResponse.success(userService.getPublicProfile(id));
    }

    @PostMapping("/me/avatar")
    public ApiResponse<Map<String, String>> uploadAvatar(
            @RequestParam("file") MultipartFile file,
            Authentication authentication) {
        try {
            if (file.isEmpty()) {
                return ApiResponse.error(400, "请选择一张图片");
            }

            String contentType = file.getContentType();
            if (contentType == null || !contentType.startsWith("image/")) {
                return ApiResponse.error(400, "仅支持图片格式");
            }

            if (file.getSize() > 5 * 1024 * 1024) {
                return ApiResponse.error(400, "图片大小不能超过 5MB");
            }

            String ext = switch (contentType) {
                case "image/png" -> ".png";
                case "image/gif" -> ".gif";
                case "image/webp" -> ".webp";
                default -> ".jpg";
            };
            String filename = UUID.randomUUID().toString().replace("-", "") + ext;

            Path avatarDir = Paths.get(uploadDir, "avatars").toAbsolutePath();
            Files.createDirectories(avatarDir);
            Path target = avatarDir.resolve(filename);
            Files.copy(file.getInputStream(), target);

            String url = "/uploads/avatars/" + filename;

            User user = userService.getUserByUsername(authentication.getName());
            user.setAvatar(url);
            userService.saveUser(user);

            return ApiResponse.success("头像上传成功", Map.of("url", url));
        } catch (Exception e) {
            return ApiResponse.error(500, "上传失败: " + e.getMessage());
        }
    }

    @PutMapping("/me")
    public ApiResponse<User> updateCurrentUser(
            @Valid @RequestBody UserProfileUpdateRequest request,
            Authentication authentication) {
        return ApiResponse.success("资料更新成功", userService.updateCurrentUser(authentication.getName(), request));
    }

    @PutMapping("/me/profile")
    public ApiResponse<Map<String, Object>> updateCurrentUserProfile(
            @Valid @RequestBody UserProfileCompatUpdateRequest request,
            Authentication authentication) {
        User user = userService.updateCurrentUserProfile(authentication.getName(), request);
        Set<Tag> tags = request.getTagIds() != null
                ? userService.updateCurrentUserTags(authentication.getName(), request.getTagIds())
                : userService.updateCurrentUserTagsByNames(authentication.getName(), request.getInterestTags());
        return ApiResponse.success("资料更新成功", Map.of("user", user, "interestTags", tags));
    }

    @GetMapping("/me/tags")
    public ApiResponse<Set<Tag>> currentUserTags(Authentication authentication) {
        return ApiResponse.success(userService.getCurrentUserTags(authentication.getName()));
    }

    @PutMapping("/me/tags")
    public ApiResponse<Set<Tag>> updateCurrentUserTags(
            @RequestBody UserTagsUpdateRequest request,
            Authentication authentication) {
        return ApiResponse.success("校园身份标签已保存",
                userService.updateCurrentUserTags(authentication.getName(), request.getTagIds()));
    }

    @PutMapping("/me/campus-identity")
    public ApiResponse<CampusIdentityVerificationResult> verifyCampusIdentity(
            @Valid @RequestBody CampusIdentityVerifyRequest request,
            Authentication authentication) {
        CampusIdentityVerificationResult result = userService.verifyCampusIdentity(authentication.getName(), request);
        if (result.isVerified()) {
            return ApiResponse.success("校园身份认证成功", result);
        }
        return ApiResponse.error(400, result.getMessage());
    }

    @PostMapping("/{id}/follow")
    public ApiResponse<Map<String, Object>> follow(@PathVariable Long id, Authentication authentication) {
        return ApiResponse.success("已关注", followService.follow(id, authentication.getName()));
    }

    @DeleteMapping("/{id}/follow")
    public ApiResponse<Map<String, Object>> unfollow(@PathVariable Long id, Authentication authentication) {
        return ApiResponse.success("已取消关注", followService.unfollow(id, authentication.getName()));
    }

    @GetMapping("/{id}/follow-stats")
    public ApiResponse<Map<String, Object>> followStats(@PathVariable Long id, Authentication authentication) {
        String username = authentication != null ? authentication.getName() : null;
        return ApiResponse.success(followService.followStats(id, username));
    }

    @GetMapping("/me/following")
    public ApiResponse<Page<UserFollow>> following(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            Authentication authentication) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(followService.following(authentication.getName(), pageable));
    }

    @GetMapping("/me/followers")
    public ApiResponse<Page<UserFollow>> followers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            Authentication authentication) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(followService.followers(authentication.getName(), pageable));
    }
}
