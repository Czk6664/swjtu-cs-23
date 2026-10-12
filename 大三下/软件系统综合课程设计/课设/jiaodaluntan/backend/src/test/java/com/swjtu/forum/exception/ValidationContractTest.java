package com.swjtu.forum.exception;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.swjtu.forum.dto.ApiResponse;
import com.swjtu.forum.dto.PostRequest;
import com.swjtu.forum.dto.UserProfileUpdateRequest;
import jakarta.validation.Valid;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class ValidationContractTest {

    private final ObjectMapper objectMapper = new ObjectMapper();
    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        LocalValidatorFactoryBean validator = new LocalValidatorFactoryBean();
        validator.afterPropertiesSet();
        mockMvc = MockMvcBuilders.standaloneSetup(new DummyValidationController())
                .setControllerAdvice(new GlobalExceptionHandler())
                .setValidator(validator)
                .build();
    }

    @Test
    void invalidPostRequestReturns400WithExplicitMessage() throws Exception {
        PostRequest request = new PostRequest();
        request.setTitle("x".repeat(201));
        request.setContent("正文");
        request.setSectionId(1L);

        mockMvc.perform(post("/posts")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value(400))
                .andExpect(jsonPath("$.message").value("标题长度不能超过 200 个字符"));
    }

    @Test
    void invalidProfileRequestReturns400WithExplicitMessage() throws Exception {
        UserProfileUpdateRequest request = new UserProfileUpdateRequest();
        request.setBio("x".repeat(501));

        mockMvc.perform(put("/users/me")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value(400))
                .andExpect(jsonPath("$.message").value("个人简介长度不能超过 500 个字符"));
    }

    @RestController
    static class DummyValidationController {

        @PostMapping("/posts")
        public ApiResponse<String> create(@Valid @RequestBody PostRequest request) {
            return ApiResponse.success("ok");
        }

        @PutMapping("/users/me")
        public ApiResponse<String> update(@Valid @RequestBody UserProfileUpdateRequest request) {
            return ApiResponse.success("ok");
        }
    }
}