package com.swjtu.forum.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class PostModerationRequest {

    @NotNull(message = "审核状态不能为空")
    private Integer status;
}
