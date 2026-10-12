package com.swjtu.forum.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class CreateReportRequest {

    @NotBlank(message = "举报原因不能为空")
    @Size(max = 32, message = "举报原因长度不能超过 32 个字符")
    private String reason;

    @Size(max = 300, message = "补充说明长度不能超过 300 个字符")
    private String detail;
}
