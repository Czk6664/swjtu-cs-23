package com.swjtu.forum.service;

import com.swjtu.forum.dto.CommentRequest;
import com.swjtu.forum.dto.AdminPostManageRequest;
import com.swjtu.forum.dto.PostRequest;
import com.swjtu.forum.entity.Comment;
import com.swjtu.forum.entity.CommentLike;
import com.swjtu.forum.entity.Notification;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.PostBrowseHistory;
import com.swjtu.forum.entity.PostFavorite;
import com.swjtu.forum.entity.PostLike;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.entity.Tag;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.exception.ApiException;
import com.swjtu.forum.exception.ForbiddenException;
import com.swjtu.forum.exception.NotFoundException;
import com.swjtu.forum.repository.CommentLikeRepository;
import com.swjtu.forum.repository.CommentRepository;
import com.swjtu.forum.repository.PostBrowseHistoryRepository;
import com.swjtu.forum.repository.PostFavoriteRepository;
import com.swjtu.forum.repository.PostLikeRepository;
import com.swjtu.forum.repository.PostRepository;
import com.swjtu.forum.repository.SectionRepository;
import com.swjtu.forum.repository.TagRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.HashSet;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

@Service
@RequiredArgsConstructor
public class PostService {

    public static final int STATUS_PENDING = 0;
    public static final int STATUS_PUBLISHED = 1;
    public static final int STATUS_HIDDEN = 2;
    public static final int STATUS_REJECTED = 3;

    private static final int HEAT_VIEW = 1;
    private static final int HEAT_COMMENT = 4;
    private static final int HEAT_LIKE = 6;
    private static final int HEAT_FAVORITE = 8;
    private static final int ACCEPTED_COMMENT_CONTRIBUTION = 10;

    private final PostRepository postRepository;
    private final SectionRepository sectionRepository;
    private final TagRepository tagRepository;
    private final CommentRepository commentRepository;
    private final PostBrowseHistoryRepository postBrowseHistoryRepository;
    private final PostLikeRepository postLikeRepository;
    private final CommentLikeRepository commentLikeRepository;
    private final PostFavoriteRepository postFavoriteRepository;
    private final UserService userService;
    private final ContentModerationService contentModerationService;
    private final NotificationService notificationService;
    private final BadgeService badgeService;
    private final CircleService circleService;

    @Transactional
    public Post createPost(PostRequest request, String username) {
        User author = userService.getUserByUsername(username);
        Section section = findSectionOrThrow(request.getSectionId());

        Post post = new Post();
        post.setAuthor(author);
        post.setSection(section);
        post.setTitle(request.getTitle().trim());
        post.setContent(request.getContent().trim());
        applyPostImages(post, request.getCoverImage(), request.getImageUrls());
        post.setStatus(contentModerationService.shouldReview(request) ? STATUS_PENDING : STATUS_PUBLISHED);
        if (request.getCircleId() != null) {
            post.setCircle(circleService.findCircleOrThrow(request.getCircleId()));
        }

        applyTags(post, request.getTags());

        Post savedPost = postRepository.save(post);
        if (circleService != null) {
            circleService.incrementPostCount(savedPost.getCircle());
        }
        userService.addExperience(author, 10);
        badgeService.checkUserBadges(author);
        section.setPostCount(section.getPostCount() + 1);
        sectionRepository.save(section);
        return savedPost;
    }

    @Transactional(readOnly = true)
    public Page<Post> getPosts(Pageable pageable) {
        return postRepository.findByStatusOrderByCreatedAtDesc(STATUS_PUBLISHED, pageable);
    }

    @Transactional(readOnly = true)
    public Page<Post> getPostsBySection(Long sectionId, Pageable pageable) {
        Section section = findSectionOrThrow(sectionId);
        return postRepository.findBySectionAndStatusOrderByCreatedAtDesc(section, STATUS_PUBLISHED, pageable);
    }

    @Transactional(readOnly = true)
    public Page<Post> getHotPosts(Pageable pageable) {
        return postRepository.findHotPosts(pageable);
    }

