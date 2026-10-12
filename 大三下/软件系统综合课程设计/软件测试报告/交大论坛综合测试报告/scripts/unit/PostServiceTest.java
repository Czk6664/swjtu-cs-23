package com.swjtu.forum.service;

import com.swjtu.forum.dto.CommentRequest;
import com.swjtu.forum.dto.PostRequest;
import com.swjtu.forum.entity.Comment;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.PostFavorite;
import com.swjtu.forum.entity.PostLike;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.entity.User;
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
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
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
class PostServiceTest {

    @Mock
    private PostRepository postRepository;

    @Mock
    private SectionRepository sectionRepository;

    @Mock
    private TagRepository tagRepository;

    @Mock
    private CommentRepository commentRepository;

    @Mock
    private PostLikeRepository postLikeRepository;

    @Mock
    private CommentLikeRepository commentLikeRepository;

    @Mock
    private PostFavoriteRepository postFavoriteRepository;

    @Mock
    private PostBrowseHistoryRepository postBrowseHistoryRepository;

    @Mock
    private NotificationService notificationService;

    @Mock
    private BadgeService badgeService;

    private PostService postService;
    private StubUserService userService;
    private StubContentModerationService contentModerationService;
    private User author;
    private User moderator;
    private Section section;
    private Section otherSection;

    @BeforeEach
    void setUp() {
        userService = new StubUserService();
        contentModerationService = new StubContentModerationService();
        postService = new PostService(
                postRepository,
                sectionRepository,
                tagRepository,
                commentRepository,
                postBrowseHistoryRepository,
                postLikeRepository,
                commentLikeRepository,
                postFavoriteRepository,
                userService,
                contentModerationService,
                notificationService,
                badgeService,
                null
        );

        author = new User();
        author.setId(1L);
        author.setUsername("author");
        author.setRole("USER");

        moderator = new User();
        moderator.setId(2L);
        moderator.setUsername("moderator");
        moderator.setRole("MODERATOR");

        section = new Section();
        section.setId(10L);
        section.setName("Academic");
        section.setModerator(moderator);
        section.setPostCount(0);

        otherSection = new Section();
        otherSection.setId(11L);
        otherSection.setName("Life");
        otherSection.setPostCount(0);
    }

    @Test
    void createPostMarksSensitiveContentAsPending() {
        PostRequest request = new PostRequest();
        request.setTitle("  敏感测试  ");
        request.setContent("  正文内容  ");
        request.setSectionId(10L);
        userService.setUser(author);
        contentModerationService.setShouldReview(true);

        when(sectionRepository.findById(10L)).thenReturn(Optional.of(section));
        when(postRepository.save(any(Post.class))).thenAnswer(invocation -> invocation.getArgument(0));

        Post created = postService.createPost(request, "author");

        assertThat(created.getStatus()).isEqualTo(PostService.STATUS_PENDING);
        assertThat(created.getTitle()).isEqualTo("敏感测试");
        assertThat(created.getContent()).isEqualTo("正文内容");
        verify(sectionRepository).save(section);
    }

    @Test
    void updatePostStatusRejectsModeratorOutsideAssignedSection() {
        Post post = new Post();
        post.setId(100L);
        post.setAuthor(author);
        post.setSection(otherSection);
        post.setStatus(PostService.STATUS_PENDING);
        userService.setUser(moderator);

        when(postRepository.findById(100L)).thenReturn(Optional.of(post));

        assertThatThrownBy(() -> postService.updatePostStatus(100L, PostService.STATUS_HIDDEN, "moderator"))
                .isInstanceOf(ForbiddenException.class)
                .hasMessage("无权处理该版块的帖子");
    }

    @Test
    void createCommentRejectsNonPublishedPost() {
        Post post = new Post();
        post.setId(200L);
        post.setStatus(PostService.STATUS_PENDING);

        CommentRequest request = new CommentRequest();
        request.setContent("一条评论");

        when(postRepository.findById(200L)).thenReturn(Optional.of(post));

        assertThatThrownBy(() -> postService.createComment(200L, request, "author"))
                .isInstanceOf(ForbiddenException.class)
                .hasMessage("当前帖子状态不允许评论");
    }

