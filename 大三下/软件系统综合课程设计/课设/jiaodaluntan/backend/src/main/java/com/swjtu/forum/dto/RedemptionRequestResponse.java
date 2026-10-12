package com.swjtu.forum.dto;

import com.swjtu.forum.entity.RedemptionRequest;
import com.swjtu.forum.entity.RewardItem;
import com.swjtu.forum.entity.User;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class RedemptionRequestResponse {
    private Long id;
    private Long userId;
    private String username;
    private RewardSummary reward;
    private Integer pointsCost;
    private Integer status;
    private String statusText;
    private String reviewNote;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public static RedemptionRequestResponse from(RedemptionRequest request) {
        if (request == null) {
            return null;
        }
        User user = request.getUser();
        RewardItem reward = request.getReward();
        return RedemptionRequestResponse.builder()
                .id(request.getId())
                .userId(user == null ? null : user.getId())
                .username(user == null ? null : user.getUsername())
                .reward(RewardSummary.from(reward))
                .pointsCost(request.getPointsCost())
                .status(request.getStatus())
                .statusText(statusText(request.getStatus()))
                .reviewNote(request.getReviewNote())
                .createdAt(request.getCreatedAt())
                .updatedAt(request.getUpdatedAt())
                .build();
    }

    private static String statusText(Integer status) {
        if (status == null) {
            return "未知";
        }
        return switch (status) {
            case 0 -> "待审核";
            case 1 -> "已通过";
            case 2 -> "已驳回";
            default -> "未知";
        };
    }

    @Data
    @Builder
    public static class RewardSummary {
        private Long id;
        private String name;
        private String description;
        private Integer costPoints;

        public static RewardSummary from(RewardItem reward) {
            if (reward == null) {
                return null;
            }
            return RewardSummary.builder()
                    .id(reward.getId())
                    .name(reward.getName())
                    .description(reward.getDescription())
                    .costPoints(reward.getCostPoints())
                    .build();
        }
    }
}
