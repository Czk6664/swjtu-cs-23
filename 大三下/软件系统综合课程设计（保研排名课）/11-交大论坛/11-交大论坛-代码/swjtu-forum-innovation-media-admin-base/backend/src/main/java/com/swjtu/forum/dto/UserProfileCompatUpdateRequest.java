package com.swjtu.forum.dto;

import jakarta.validation.constraints.Size;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.util.List;

@Data
@EqualsAndHashCode(callSuper = true)
public class UserProfileCompatUpdateRequest extends UserProfileUpdateRequest {

    @Size(max = 8, message = "最多选择 8 个校园身份标签")
    private List<String> interestTags;

    @Size(max = 8, message = "最多选择 8 个校园身份标签")
    private List<Long> tagIds;
}
