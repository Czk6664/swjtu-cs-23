package com.swjtu.forum.dto;

import lombok.Data;

@Data
public class ReviewRedemptionRequest {
    private Boolean approve;
    private String note;
}
