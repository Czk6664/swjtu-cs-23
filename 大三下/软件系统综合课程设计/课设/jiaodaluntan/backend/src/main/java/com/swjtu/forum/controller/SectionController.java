package com.swjtu.forum.controller;

import com.swjtu.forum.dto.ApiResponse;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.repository.SectionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/sections")
@RequiredArgsConstructor
public class SectionController {

    private final SectionRepository sectionRepository;

    @GetMapping
    public ApiResponse<List<Section>> getSections() {
        return ApiResponse.success(sectionRepository.findAllByOrderBySortOrderAsc());
    }
}
