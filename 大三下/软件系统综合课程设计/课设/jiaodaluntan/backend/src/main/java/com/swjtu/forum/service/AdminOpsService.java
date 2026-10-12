package com.swjtu.forum.service;

import com.swjtu.forum.dto.AdminPostManageRequest;
import com.swjtu.forum.dto.SectionManageRequest;
import com.swjtu.forum.entity.Comment;
import com.swjtu.forum.entity.OperationLog;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.exception.ApiException;
import com.swjtu.forum.exception.NotFoundException;
import com.swjtu.forum.repository.CommentRepository;
import com.swjtu.forum.repository.OperationLogRepository;
import com.swjtu.forum.repository.PostRepository;
import com.swjtu.forum.repository.SectionRepository;
import com.swjtu.forum.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
@RequiredArgsConstructor
public class AdminOpsService {

    private final PostRepository postRepository;
    private final CommentRepository commentRepository;
    private final SectionRepository sectionRepository;
    private final UserRepository userRepository;
    private final OperationLogRepository operationLogRepository;
    private final UserService userService;
    private final PostService postService;

    @Transactional(readOnly = true)
    public Page<Post> getPendingPosts(Pageable pageable) {
        return postRepository.findByStatusOrderByCreatedAtDesc(PostService.STATUS_PENDING, pageable);
    }

    @Transactional(readOnly = true)
    public Page<Post> listAllPosts(Pageable pageable) {
        return postService.getAllPosts(pageable);
    }

    @Transactional
    public Comment hideComment(Long commentId, String operatorName) {
        Comment comment = commentRepository.findById(commentId)
                .orElseThrow(() -> new NotFoundException("评论不存在"));
        User operator = userService.getUserByUsername(operatorName);
        assertCanModerate(operator, comment.getPost());
        comment.setStatus(2);
        Comment saved = commentRepository.save(comment);
        syncVisibleCommentCount(comment.getPost());
        log(operator, "HIDE_COMMENT", "COMMENT", commentId, "隐藏评论");
        return saved;
    }

    @Transactional
    public Comment restoreComment(Long commentId, String operatorName) {
        Comment comment = commentRepository.findById(commentId)
                .orElseThrow(() -> new NotFoundException("评论不存在"));
        User operator = userService.getUserByUsername(operatorName);
        assertCanModerate(operator, comment.getPost());
        comment.setStatus(1);
        Comment saved = commentRepository.save(comment);
        syncVisibleCommentCount(comment.getPost());
        log(operator, "RESTORE_COMMENT", "COMMENT", commentId, "恢复评论");
        return saved;
    }

    /** Keep the post's cached comment counter aligned with the number of visible comments. */
    private void syncVisibleCommentCount(Post post) {
        if (post == null) {
            return;
        }
        post.setCommentCount((int) commentRepository.countByPostAndStatus(post, 1));
        postRepository.save(post);
    }

    @Transactional
    public Post moderatePostStatus(Long postId, Integer status, String operatorName) {
        Post updated = postService.updatePostStatus(postId, status, operatorName);
        User operator = userService.getUserByUsername(operatorName);
        log(operator, "MODERATE_POST", "POST", postId, "帖子状态更新为 " + status);
        return updated;
    }

    @Transactional
    public Post updatePost(Long postId, AdminPostManageRequest request, String operatorName) {
        Post updated = postService.updateManagedPost(postId, request, operatorName);
        User operator = userService.getUserByUsername(operatorName);
        log(operator, "UPDATE_POST", "POST", postId, "管理员更新帖子");
        return updated;
    }

    @Transactional
    public void deletePost(Long postId, String operatorName) {
        postService.deleteManagedPost(postId, operatorName);
        User operator = userService.getUserByUsername(operatorName);
        log(operator, "DELETE_POST", "POST", postId, "管理员删除帖子");
    }

    @Transactional(readOnly = true)
    public Page<User> listUsers(Pageable pageable) {
        return userRepository.findAll(pageable);
    }

