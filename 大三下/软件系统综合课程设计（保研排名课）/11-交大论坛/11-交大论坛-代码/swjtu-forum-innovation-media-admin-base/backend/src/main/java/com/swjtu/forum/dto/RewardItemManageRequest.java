package com.swjtu.forum.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class RewardItemManageRequest {
    @NotBlank(message = "奖励名称不能为空")
    @Size(max = 100, message = "奖励名称不能超过 100 个字符")
    private String name;

    @Size(max = 500, message = "奖励说明不能超过 500 个字符")
    private String description;

    @Min(value = 1, message = "兑换积分至少为 1")
    private Integer costPoints;

    @Min(value = 0, message = "库存不能小于 0")
    private Integer stock;

    private Integer status;
}