    @Transactional(readOnly = true)
    public Page<Post> getMyPosts(String username, Pageable pageable) {
        User author = userService.getUserByUsername(username);
        return postRepository.findByAuthorOrderByCreatedAtDesc(author, pageable);
    }

    @Transactional(readOnly = true)
    public Page<Post> getPublishedPostsByUser(Long userId, Pageable pageable) {
        User author = userService.getUserById(userId);
        return postRepository.findByAuthorAndStatusOrderByCreatedAtDesc(author, STATUS_PUBLISHED, pageable);
    }

    @Transactional(readOnly = true)
    public Page<Post> getMyFavoritePosts(String username, Pageable pageable) {
        User user = userService.getUserByUsername(username);
        Page<PostFavorite> favorites = postFavoriteRepository.findByUserOrderByCreatedAtDesc(user, pageable);
        List<Post> posts = favorites.getContent().stream()
                .map(PostFavorite::getPost)
                .peek(post -> enrichInteractionState(post, user))
                .toList();
        return new PageImpl<>(posts, pageable, favorites.getTotalElements());
    }

    @Transactional(readOnly = true)
    public Page<Post> getMyBrowseHistory(String username, Pageable pageable) {
        User user = userService.getUserByUsername(username);
        Page<PostBrowseHistory> historyPage = postBrowseHistoryRepository.findByUserOrderByLastViewedAtDesc(user, pageable);
        List<Post> posts = historyPage.getContent().stream().map(PostBrowseHistory::getPost).toList();
        return new PageImpl<>(posts, pageable, historyPage.getTotalElements());
    }

    @Transactional(readOnly = true)
    public Page<Post> getAllPosts(Pageable pageable) {
        return postRepository.findAllByOrderByCreatedAtDesc(pageable);
    }

    @Transactional
    public Post getPostById(Long id, String username) {
        Post post = findPostOrThrow(id);
        User viewer = resolveViewer(username);
        assertReadable(post, viewer);

        if (viewer != null) {
            recordBrowseHistory(post, viewer);
        }

        if (post.getStatus() == STATUS_PUBLISHED) {
            post.setViewCount(post.getViewCount() + 1);
            increaseHeat(post, HEAT_VIEW);
            Post saved = postRepository.save(post);
            enrichInteractionState(saved, viewer);
            return saved;
        }
        enrichInteractionState(post, viewer);
        return post;
    }

    @Transactional(readOnly = true)
    public Post getOwnedPost(String username, Long postId) {
        User author = userService.getUserByUsername(username);
        return postRepository.findByIdAndAuthor(postId, author)
                .orElseThrow(() -> new NotFoundException("帖子不存在"));
    }

    @Transactional
    public Post updateOwnedPost(Long postId, PostRequest request, String username) {
        User author = userService.getUserByUsername(username);
        Post post = postRepository.findByIdAndAuthor(postId, author)
                .orElseThrow(() -> new NotFoundException("帖子不存在"));
        Section targetSection = findSectionOrThrow(request.getSectionId());

        applyPostUpdate(post, targetSection, request.getTitle(), request.getContent(), request.getCoverImage(),
                request.getImageUrls(), request.getTags());
        post.setCircle(request.getCircleId() == null ? null : circleService.findCircleOrThrow(request.getCircleId()));
        post.setStatus(contentModerationService.shouldReview(request) ? STATUS_PENDING : STATUS_PUBLISHED);
        return postRepository.save(post);
    }

    @Transactional
    public Post withdrawOwnedPost(Long postId, String username) {
        User author = userService.getUserByUsername(username);
        Post post = postRepository.findByIdAndAuthor(postId, author)
                .orElseThrow(() -> new NotFoundException("帖子不存在"));
        post.setStatus(STATUS_HIDDEN);
        return postRepository.save(post);
    }

