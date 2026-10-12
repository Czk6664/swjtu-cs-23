package com.swjtu.forum.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class ReviewReportRequest {

    @NotNull(message = "处理结果不能为空")
    private Boolean accept;

    @Size(max = 300, message = "处理备注长度不能超过 300 个字符")
    private String reviewNote;
}