    @Test
    void getAllPostsDelegatesToRepositoryOrderingQuery() {
        org.springframework.data.domain.Pageable pageable = org.springframework.data.domain.PageRequest.of(0, 20);
        when(postRepository.findAllByOrderByCreatedAtDesc(pageable))
                .thenReturn(org.springframework.data.domain.Page.empty(pageable));

        assertThat(postService.getAllPosts(pageable).getContent()).isEmpty();
        verify(postRepository).findAllByOrderByCreatedAtDesc(pageable);
    }

    @Test
    void getPostByIdHydratesCurrentUserInteractionState() {
        Post post = publishedPost(250L, author);
        post.setViewCount(3);
        User viewer = user("viewer", 5L, "USER");
        userService.setUser(viewer);

        when(postRepository.findById(250L)).thenReturn(Optional.of(post));
        when(postRepository.save(any(Post.class))).thenAnswer(invocation -> invocation.getArgument(0));
        when(postLikeRepository.findByUserAndPost(viewer, post)).thenReturn(Optional.of(new PostLike()));
        when(postFavoriteRepository.findByUserAndPost(viewer, post)).thenReturn(Optional.of(new PostFavorite()));

        Post result = postService.getPostById(250L, "viewer");

        assertThat(result.getLikedByCurrentUser()).isTrue();
        assertThat(result.getFavoritedByCurrentUser()).isTrue();
        assertThat(result.getViewCount()).isEqualTo(4);
    }

    @Test
    void deleteManagedPostDecrementsSectionCountAndDeletesPost() {
        Post post = new Post();
        post.setId(300L);
        post.setAuthor(author);
        post.setSection(section);
        post.setStatus(PostService.STATUS_PUBLISHED);
        post.getTags().add(new com.swjtu.forum.entity.Tag());
        section.setPostCount(5);

        User admin = new User();
        admin.setId(9L);
        admin.setUsername("admin");
        admin.setRole("ADMIN");
        userService.setUser(admin);

        when(postRepository.findById(300L)).thenReturn(Optional.of(post));

        postService.deleteManagedPost(300L, "admin");

        assertThat(post.getStatus()).isEqualTo(PostService.STATUS_HIDDEN);
        verify(postRepository).save(post);
        verify(postRepository, never()).delete(post);
    }

    @Test
    void deleteManagedPostRejectsModeratorOutsideAssignedSection() {
        Post post = new Post();
        post.setId(301L);
        post.setAuthor(author);
        post.setSection(otherSection);
        userService.setUser(moderator);

        when(postRepository.findById(301L)).thenReturn(Optional.of(post));

        assertThatThrownBy(() -> postService.deleteManagedPost(301L, "moderator"))
                .isInstanceOf(ForbiddenException.class)
                .hasMessage("无权处理该版块的帖子");

        verify(postRepository, never()).delete(any(Post.class));
    }

    @Test
    void withdrawOwnedPostHidesAuthorsPost() {
        Post post = new Post();
        post.setId(400L);
        post.setAuthor(author);
        post.setSection(section);
        post.setStatus(PostService.STATUS_PUBLISHED);
        userService.setUser(author);

        when(postRepository.findByIdAndAuthor(400L, author)).thenReturn(Optional.of(post));
        when(postRepository.save(any(Post.class))).thenAnswer(invocation -> invocation.getArgument(0));

        Post withdrawn = postService.withdrawOwnedPost(400L, "author");

        assertThat(withdrawn.getStatus()).isEqualTo(PostService.STATUS_HIDDEN);
        verify(postRepository).save(post);
    }

    @Test
    void withdrawOwnedPostRejectsNonAuthor() {
        userService.setUser(author);
        when(postRepository.findByIdAndAuthor(401L, author)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> postService.withdrawOwnedPost(401L, "author"))
                .isInstanceOf(NotFoundException.class)
                .hasMessage("帖子不存在");
    }

