package com.swjtu.forum.dto;

import com.swjtu.forum.entity.User;
import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class CampusIdentityVerificationResult {

    private boolean verified;
    private String status;
    private String message;
    private User user;
}
