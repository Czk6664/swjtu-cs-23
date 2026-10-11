package com.swjtu.forum.service;

import com.swjtu.forum.dto.LoginRequest;
import com.swjtu.forum.dto.CampusIdentityVerificationResult;
import com.swjtu.forum.dto.CampusIdentityVerifyRequest;
import com.swjtu.forum.dto.RegisterRequest;
import com.swjtu.forum.dto.UserProfileUpdateRequest;
import com.swjtu.forum.entity.Tag;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.repository.TagRepository;
import com.swjtu.forum.exception.ApiException;
import com.swjtu.forum.exception.NotFoundException;
import com.swjtu.forum.repository.UserRepository;
import com.swjtu.forum.security.JwtUtil;
import com.swjtu.forum.security.LoginAttemptService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class UserService {

    private static final Map<String, CampusIdentityRecord> CAMPUS_DIRECTORY = buildCampusDirectory();

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;
    private final LoginAttemptService loginAttemptService;
    private final NotificationService notificationService;
    private final TagRepository tagRepository;

    @Transactional
    public Map<String, Object> register(RegisterRequest request) {
        if (userRepository.existsByUsername(request.getUsername())) {
            throw new ApiException(400, "用户名已存在");
        }
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new ApiException(400, "邮箱已被注册");
        }

        User user = new User();
        user.setUsername(request.getUsername().trim());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setEmail(request.getEmail().trim());
        user.setStudentId(trimToNull(request.getStudentId()));
        user.setCollege(trimToNull(request.getCollege()));
        user.setMajor(trimToNull(request.getMajor()));
        user.setEnabled(true);

        userRepository.save(user);

        String token = jwtUtil.generateToken(user.getUsername());
        Map<String, Object> result = new HashMap<>();
        result.put("token", token);
        result.put("user", user);
        result.put("activationMode", "direct");
        result.put("activationRequired", false);
        return result;
    }

    @Transactional(readOnly = true)
    public Map<String, Object> login(LoginRequest request) {
        String loginKey = request.getUsername();
        if (loginAttemptService.isBlocked(loginKey)) {
            throw new ApiException(429, "登录尝试过于频繁，请 5 分钟后再试");
        }

        User user = userRepository.findByUsername(request.getUsername())
                .orElseThrow(() -> {
                    loginAttemptService.recordFailure(loginKey);
                    return new ApiException(400, "用户名或密码错误");
                });

        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            loginAttemptService.recordFailure(loginKey);
            throw new ApiException(400, "用户名或密码错误");
        }

        if (!Boolean.TRUE.equals(user.getEnabled())) {
            throw new ApiException(403, "账号已被禁用");
        }

        loginAttemptService.recordSuccess(loginKey);
        String token = jwtUtil.generateToken(user.getUsername());
        Map<String, Object> result = new HashMap<>();
        result.put("token", token);
        result.put("user", user);
        result.put("activationMode", "direct");
        result.put("activationRequired", false);
        return result;
    }

    @Transactional(readOnly = true)
    public User getUserByUsername(String username) {
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new NotFoundException("用户不存在"));
    }

    @Transactional(readOnly = true)
    public User getUserById(Long id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("User not found"));
    }

    @Transactional(readOnly = true)
    public Map<String, Object> getPublicProfile(Long id) {
        User user = getUserById(id);
        Map<String, Object> profile = new LinkedHashMap<>();
        profile.put("id", user.getId());
        profile.put("username", user.getUsername());
        profile.put("avatar", user.getAvatar());
        profile.put("bio", user.getBio());
        profile.put("college", user.getCollege());
        profile.put("major", user.getMajor());
        profile.put("level", user.getLevel());
        profile.put("exp", user.getExp());
        profile.put("points", user.getPoints());
        profile.put("role", user.getRole());
        profile.put("campusVerified", user.getCampusVerified());
        profile.put("createdAt", user.getCreatedAt());
        profile.put("tags", user.getTags());
        return profile;
    }

    @Transactional
    public User saveUser(User user) {
        return userRepository.save(user);
    }

    @Transactional
    public void addExperience(User user, int exp) {
        int currentExp = user.getExp() == null ? 0 : user.getExp();
        user.setExp(currentExp + exp);
        checkLevelUp(user);
        userRepository.save(user);
    }

    @Transactional
    public void addContribution(User user, int amount) {
        int currentPoints = user.getPoints() == null ? 0 : user.getPoints();
        user.setPoints(currentPoints + amount);
        addExperience(user, amount);
    }

    @Transactional
    public User updateCurrentUser(String username, UserProfileUpdateRequest request) {
        User user = getUserByUsername(username);
        user.setAvatar(trimToNull(request.getAvatar()));
        user.setBio(trimToNull(request.getBio()));
        if (!Boolean.TRUE.equals(user.getCampusVerified())) {
            user.setCollege(trimToNull(request.getCollege()));
            user.setMajor(trimToNull(request.getMajor()));
            user.setStudentId(trimToNull(request.getStudentId()));
        }
        return userRepository.save(user);
    }

    @Transactional
    public User updateCurrentUserProfile(String username, UserProfileUpdateRequest request) {
        return updateCurrentUser(username, request);
    }

    @Transactional(readOnly = true)
    public List<Tag> listInterestTags() {
        return tagRepository.findByCategoryOrderByUseCountDescNameAsc("interest");
    }

    @Transactional(readOnly = true)
    public Set<Tag> getCurrentUserTags(String username) {
        return getUserByUsername(username).getTags().stream()
                .collect(Collectors.toCollection(LinkedHashSet::new));
    }

    @Transactional
    public Set<Tag> updateCurrentUserTags(String username, List<Long> tagIds) {
        User user = getUserByUsername(username);
        Set<Long> requested = tagIds == null ? Set.of() : new HashSet<>(tagIds);
        if (requested.size() > 8) {
            throw new ApiException(400, "最多选择 8 个校园身份标签");
        }

        Set<Tag> interestTags = requested.isEmpty()
                ? Set.of()
                : tagRepository.findAllById(requested).stream()
                .filter(tag -> "interest".equals(tag.getCategory()))
                .collect(Collectors.toCollection(LinkedHashSet::new));
        if (interestTags.size() != requested.size()) {
            throw new ApiException(400, "包含不存在或不可选的校园身份标签");
        }

        Set<Tag> nextTags = user.getTags().stream()
                .filter(tag -> !"interest".equals(tag.getCategory()))
                .collect(Collectors.toCollection(LinkedHashSet::new));
        nextTags.addAll(interestTags);
        user.setTags(nextTags);
        userRepository.save(user);
        return interestTags;
    }

    @Transactional
    public Set<Tag> updateCurrentUserTagsByNames(String username, List<String> tagNames) {
        User user = getUserByUsername(username);
        List<String> requested = tagNames == null ? List.of() : tagNames.stream()
                .map(this::trimToNull)
                .filter(StringUtils::hasText)
                .distinct()
                .toList();
        if (requested.size() > 8) {
            throw new ApiException(400, "最多选择 8 个校园身份标签");
        }

        Set<Tag> interestTags = requested.stream()
                .map(this::findOrCreateInterestTag)
                .collect(Collectors.toCollection(LinkedHashSet::new));
        Set<Tag> nextTags = user.getTags().stream()
                .filter(tag -> !"interest".equals(tag.getCategory()))
                .collect(Collectors.toCollection(LinkedHashSet::new));
        nextTags.addAll(interestTags);
        user.setTags(nextTags);
        userRepository.save(user);
        return interestTags;
    }

    @Transactional
    public CampusIdentityVerificationResult verifyCampusIdentity(String username, CampusIdentityVerifyRequest request) {
        User user = getUserByUsername(username);
        String studentId = trimToNull(request.getStudentId());
        String campusEmail = trimToNull(request.getCampusEmail());
        CampusIdentityRecord record = CAMPUS_DIRECTORY.get(studentId);

        if (record == null) {
            user.setCampusVerified(false);
            user.setCampusIdentityStatus("FAILED");
            user.setCampusVerificationMessage("未找到对应学号的校园身份信息");
            userRepository.save(user);
            return new CampusIdentityVerificationResult(false, user.getCampusIdentityStatus(), user.getCampusVerificationMessage(), user);
        }

        if (!record.campusEmail().equalsIgnoreCase(campusEmail)) {
            user.setCampusVerified(false);
            user.setCampusIdentityStatus("FAILED");
            user.setCampusVerificationMessage("校园邮箱与学号不匹配");
            userRepository.save(user);
            return new CampusIdentityVerificationResult(false, user.getCampusIdentityStatus(), user.getCampusVerificationMessage(), user);
        }

        LocalDateTime now = LocalDateTime.now();
        user.setStudentId(record.studentId());
        user.setCampusEmail(record.campusEmail());
        user.setCollege(record.college());
        user.setMajor(record.major());
        user.setCampusVerified(true);
        user.setCampusIdentityStatus("VERIFIED");
        user.setCampusVerificationMessage("校园身份已认证，资料已同步");
        user.setCampusVerifiedAt(now);
        user.setCampusProfileSyncedAt(now);
        userRepository.save(user);

        return new CampusIdentityVerificationResult(true, user.getCampusIdentityStatus(), user.getCampusVerificationMessage(), user);
    }

    private void checkLevelUp(User user) {
        int currentExp = user.getExp();
        int currentLevel = user.getLevel();
        int nextLevelExp = getNextLevelRequirement(currentLevel);

        if (currentExp >= nextLevelExp) {
            int newLevel = currentLevel + 1;
            user.setLevel(newLevel);
            if (notificationService != null) {
                notificationService.notify(user, com.swjtu.forum.entity.Notification.TYPE_LEVEL_UP,
                        "恭喜升级到 Lv." + newLevel,
                        "持续活跃可解锁更多权益，继续加油！", (long) newLevel, "LEVEL");
            }
        }
    }

    private int getNextLevelRequirement(int level) {
        return level * 100;
    }

    private String trimToNull(String value) {
        if (!StringUtils.hasText(value)) {
            return null;
        }
        return value.trim();
    }

    private Tag findOrCreateInterestTag(String name) {
        return tagRepository.findByName(name).orElseGet(() -> {
            Tag tag = new Tag();
            tag.setName(name);
            tag.setCategory("interest");
            tag.setUseCount(0);
            return tagRepository.save(tag);
        });
    }

    private static Map<String, CampusIdentityRecord> buildCampusDirectory() {
        Map<String, CampusIdentityRecord> directory = new LinkedHashMap<>();
        directory.put("20240001", new CampusIdentityRecord("20240001", "20240001@swjtu.edu.cn", "计算机与人工智能学院", "软件工程"));
        directory.put("20240002", new CampusIdentityRecord("20240002", "20240002@swjtu.edu.cn", "信息科学与技术学院", "计算机科学与技术"));
        directory.put("20240003", new CampusIdentityRecord("20240003", "20240003@swjtu.edu.cn", "土木工程学院", "交通工程"));
        return directory;
    }

    private record CampusIdentityRecord(String studentId, String campusEmail, String college, String major) {
    }
}
