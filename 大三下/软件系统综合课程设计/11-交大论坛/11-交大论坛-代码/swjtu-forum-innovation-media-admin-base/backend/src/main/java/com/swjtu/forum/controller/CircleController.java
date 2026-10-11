package com.swjtu.forum.controller;

import com.swjtu.forum.dto.ApiResponse;
import com.swjtu.forum.dto.CircleRequest;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.service.CircleService;
import com.swjtu.forum.util.Pageables;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/circles")
@RequiredArgsConstructor
public class CircleController {

    private final CircleService circleService;

    @GetMapping
    public ApiResponse<List<Map<String, Object>>> list(Authentication authentication) {
        String username = authentication == null ? null : authentication.getName();
        return ApiResponse.success(circleService.listCircles(username));
    }

    @GetMapping("/{id}")
    public ApiResponse<Map<String, Object>> detail(@PathVariable Long id, Authentication authentication) {
        String username = authentication == null ? null : authentication.getName();
        return ApiResponse.success(circleService.getCircle(id, username));
    }

    @PostMapping
    public ApiResponse<Map<String, Object>> create(@Valid @RequestBody CircleRequest request, Authentication authentication) {
        return ApiResponse.success("圈子创建成功", circleService.createCircle(request, authentication.getName()));
    }

    @PostMapping("/{id}/join")
    public ApiResponse<Map<String, Object>> join(@PathVariable Long id, Authentication authentication) {
        return ApiResponse.success("已加入圈子", circleService.joinCircle(id, authentication.getName()));
    }

    @DeleteMapping("/{id}/join")
    public ApiResponse<Map<String, Object>> leave(@PathVariable Long id, Authentication authentication) {
        return ApiResponse.success("已退出圈子", circleService.leaveCircle(id, authentication.getName()));
    }

    @GetMapping("/{id}/posts")
    public ApiResponse<Page<Post>> posts(
            @PathVariable Long id,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = Pageables.of(page, size);
        return ApiResponse.success(circleService.circlePosts(id, pageable));
    }
}
