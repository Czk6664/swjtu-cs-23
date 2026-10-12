package com.swjtu.forum.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class SectionManageRequest {
    @NotBlank(message = "版块名称不能为空")
    @Size(max = 50, message = "版块名称不能超过 50 个字符")
    private String name;

    @Size(max = 200, message = "版块描述不能超过 200 个字符")
    private String description;

    @Size(max = 200, message = "图标地址不能超过 200 个字符")
    private String icon;

    private Integer sortOrder;

    private Long moderatorId;
}
