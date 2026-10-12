package com.swjtu.forum.dto;

import lombok.Data;

import java.util.List;

@Data
public class UserTagsUpdateRequest {
    private List<Long> tagIds;
}
