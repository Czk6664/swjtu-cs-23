package com.swjtu.forum.dto;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.util.List;

@Data
public class BulkReviewReportRequest {

    @NotEmpty(message = "批量处理的举报不能为空")
    private List<Long> reportIds;

    @NotNull(message = "处理结果不能为空")
    private Boolean accept;

    @Size(max = 300, message = "处理备注长度不能超过 300 个字符")
    private String reviewNote;
}