    @Transactional
    public Post updateManagedPost(Long postId, AdminPostManageRequest request, String username) {
        Post post = findPostOrThrow(postId);
        User operator = userService.getUserByUsername(username);
        assertCanModerate(operator, post);
        Section targetSection = findSectionOrThrow(request.getSectionId());

        applyPostUpdate(post, targetSection, request.getTitle(), request.getContent(), request.getCoverImage(),
                request.getImageUrls(), request.getTags());
        post.setStatus(request.getStatus());
        return postRepository.save(post);
    }

    @Transactional
    public void deleteManagedPost(Long postId, String username) {
        Post post = findPostOrThrow(postId);
        User operator = userService.getUserByUsername(username);
        assertCanModerate(operator, post);
        post.setStatus(STATUS_HIDDEN);
        postRepository.save(post);
    }

    @Transactional
    public InteractionResult togglePostLike(Long postId, String username) {
        Post post = findPostOrThrow(postId);
        User user = userService.getUserByUsername(username);
        assertReadable(post, user);
        if (post.getStatus() != STATUS_PUBLISHED) {
            throw new ForbiddenException("当前帖子状态不允许点赞");
        }

        return postLikeRepository.findByUserAndPost(user, post)
                .map(existing -> {
                    postLikeRepository.delete(existing);
                    post.setLikeCount(Math.max(0, post.getLikeCount() - 1));
                    increaseHeat(post, -HEAT_LIKE);
                    postRepository.save(post);
                    return new InteractionResult(false, post.getLikeCount());
                })
                .orElseGet(() -> {
                    PostLike like = new PostLike();
                    like.setUser(user);
                    like.setPost(post);
                    postLikeRepository.save(like);
                    post.setLikeCount(post.getLikeCount() + 1);
                    increaseHeat(post, HEAT_LIKE);
                    postRepository.save(post);
                    return new InteractionResult(true, post.getLikeCount());
                });
    }

    @Transactional
    public InteractionResult togglePostFavorite(Long postId, String username) {
        Post post = findPostOrThrow(postId);
        User user = userService.getUserByUsername(username);
        assertReadable(post, user);
        if (post.getStatus() != STATUS_PUBLISHED) {
            throw new ForbiddenException("当前帖子状态不允许收藏");
        }

        return postFavoriteRepository.findByUserAndPost(user, post)
                .map(existing -> {
                    postFavoriteRepository.delete(existing);
                    post.setCollectCount(Math.max(0, post.getCollectCount() - 1));
                    increaseHeat(post, -HEAT_FAVORITE);
                    postRepository.save(post);
                    return new InteractionResult(false, post.getCollectCount());
                })
                .orElseGet(() -> {
                    PostFavorite favorite = new PostFavorite();
                    favorite.setUser(user);
                    favorite.setPost(post);
                    postFavoriteRepository.save(favorite);
                    post.setCollectCount(post.getCollectCount() + 1);
                    increaseHeat(post, HEAT_FAVORITE);
                    postRepository.save(post);
                    return new InteractionResult(true, post.getCollectCount());
                });
    }

    @Transactional
    public InteractionResult toggleCommentLike(Long commentId, String username) {
        Comment comment = commentRepository.findById(commentId)
                .orElseThrow(() -> new NotFoundException("评论不存在"));
        User user = userService.getUserByUsername(username);
        Post post = comment.getPost();
        assertReadable(post, user);
        if (post.getStatus() != STATUS_PUBLISHED) {
            throw new ForbiddenException("当前帖子状态不允许点赞评论");
        }

        return commentLikeRepository.findByUserAndComment(user, comment)
                .map(existing -> {
                    commentLikeRepository.delete(existing);
                    comment.setLikeCount(Math.max(0, comment.getLikeCount() - 1));
                    commentRepository.save(comment);
                    increaseHeat(post, -HEAT_LIKE);
                    postRepository.save(post);
                    return new InteractionResult(false, comment.getLikeCount());
                })
                .orElseGet(() -> {
                    CommentLike like = new CommentLike();
                    like.setUser(user);
                    like.setComment(comment);
                    commentLikeRepository.save(like);
                    comment.setLikeCount(comment.getLikeCount() + 1);
                    commentRepository.save(comment);
                    increaseHeat(post, HEAT_LIKE);
                    postRepository.save(post);
                    return new InteractionResult(true, comment.getLikeCount());
                });
    }

