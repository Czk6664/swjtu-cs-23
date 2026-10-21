package com.swjtu.forum.service;

import com.swjtu.forum.dto.CircleRequest;
import com.swjtu.forum.entity.Circle;
import com.swjtu.forum.entity.CircleMember;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.exception.ApiException;
import com.swjtu.forum.exception.NotFoundException;
import com.swjtu.forum.repository.CircleMemberRepository;
import com.swjtu.forum.repository.CircleRepository;
import com.swjtu.forum.repository.PostRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
public class CircleService {

    private static final Pattern NON_SLUG = Pattern.compile("[^a-z0-9-]+");

    private final CircleRepository circleRepository;
    private final CircleMemberRepository circleMemberRepository;
    private final PostRepository postRepository;
    private final UserService userService;

    @Transactional(readOnly = true)
    public List<Map<String, Object>> listCircles(String username) {
        User viewer = resolveUser(username);
        return circleRepository.findAllByOrderByMemberCountDescPostCountDescCreatedAtDesc().stream()
                .map(circle -> circleView(circle, viewer))
                .toList();
    }

    @Transactional(readOnly = true)
    public Map<String, Object> getCircle(Long id, String username) {
        User viewer = resolveUser(username);
        return circleView(findCircleOrThrow(id), viewer);
    }

    @Transactional
    public Map<String, Object> createCircle(CircleRequest request, String username) {
        User creator = userService.getUserByUsername(username);
        String name = request.getName().trim();
        if (circleRepository.findByName(name).isPresent()) {
            throw new ApiException(400, "圈子名称已存在");
        }

        Circle circle = new Circle();
        circle.setName(name);
        circle.setSlug(uniqueSlug(name));
        circle.setDescription(request.getDescription().trim());
        circle.setIcon(StringUtils.hasText(request.getIcon()) ? request.getIcon().trim() : "社");
        circle.setCreator(creator);
        Circle saved = circleRepository.save(circle);
        join(saved, creator, "OWNER");
        return circleView(saved, creator);
    }

    @Transactional
    public Map<String, Object> joinCircle(Long id, String username) {
        Circle circle = findCircleOrThrow(id);
        User user = userService.getUserByUsername(username);
        join(circle, user, "MEMBER");
        return circleView(circle, user);
    }

    @Transactional
    public Map<String, Object> leaveCircle(Long id, String username) {
        Circle circle = findCircleOrThrow(id);
        User user = userService.getUserByUsername(username);
        circleMemberRepository.deleteByCircleAndUser(circle, user);
        circle.setMemberCount((int) circleMemberRepository.countByCircle(circle));
        circleRepository.save(circle);
        return circleView(circle, user);
    }

    @Transactional(readOnly = true)
    public Page<Post> circlePosts(Long id, Pageable pageable) {
        Circle circle = findCircleOrThrow(id);
        return postRepository.findByCircleAndStatusOrderByCreatedAtDesc(circle, PostService.STATUS_PUBLISHED, pageable);
    }

    @Transactional
    public void incrementPostCount(Circle circle) {
        if (circle == null) {
            return;
        }
        circle.setPostCount((circle.getPostCount() == null ? 0 : circle.getPostCount()) + 1);
        circleRepository.save(circle);
    }

    public Circle findCircleOrThrow(Long id) {
        return circleRepository.findById(id).orElseThrow(() -> new NotFoundException("圈子不存在"));
    }

    private void join(Circle circle, User user, String role) {
        circleMemberRepository.findByCircleAndUser(circle, user).orElseGet(() -> {
            CircleMember member = new CircleMember();
            member.setCircle(circle);
            member.setUser(user);
            member.setRole(role);
            circleMemberRepository.save(member);
            circle.setMemberCount((int) circleMemberRepository.countByCircle(circle));
            circleRepository.save(circle);
            return member;
        });
    }

    private Map<String, Object> circleView(Circle circle, User viewer) {
        Map<String, Object> view = new LinkedHashMap<>();
        view.put("id", circle.getId());
        view.put("name", circle.getName());
        view.put("slug", circle.getSlug());
        view.put("description", circle.getDescription());
        view.put("icon", circle.getIcon());
        view.put("memberCount", circle.getMemberCount());
        view.put("postCount", circle.getPostCount());
        view.put("createdAt", circle.getCreatedAt());
        view.put("joined", viewer != null && circleMemberRepository.existsByCircleAndUser(circle, viewer));
        return view;
    }

    private User resolveUser(String username) {
        return StringUtils.hasText(username) ? userService.getUserByUsername(username) : null;
    }

    private String uniqueSlug(String name) {
        String base = NON_SLUG.matcher(name.toLowerCase().replace(" ", "-")).replaceAll("-");
        base = base.replaceAll("-+", "-").replaceAll("(^-|-$)", "");
        if (!StringUtils.hasText(base)) {
            base = "circle";
        }
        String slug = base;
        int suffix = 2;
        while (circleRepository.findBySlug(slug).isPresent()) {
            slug = base + "-" + suffix++;
        }
        return slug;
    }
}
