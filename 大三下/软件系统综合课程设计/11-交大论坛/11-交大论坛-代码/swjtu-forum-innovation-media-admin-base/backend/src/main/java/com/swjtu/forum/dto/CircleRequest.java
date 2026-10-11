package com.swjtu.forum.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class CircleRequest {
    @NotBlank(message = "圈子名称不能为空")
    @Size(max = 80, message = "圈子名称不能超过 80 个字符")
    private String name;

    @NotBlank(message = "圈子简介不能为空")
    @Size(max = 500, message = "圈子简介不能超过 500 个字符")
    private String description;

    @Size(max = 100, message = "圈子图标不能超过 100 个字符")
    private String icon;
}
