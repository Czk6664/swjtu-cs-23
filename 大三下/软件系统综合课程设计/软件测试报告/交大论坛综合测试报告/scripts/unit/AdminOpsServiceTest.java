package com.swjtu.forum.service;

import com.swjtu.forum.entity.OperationLog;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.exception.ApiException;
import com.swjtu.forum.exception.NotFoundException;
import com.swjtu.forum.repository.CommentRepository;
import com.swjtu.forum.repository.OperationLogRepository;
import com.swjtu.forum.repository.PostRepository;
import com.swjtu.forum.repository.SectionRepository;
import com.swjtu.forum.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
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
    void banUserRejectsMissingUser() {
        when(userRepository.findById(404L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> adminOpsService.banUser(404L, "admin"))
                .isInstanceOf(NotFoundException.class)
                .hasMessage("用户不存在");

        verify(userRepository, never()).save(any(User.class));
        verify(operationLogRepository, never()).save(any(OperationLog.class));
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

    @Test
    void banUserDisablesTargetAndWritesOperationLog() {
        User target = new User();
        target.setId(2L);
        target.setUsername("target");
        target.setRole("USER");
        target.setEnabled(true);

        User operator = new User();
        operator.setId(9L);
        operator.setUsername("admin");
        operator.setRole("ADMIN");
        operator.setEnabled(true);

        when(userRepository.findById(2L)).thenReturn(Optional.of(target));
        when(userRepository.save(target)).thenAnswer(invocation -> invocation.getArgument(0));
        when(userService.getUserByUsername("admin")).thenReturn(operator);

        User saved = adminOpsService.banUser(2L, "admin");

        assertThat(saved.getEnabled()).isFalse();
        verify(userRepository).save(target);

        ArgumentCaptor<OperationLog> logCaptor = ArgumentCaptor.forClass(OperationLog.class);
        verify(operationLogRepository).save(logCaptor.capture());
        assertThat(logCaptor.getValue().getActor()).isEqualTo(operator);
        assertThat(logCaptor.getValue().getAction()).isEqualTo("BAN_USER");
        assertThat(logCaptor.getValue().getTargetType()).isEqualTo("USER");
        assertThat(logCaptor.getValue().getTargetId()).isEqualTo(2L);
    }
}