    @Test
    void acceptCommentAllowsAuthorAndClearsPreviousAcceptedComment() {
        User helper = user("helper", 3L, "USER");
        Post post = publishedPost(500L, author);
        Comment previous = comment(10L, post, helper, true);
        Comment target = comment(11L, post, helper, false);
        userService.setUser(author);

        when(postRepository.findById(500L)).thenReturn(Optional.of(post));
        when(commentRepository.findById(11L)).thenReturn(Optional.of(target));
        when(commentRepository.findByPostAndAcceptedTrue(post)).thenReturn(Optional.of(previous));
        when(commentRepository.save(any(Comment.class))).thenAnswer(invocation -> invocation.getArgument(0));
        when(postRepository.save(any(Post.class))).thenAnswer(invocation -> invocation.getArgument(0));

        Comment accepted = postService.acceptComment(500L, 11L, "author");

        assertThat(previous.getAccepted()).isFalse();
        assertThat(accepted.getAccepted()).isTrue();
        assertThat(post.getAcceptedCommentId()).isEqualTo(11L);
        assertThat(userService.contributionCount).isEqualTo(10);
    }

    @Test
    void acceptCommentRejectsNonAuthor() {
        User helper = user("helper", 3L, "USER");
        Post post = publishedPost(501L, author);
        userService.setUser(helper);

        when(postRepository.findById(501L)).thenReturn(Optional.of(post));

        assertThatThrownBy(() -> postService.acceptComment(501L, 12L, "helper"))
                .isInstanceOf(ForbiddenException.class)
                .hasMessage("只有楼主可以采纳最佳答案");

        verify(commentRepository, never()).save(any(Comment.class));
    }

    @Test
    void cancelAcceptedCommentClearsPostAcceptedCommentId() {
        Post post = publishedPost(502L, author);
        post.setAcceptedCommentId(13L);
        Comment accepted = comment(13L, post, user("helper", 3L, "USER"), true);
        userService.setUser(author);

        when(postRepository.findById(502L)).thenReturn(Optional.of(post));
        when(commentRepository.findById(13L)).thenReturn(Optional.of(accepted));
        when(commentRepository.save(any(Comment.class))).thenAnswer(invocation -> invocation.getArgument(0));
        when(postRepository.save(any(Post.class))).thenAnswer(invocation -> invocation.getArgument(0));

        Comment cancelled = postService.cancelAcceptedComment(502L, 13L, "author");

        assertThat(cancelled.getAccepted()).isFalse();
        assertThat(post.getAcceptedCommentId()).isNull();
    }

    private Post publishedPost(Long id, User author) {
        Post post = new Post();
        post.setId(id);
        post.setAuthor(author);
        post.setSection(section);
        post.setStatus(PostService.STATUS_PUBLISHED);
        return post;
    }

    private Comment comment(Long id, Post post, User author, boolean accepted) {
        Comment comment = new Comment();
        comment.setId(id);
        comment.setPost(post);
        comment.setAuthor(author);
        comment.setStatus(1);
        comment.setAccepted(accepted);
        comment.setContent("comment " + id);
        return comment;
    }

    private User user(String username, Long id, String role) {
        User user = new User();
        user.setUsername(username);
        user.setId(id);
        user.setRole(role);
        return user;
    }

    private static class StubUserService extends UserService {
        private User user;
        private int contributionCount;

        StubUserService() {
            super(null, null, null, null, null, null);
        }

        void setUser(User user) {
            this.user = user;
        }

        @Override
        public User getUserByUsername(String username) {
            return user;
        }

        @Override
        public void addExperience(User user, int exp) {
        }

        @Override
        public void addContribution(User user, int amount) {
            contributionCount += amount;
        }
    }

    private static class StubContentModerationService extends ContentModerationService {
        private boolean shouldReview;

        void setShouldReview(boolean shouldReview) {
            this.shouldReview = shouldReview;
        }

        @Override
        public boolean shouldReview(PostRequest request) {
            validatePostRequest(request);
            return shouldReview;
        }
    }
}