    @Transactional(readOnly = true)
    public Page<Comment> getComments(Long postId, Pageable pageable, String username) {
        Post post = findPostOrThrow(postId);
        User viewer = resolveViewer(username);
        assertReadable(post, viewer);
        Page<Comment> topLevel = commentRepository.findByPostAndParentIsNullAndStatusOrderByCreatedAtDesc(post, 1, pageable);
        // Attach visible replies so the frontend can render a two-level thread in one round trip.
        topLevel.getContent().forEach(this::attachReplies);
        return topLevel;
    }

    @Transactional(readOnly = true)
    public List<Comment> getReplies(Long commentId, String username) {
        Comment parent = commentRepository.findById(commentId)
                .orElseThrow(() -> new NotFoundException("评论不存在"));
        User viewer = resolveViewer(username);
        assertReadable(parent.getPost(), viewer);
        return commentRepository.findByParentAndStatusOrderByCreatedAtAsc(parent, 1);
    }

    private void attachReplies(Comment comment) {
        List<Comment> replies = commentRepository.findByParentAndStatusOrderByCreatedAtAsc(comment, 1);
        comment.setReplies(replies);
        comment.setReplyCount(replies.size());
    }

    @Transactional
    public Comment createComment(Long postId, CommentRequest request, String username) {
        Post post = findPostOrThrow(postId);
        if (post.getStatus() != STATUS_PUBLISHED) {
            throw new ForbiddenException("当前帖子状态不允许评论");
        }

        contentModerationService.validateCommentRequest(request);
        User author = userService.getUserByUsername(username);

        Comment comment = new Comment();
        comment.setPost(post);
        comment.setAuthor(author);
        comment.setContent(request.getContent().trim());

        Comment parent = resolveParentComment(request.getParentId(), post);
        comment.setParent(parent);

        Comment savedComment = commentRepository.save(comment);
        post.setCommentCount((int) commentRepository.countByPostAndStatus(post, 1));
        increaseHeat(post, HEAT_COMMENT);
        postRepository.save(post);
        userService.addExperience(author, 5);
        badgeService.checkUserBadges(author);

        notifyComment(post, parent, author);
        return savedComment;
    }

    @Transactional
    public Comment acceptComment(Long postId, Long commentId, String username) {
        Post post = findPostOrThrow(postId);
        User operator = userService.getUserByUsername(username);
        assertPostAuthor(post, operator);
        if (post.getStatus() != STATUS_PUBLISHED) {
            throw new ForbiddenException("当前帖子状态不允许采纳评论");
        }

        Comment target = findCommentInPostOrThrow(commentId, post);
        if (target.getStatus() != null && target.getStatus() != 1) {
            throw new ApiException(400, "不能采纳已隐藏的评论");
        }

        boolean firstAcceptedForTarget = !Boolean.TRUE.equals(target.getAccepted());
        commentRepository.findByPostAndAcceptedTrue(post)
                .filter(existing -> !existing.getId().equals(target.getId()))
                .ifPresent(existing -> {
                    existing.setAccepted(false);
                    commentRepository.save(existing);
                });

        target.setAccepted(true);
        Comment saved = commentRepository.save(target);
        post.setAcceptedCommentId(saved.getId());
        postRepository.save(post);

        if (firstAcceptedForTarget && target.getAuthor() != null
                && !target.getAuthor().getId().equals(post.getAuthor().getId())) {
            userService.addContribution(target.getAuthor(), ACCEPTED_COMMENT_CONTRIBUTION);
            badgeService.checkUserBadges(target.getAuthor());
        }
        return saved;
    }

