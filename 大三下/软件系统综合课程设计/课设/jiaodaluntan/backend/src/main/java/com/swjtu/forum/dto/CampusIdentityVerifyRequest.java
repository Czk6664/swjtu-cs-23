package com.swjtu.forum.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

@Data
public class CampusIdentityVerifyRequest {

    @NotBlank(message = "校园邮箱不能为空")
    @Email(message = "校园邮箱格式不正确")
    @Pattern(regexp = ".+@swjtu\\.edu\\.cn$", message = "请输入西南交通大学校园邮箱")
    private String campusEmail;

    @NotBlank(message = "学号不能为空")
    @Pattern(regexp = "\\d{8}", message = "学号必须为 8 位数字")
    private String studentId;
}
