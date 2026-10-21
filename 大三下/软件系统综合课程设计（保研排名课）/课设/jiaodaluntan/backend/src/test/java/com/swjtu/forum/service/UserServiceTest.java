package com.swjtu.forum.service;

import com.swjtu.forum.dto.CampusIdentityVerificationResult;
import com.swjtu.forum.dto.CampusIdentityVerifyRequest;
import com.swjtu.forum.dto.LoginRequest;
import com.swjtu.forum.dto.RegisterRequest;
import com.swjtu.forum.dto.UserProfileUpdateRequest;
import com.swjtu.forum.entity.Tag;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.repository.TagRepository;
import com.swjtu.forum.repository.UserRepository;
import com.swjtu.forum.security.JwtUtil;
import com.swjtu.forum.security.LoginAttemptService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private TagRepository tagRepository;

    private UserService userService;
    private StubJwtUtil jwtUtil;
    private User user;

    @BeforeEach
    void setUp() {
        jwtUtil = new StubJwtUtil();
        userService = new UserService(userRepository, passwordEncoder, jwtUtil, new LoginAttemptService(), null, tagRepository);

        user = new User();
        user.setId(1L);
        user.setUsername("alice");
        user.setPassword("encoded-password");
        user.setEmail("alice@example.com");
        user.setEnabled(true);
    }

    @Test
    void registerReturnsDirectActivationMetadataAndEnabledUser() {
        RegisterRequest request = new RegisterRequest();
        request.setUsername("alice");
        request.setPassword("password");
        request.setEmail("alice@example.com");
        request.setStudentId("20240001");
        request.setCollege("Computer");
        request.setMajor("Software");

        when(userRepository.existsByUsername("alice")).thenReturn(false);
        when(userRepository.existsByEmail("alice@example.com")).thenReturn(false);
        when(passwordEncoder.encode("password")).thenReturn("encoded-password");
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        Map<String, Object> result = userService.register(request);

        assertThat(result).containsEntry("token", "stub-token-alice");
        assertThat(result).containsEntry("activationMode", "direct");
        assertThat(result).containsEntry("activationRequired", false);
        assertThat(((User) result.get("user")).getEnabled()).isTrue();
    }

    @Test
    void loginReturnsDirectActivationMetadata() {
        LoginRequest request = new LoginRequest();
        request.setUsername("alice");
        request.setPassword("password");

        when(userRepository.findByUsername("alice")).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("password", "encoded-password")).thenReturn(true);

        Map<String, Object> result = userService.login(request);

        assertThat(result).containsEntry("token", "stub-token-alice");
        assertThat(result).containsEntry("activationMode", "direct");
        assertThat(result).containsEntry("activationRequired", false);
    }

    @Test
    void updateCurrentUserProfilePersistsPhaseOneFields() {
        UserProfileUpdateRequest request = new UserProfileUpdateRequest();
        request.setAvatar("https://example.com/avatar.png");
        request.setBio("bio");
        request.setCollege("Computer");
        request.setMajor("Software");
        request.setStudentId("20240001");

        when(userRepository.findByUsername("alice")).thenReturn(Optional.of(user));
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        User updated = userService.updateCurrentUserProfile("alice", request);

        assertThat(updated.getAvatar()).isEqualTo("https://example.com/avatar.png");
        assertThat(updated.getBio()).isEqualTo("bio");
        assertThat(updated.getCollege()).isEqualTo("Computer");
        assertThat(updated.getMajor()).isEqualTo("Software");
        assertThat(updated.getStudentId()).isEqualTo("20240001");

        ArgumentCaptor<User> savedUser = ArgumentCaptor.forClass(User.class);
        verify(userRepository).save(savedUser.capture());
        assertThat(savedUser.getValue().getCollege()).isEqualTo("Computer");
    }

    @Test
    void verifyCampusIdentitySyncsTrustedProfileFieldsOnSuccess() {
        CampusIdentityVerifyRequest request = new CampusIdentityVerifyRequest();
        request.setStudentId("20240001");
        request.setCampusEmail("20240001@swjtu.edu.cn");

        when(userRepository.findByUsername("alice")).thenReturn(Optional.of(user));
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        CampusIdentityVerificationResult result = userService.verifyCampusIdentity("alice", request);

        assertThat(result.isVerified()).isTrue();
        assertThat(result.getStatus()).isEqualTo("VERIFIED");
        assertThat(result.getUser().getCollege()).isEqualTo("计算机与人工智能学院");
        assertThat(result.getUser().getMajor()).isEqualTo("软件工程");
        assertThat(result.getUser().getCampusVerified()).isTrue();
        assertThat(result.getUser().getCampusEmail()).isEqualTo("20240001@swjtu.edu.cn");
    }

    @Test
    void verifyCampusIdentityReturnsFailureWithoutOverwritingProfileOnMismatch() {
        user.setCollege("Original College");
        user.setMajor("Original Major");
        user.setStudentId("legacy");

        CampusIdentityVerifyRequest request = new CampusIdentityVerifyRequest();
        request.setStudentId("20240001");
        request.setCampusEmail("wrong@swjtu.edu.cn");

        when(userRepository.findByUsername("alice")).thenReturn(Optional.of(user));
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        CampusIdentityVerificationResult result = userService.verifyCampusIdentity("alice", request);

        assertThat(result.isVerified()).isFalse();
        assertThat(result.getStatus()).isEqualTo("FAILED");
        assertThat(result.getMessage()).isEqualTo("校园邮箱与学号不匹配");
        assertThat(result.getUser().getCollege()).isEqualTo("Original College");
        assertThat(result.getUser().getMajor()).isEqualTo("Original Major");
        assertThat(result.getUser().getStudentId()).isEqualTo("legacy");
    }

    @Test
    void updateCurrentUserProfileDoesNotOverrideTrustedCampusFieldsAfterVerification() {
        user.setCampusVerified(true);
        user.setCollege("计算机与人工智能学院");
        user.setMajor("软件工程");
        user.setStudentId("20240001");

        UserProfileUpdateRequest request = new UserProfileUpdateRequest();
        request.setAvatar("https://example.com/avatar.png");
        request.setBio("bio");
        request.setCollege("Other College");
        request.setMajor("Other Major");
        request.setStudentId("99999999");

        when(userRepository.findByUsername("alice")).thenReturn(Optional.of(user));
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        User updated = userService.updateCurrentUserProfile("alice", request);

        assertThat(updated.getAvatar()).isEqualTo("https://example.com/avatar.png");
        assertThat(updated.getBio()).isEqualTo("bio");
        assertThat(updated.getCollege()).isEqualTo("计算机与人工智能学院");
        assertThat(updated.getMajor()).isEqualTo("软件工程");
        assertThat(updated.getStudentId()).isEqualTo("20240001");
    }

    @Test
    void updateCurrentUserTagsReplacesOnlyInterestTags() {
        Tag postTag = tag(1L, "Spring Boot", "post");
        Tag oldInterest = tag(2L, "考研保研", "interest");
        Tag newInterest = tag(3L, "课程互助", "interest");
        user.setTags(new LinkedHashSet<>(List.of(postTag, oldInterest)));

        when(userRepository.findByUsername("alice")).thenReturn(Optional.of(user));
        when(tagRepository.findAllById(Set.of(3L))).thenReturn(List.of(newInterest));
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        Set<Tag> selected = userService.updateCurrentUserTags("alice", List.of(3L));

        assertThat(selected).containsExactly(newInterest);
        assertThat(user.getTags()).containsExactly(postTag, newInterest);
        verify(userRepository).save(user);
    }

    private Tag tag(Long id, String name, String category) {
        Tag tag = new Tag();
        tag.setId(id);
        tag.setName(name);
        tag.setCategory(category);
        return tag;
    }

    private static class StubJwtUtil extends JwtUtil {
        @Override
        public String generateToken(String username) {
            return "stub-token-" + username;
        }
    }
}