    @Transactional
    public Comment cancelAcceptedComment(Long postId, Long commentId, String username) {
        Post post = findPostOrThrow(postId);
        User operator = userService.getUserByUsername(username);
        assertPostAuthor(post, operator);

        Comment target = findCommentInPostOrThrow(commentId, post);
        if (!Boolean.TRUE.equals(target.getAccepted())) {
            throw new ApiException(400, "该评论尚未被采纳");
        }

        target.setAccepted(false);
        Comment saved = commentRepository.save(target);
        if (saved.getId().equals(post.getAcceptedCommentId())) {
            post.setAcceptedCommentId(null);
            postRepository.save(post);
        }
        return saved;
    }

    private Comment resolveParentComment(Long parentId, Post post) {
        if (parentId == null) {
            return null;
        }
        Comment parent = commentRepository.findById(parentId)
                .orElseThrow(() -> new NotFoundException("被回复的评论不存在"));
        if (parent.getPost() == null || !parent.getPost().getId().equals(post.getId())) {
            throw new ApiException(400, "被回复的评论不属于该帖子");
        }
        if (parent.getStatus() != null && parent.getStatus() == 2) {
            throw new ApiException(400, "被回复的评论已被隐藏");
        }
        // Keep the thread two levels deep: a reply to a reply attaches to the same root.
        return parent.getParent() != null ? parent.getParent() : parent;
    }

    private void notifyComment(Post post, Comment parent, User author) {
        if (parent != null) {
            notificationService.notifyOther(parent.getAuthor(), author, Notification.TYPE_REPLY,
                    "你的评论收到新回复",
                    author.getUsername() + " 回复了你在《" + safeTitle(post) + "》下的评论",
                    post.getId(), "POST");
        }
        notificationService.notifyOther(post.getAuthor(), author, Notification.TYPE_COMMENT,
                "你的帖子收到新评论",
                author.getUsername() + " 评论了《" + safeTitle(post) + "》",
                post.getId(), "POST");
    }

    private String safeTitle(Post post) {
        String title = post.getTitle();
        if (title == null) {
            return "";
        }
        return title.length() > 30 ? title.substring(0, 30) + "…" : title;
    }

    @Transactional
    public Post updatePostStatus(Long postId, Integer targetStatus, String username) {
        if (targetStatus == null || targetStatus < STATUS_PENDING || targetStatus > STATUS_REJECTED) {
            throw new ApiException(400, "非法的审核状态");
        }

        Post post = findPostOrThrow(postId);
        User operator = userService.getUserByUsername(username);
        assertCanModerate(operator, post);
        post.setStatus(targetStatus);
        return postRepository.save(post);
    }

