package com.swjtu.forum.dto;

import com.swjtu.forum.entity.Post;
import lombok.Data;

import java.util.List;

@Data
public class RecommendationPreviewResponse {
    private String viewerUsername;
    private List<String> interestTags;
    private List<Post> posts;
}
