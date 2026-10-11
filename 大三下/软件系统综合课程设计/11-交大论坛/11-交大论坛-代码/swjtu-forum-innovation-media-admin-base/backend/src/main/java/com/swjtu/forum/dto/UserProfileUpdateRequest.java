package com.swjtu.forum.dto;

import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class UserProfileUpdateRequest {

    @Size(max = 500, message = "头像链接长度不能超过 500 个字符")
    private String avatar;

    @Size(max = 500, message = "个人简介长度不能超过 500 个字符")
    private String bio;

    @Size(max = 50, message = "学院长度不能超过 50 个字符")
    private String college;

    @Size(max = 50, message = "专业长度不能超过 50 个字符")
    private String major;

    @Size(max = 20, message = "学号长度不能超过 20 个字符")
    private String studentId;
}