    @Transactional
    public User banUser(Long userId, String operatorName) {
        User user = userRepository.findById(userId).orElseThrow(() -> new NotFoundException("用户不存在"));
        if ("ADMIN".equals(user.getRole()) && Boolean.TRUE.equals(user.getEnabled())
                && userRepository.countByRoleAndEnabledTrue("ADMIN") <= 1) {
            throw new ApiException(400, "至少需要保留一个可用管理员账号");
        }
        user.setEnabled(false);
        User saved = userRepository.save(user);
        User operator = userService.getUserByUsername(operatorName);
        log(operator, "BAN_USER", "USER", userId, "封禁用户");
        return saved;
    }

    @Transactional
    public User unbanUser(Long userId, String operatorName) {
        User user = userRepository.findById(userId).orElseThrow(() -> new NotFoundException("用户不存在"));
        user.setEnabled(true);
        User saved = userRepository.save(user);
        User operator = userService.getUserByUsername(operatorName);
        log(operator, "UNBAN_USER", "USER", userId, "解除封禁");
        return saved;
    }

    @Transactional
    public Section createSection(SectionManageRequest request, String operatorName) {
        sectionRepository.findByName(request.getName().trim()).ifPresent(exist -> {
            throw new ApiException(400, "版块名称已存在");
        });
        Section section = new Section();
        mergeSection(section, request);
        Section saved = sectionRepository.save(section);
        User operator = userService.getUserByUsername(operatorName);
        log(operator, "CREATE_SECTION", "SECTION", saved.getId(), "创建版块");
        return saved;
    }

    @Transactional
    public Section updateSection(Long sectionId, SectionManageRequest request, String operatorName) {
        Section section = sectionRepository.findById(sectionId).orElseThrow(() -> new NotFoundException("版块不存在"));
        if (!section.getName().equals(request.getName().trim())) {
            sectionRepository.findByName(request.getName().trim()).ifPresent(exist -> {
                throw new ApiException(400, "版块名称已存在");
            });
        }
        mergeSection(section, request);
        Section saved = sectionRepository.save(section);
        User operator = userService.getUserByUsername(operatorName);
        log(operator, "UPDATE_SECTION", "SECTION", sectionId, "更新版块");
        return saved;
    }

    @Transactional
    public void deleteSection(Long sectionId, String operatorName) {
        Section section = sectionRepository.findById(sectionId).orElseThrow(() -> new NotFoundException("版块不存在"));
        if (postRepository.countBySection(section) > 0) {
            throw new ApiException(400, "版块下仍有帖子，不能删除");
        }
        sectionRepository.delete(section);
        User operator = userService.getUserByUsername(operatorName);
        log(operator, "DELETE_SECTION", "SECTION", sectionId, "删除版块");
    }

    @Transactional(readOnly = true)
    public Page<OperationLog> getLogs(Pageable pageable) {
        return operationLogRepository.findAllByOrderByCreatedAtDesc(pageable);
    }

    private void mergeSection(Section section, SectionManageRequest request) {
        section.setName(request.getName().trim());
        section.setDescription(trimToNull(request.getDescription()));
        section.setIcon(trimToNull(request.getIcon()));
        section.setSortOrder(request.getSortOrder() == null ? 0 : request.getSortOrder());

        if (request.getModeratorId() == null) {
            section.setModerator(null);
        } else {
            User moderator = userRepository.findById(request.getModeratorId())
                    .orElseThrow(() -> new NotFoundException("版主用户不存在"));
            if (!"MODERATOR".equals(moderator.getRole()) && !"ADMIN".equals(moderator.getRole())) {
                throw new ApiException(400, "指定用户不是版主或管理员");
            }
            section.setModerator(moderator);
        }
    }

    private void assertCanModerate(User operator, Post post) {
        if ("ADMIN".equals(operator.getRole())) {
            return;
        }
        if ("MODERATOR".equals(operator.getRole())
                && post.getSection() != null
                && post.getSection().getModerator() != null
                && post.getSection().getModerator().getId().equals(operator.getId())) {
            return;
        }
        throw new ApiException(403, "无权处理该内容");
    }

    private void log(User actor, String action, String targetType, Long targetId, String detail) {
        OperationLog log = new OperationLog();
        log.setActor(actor);
        log.setAction(action);
        log.setTargetType(targetType);
        log.setTargetId(targetId);
        log.setDetail(detail);
        operationLogRepository.save(log);
    }

    private String trimToNull(String value) {
        if (!StringUtils.hasText(value)) {
            return null;
        }
        return value.trim();
    }
}