    private Post findPostOrThrow(Long id) {
        return postRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("帖子不存在"));
    }

    private void enrichInteractionState(Post post, User viewer) {
        if (post == null || viewer == null) {
            return;
        }
        post.setLikedByCurrentUser(postLikeRepository.findByUserAndPost(viewer, post).isPresent());
        post.setFavoritedByCurrentUser(postFavoriteRepository.findByUserAndPost(viewer, post).isPresent());
    }

    private Comment findCommentInPostOrThrow(Long commentId, Post post) {
        Comment comment = commentRepository.findById(commentId)
                .orElseThrow(() -> new NotFoundException("评论不存在"));
        if (comment.getPost() == null || !comment.getPost().getId().equals(post.getId())) {
            throw new ApiException(400, "评论不属于该帖子");
        }
        return comment;
    }

    private Section findSectionOrThrow(Long id) {
        return sectionRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("版块不存在"));
    }

    private User resolveViewer(String username) {
        if (!StringUtils.hasText(username)) {
            return null;
        }
        return userService.getUserByUsername(username);
    }

    private void assertReadable(Post post, User viewer) {
        if (post.getStatus() == STATUS_PUBLISHED) {
            return;
        }

        if (viewer == null) {
            throw new NotFoundException("帖子不存在");
        }

        boolean isAuthor = post.getAuthor() != null && post.getAuthor().getId().equals(viewer.getId());
        if (isAuthor || canModerate(viewer, post.getSection())) {
            return;
        }

        throw new NotFoundException("帖子不存在");
    }

    private void assertCanModerate(User operator, Post post) {
        if (canModerate(operator, post.getSection())) {
            return;
        }
        throw new ForbiddenException("无权处理该版块的帖子");
    }

    private void assertPostAuthor(Post post, User operator) {
        if (post.getAuthor() != null && operator != null && post.getAuthor().getId().equals(operator.getId())) {
            return;
        }
        throw new ForbiddenException("只有楼主可以采纳最佳答案");
    }

    private void applyPostUpdate(Post post, Section targetSection, String title, String content, String coverImage,
                                 List<String> imageUrls, List<String> tags) {
        Section previousSection = post.getSection();
        if (previousSection != null && !previousSection.getId().equals(targetSection.getId())) {
            previousSection.setPostCount(Math.max(0, previousSection.getPostCount() - 1));
            targetSection.setPostCount(targetSection.getPostCount() + 1);
            sectionRepository.save(previousSection);
            sectionRepository.save(targetSection);
        }

        post.setSection(targetSection);
        post.setTitle(title.trim());
        post.setContent(content.trim());
        applyPostImages(post, coverImage, imageUrls);
        applyTags(post, tags);
    }

    private void applyPostImages(Post post, String coverImage, List<String> rawImageUrls) {
        List<String> images = normalizePostImages(coverImage, rawImageUrls);
        post.getImageUrls().clear();
        post.getImageUrls().addAll(images);
        post.setCoverImage(images.isEmpty() ? null : images.get(0));
    }

    private List<String> normalizePostImages(String coverImage, List<String> rawImageUrls) {
        LinkedHashSet<String> images = new LinkedHashSet<>();
        if (rawImageUrls != null) {
            if (rawImageUrls.size() > 9) {
                throw new ApiException(400, "帖子图片最多上传 9 张");
            }
            rawImageUrls.stream()
                    .map(this::trimToNull)
                    .filter(StringUtils::hasText)
                    .forEach(images::add);
        }
        String legacyCover = trimToNull(coverImage);
        if (images.isEmpty() && StringUtils.hasText(legacyCover)) {
            images.add(legacyCover);
        }
        if (images.size() > 9) {
            throw new ApiException(400, "帖子图片最多上传 9 张");
        }
        for (String image : images) {
            if (image.length() > 500) {
                throw new ApiException(400, "图片链接长度不能超过 500 个字符");
            }
        }
        return new ArrayList<>(images);
    }

    private boolean canModerate(User operator, Section section) {
        if (operator == null || !StringUtils.hasText(operator.getRole())) {
            return false;
        }
        if ("ADMIN".equals(operator.getRole())) {
            return true;
        }
        return "MODERATOR".equals(operator.getRole())
                && section.getModerator() != null
                && section.getModerator().getId().equals(operator.getId());
    }

    private void increaseHeat(Post post, int delta) {
        int current = post.getHeatScore() == null ? 0 : post.getHeatScore();
        post.setHeatScore(Math.max(0, current + delta));
    }

    private void recordBrowseHistory(Post post, User viewer) {
        PostBrowseHistory history = postBrowseHistoryRepository.findByUserAndPost(viewer, post)
                .orElseGet(() -> {
                    PostBrowseHistory newHistory = new PostBrowseHistory();
                    newHistory.setUser(viewer);
                    newHistory.setPost(post);
                    return newHistory;
                });
        postBrowseHistoryRepository.save(history);
    }

    private void applyTags(Post post, List<String> rawTags) {
        Set<Tag> tags = new HashSet<>();
        if (rawTags != null && !rawTags.isEmpty()) {
            for (String rawTagName : rawTags) {
                String tagName = rawTagName.trim();
                Tag tag = tagRepository.findByName(tagName)
                        .orElseGet(() -> {
                            Tag newTag = new Tag();
                            newTag.setName(tagName);
                            return tagRepository.save(newTag);
                        });
                tags.add(tag);
            }
        }
        post.setTags(tags);
    }

    private String trimToNull(String value) {
        if (!StringUtils.hasText(value)) {
            return null;
        }
        return value.trim();
    }

    public record InteractionResult(boolean active, int count) {}
}
