package com.swjtu.forum.dto;

import lombok.Data;

import java.util.List;

@Data
public class InterestTagsRequest {
    private List<String> tags;
}
