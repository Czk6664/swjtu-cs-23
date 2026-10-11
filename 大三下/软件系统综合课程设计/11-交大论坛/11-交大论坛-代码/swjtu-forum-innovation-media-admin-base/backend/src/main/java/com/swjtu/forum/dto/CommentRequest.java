package com.swjtu.forum.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class CommentRequest {

    @NotBlank(message = "评论内容不能为空")
    @Size(max = 2000, message = "评论长度不能超过 2000 个字符")
    private String content;

    /** Optional id of the comment being replied to; null for a top-level comment. */
    private Long parentId;
}