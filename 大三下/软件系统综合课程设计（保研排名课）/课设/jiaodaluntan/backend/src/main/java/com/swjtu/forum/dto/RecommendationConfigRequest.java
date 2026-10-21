package com.swjtu.forum.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class RecommendationConfigRequest {

    @NotNull(message = "兴趣标签权重不能为空")
    @Min(value = 0, message = "兴趣标签权重不能小于 0")
    @Max(value = 100, message = "兴趣标签权重不能大于 100")
    private Integer tagWeight;

    @NotNull(message = "互动热度权重不能为空")
    @Min(value = 0, message = "互动热度权重不能小于 0")
    @Max(value = 100, message = "互动热度权重不能大于 100")
    private Integer engagementWeight;

    @NotNull(message = "内容新鲜度权重不能为空")
    @Min(value = 0, message = "内容新鲜度权重不能小于 0")
    @Max(value = 100, message = "内容新鲜度权重不能大于 100")
    private Integer recencyWeight;

    @NotNull(message = "推荐说明开关不能为空")
    private Boolean explainabilityEnabled;
}
