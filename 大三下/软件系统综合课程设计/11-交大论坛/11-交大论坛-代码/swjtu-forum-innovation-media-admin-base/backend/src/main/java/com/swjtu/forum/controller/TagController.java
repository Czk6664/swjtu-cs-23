package com.swjtu.forum.controller;

import com.swjtu.forum.dto.ApiResponse;
import com.swjtu.forum.entity.Tag;
import com.swjtu.forum.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/tags")
@RequiredArgsConstructor
public class TagController {

    private final UserService userService;

    @GetMapping("/interests")
    public ApiResponse<List<Tag>> listInterestTags() {
        return ApiResponse.success(userService.listInterestTags());
    }
}
