package com.swjtu.forum.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.util.List;

@Data
public class PostRequest {

    @NotBlank(message = "标题不能为空")
    @Size(max = 200, message = "标题长度不能超过 200 个字符")
    private String title;

    @NotBlank(message = "正文不能为空")
    @Size(max = 10000, message = "正文长度不能超过 10000 个字符")
    private String content;

    @NotNull(message = "版块不能为空")
    private Long sectionId;

    @Size(max = 500, message = "封面链接长度不能超过 500 个字符")
    private String coverImage;

    @Size(max = 9, message = "帖子图片最多上传 9 张")
    private List<String> imageUrls;

    private Long circleId;

    private List<String> tags;
}
