package com.swjtu.forum.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.swjtu.forum.dto.ApiResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.InsufficientAuthenticationException;

import static org.assertj.core.api.Assertions.assertThat;

class SecurityContractTest {

    private final ObjectMapper objectMapper = new ObjectMapper();

    private RestAuthenticationEntryPoint authenticationEntryPoint;
    private RestAccessDeniedHandler accessDeniedHandler;

    @BeforeEach
    void setUp() {
        authenticationEntryPoint = new RestAuthenticationEntryPoint(objectMapper);
        accessDeniedHandler = new RestAccessDeniedHandler(objectMapper);
    }

    @Test
    void unauthenticatedRequestsReturn401JsonContract() throws Exception {
        MockHttpServletResponse response = new MockHttpServletResponse();

        authenticationEntryPoint.commence(
                new MockHttpServletRequest(),
                response,
                new InsufficientAuthenticationException("missing token")
        );

        ApiResponse<?> body = objectMapper.readValue(response.getContentAsString(), ApiResponse.class);
        assertThat(response.getStatus()).isEqualTo(401);
        assertThat(body.getCode()).isEqualTo(401);
        assertThat(body.getMessage()).isEqualTo("请先登录");
    }

    @Test
    void forbiddenRequestsReturn403JsonContract() throws Exception {
        MockHttpServletResponse response = new MockHttpServletResponse();

        accessDeniedHandler.handle(
                new MockHttpServletRequest(),
                response,
                new AccessDeniedException("forbidden")
        );

        ApiResponse<?> body = objectMapper.readValue(response.getContentAsString(), ApiResponse.class);
        assertThat(response.getStatus()).isEqualTo(403);
        assertThat(body.getCode()).isEqualTo(403);
        assertThat(body.getMessage()).isEqualTo("无权执行该操作");
    }
}