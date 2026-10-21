package com.swjtu.forum.service;

import com.swjtu.forum.dto.CommentRequest;
import com.swjtu.forum.dto.PostRequest;
import com.swjtu.forum.exception.ApiException;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.List;

@Service
public class ContentModerationService {

    private static final List<String> SENSITIVE_WORDS = List.of(
            "赌博",
            "色情",
            "刷单",
            "代写",
            "作弊器"
    );

    public boolean shouldReview(PostRequest request) {
        validatePostRequest(request);
        return containsSensitiveWord(request.getTitle()) || containsSensitiveWord(request.getContent());
    }

    public void validateCommentRequest(CommentRequest request) {
        if (containsSensitiveWord(request.getContent())) {
            throw new ApiException(400, "评论内容包含敏感词，请修改后再提交");
        }
    }

    public void validatePostRequest(PostRequest request) {
        if (request.getTags() != null && request.getTags().size() > 5) {
            throw new ApiException(400, "标签数量不能超过 5 个");
        }

        if (request.getTags() != null) {
            for (String tag : request.getTags()) {
                if (!StringUtils.hasText(tag)) {
                    throw new ApiException(400, "标签不能为空");
                }
                if (tag.trim().length() > 20) {
                    throw new ApiException(400, "标签长度不能超过 20 个字符");
                }
            }
        }
    }

    private boolean containsSensitiveWord(String content) {
        if (!StringUtils.hasText(content)) {
            return false;
        }

        return SENSITIVE_WORDS.stream().anyMatch(content::contains);
    }
}
