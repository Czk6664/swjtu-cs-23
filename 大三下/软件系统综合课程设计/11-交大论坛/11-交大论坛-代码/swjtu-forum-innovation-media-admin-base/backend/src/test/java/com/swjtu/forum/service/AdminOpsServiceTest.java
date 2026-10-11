package com.swjtu.forum.service;

import com.swjtu.forum.entity.User;
import com.swjtu.forum.exception.ApiException;
import com.swjtu.forum.repository.CommentRepository;
import com.swjtu.forum.repository.OperationLogRepository;
import com.swjtu.forum.repository.PostRepository;
import com.swjtu.forum.repository.SectionRepository;
import com.swjtu.forum.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AdminOpsServiceTest {

    @Mock
    private PostRepository postRepository;
    @Mock
    private CommentRepository commentRepository;
    @Mock
    private SectionRepository sectionRepository;
    @Mock
    private UserRepository userRepository;
    @Mock
    private OperationLogRepository operationLogRepository;
    @Mock
    private UserService userService;
    @Mock
    private PostService postService;

    private AdminOpsService adminOpsService;

    @BeforeEach
    void setUp() {
        adminOpsService = new AdminOpsService(
                postRepository,
                commentRepository,
                sectionRepository,
                userRepository,
                operationLogRepository,
                userService,
                postService
        );
    }

    @Test
    void banUserRejectsLastEnabledAdmin() {
        User admin = new User();
        admin.setId(1L);
        admin.setUsername("admin");
        admin.setRole("ADMIN");
        admin.setEnabled(true);

        when(userRepository.findById(1L)).thenReturn(Optional.of(admin));
        when(userRepository.countByRoleAndEnabledTrue("ADMIN")).thenReturn(1L);

        assertThatThrownBy(() -> adminOpsService.banUser(1L, "admin"))
                .isInstanceOf(ApiException.class)
                .hasMessage("至少需要保留一个可用管理员账号");

        verify(userRepository, never()).save(admin);
    }
}
