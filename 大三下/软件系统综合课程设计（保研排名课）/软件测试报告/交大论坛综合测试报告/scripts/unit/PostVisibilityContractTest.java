package com.swjtu.forum.service;

import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.entity.User;
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
class PostVisibilityContractTest {

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
    private BadgeService badgeService;

    private PostService postService;
    private StubUserService userService;
    private StubContentModerationService contentModerationService;
    private User author;
    private User moderator;
    private Section moderatedSection;
    private Post hiddenPost;

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
                null,
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

        moderatedSection = new Section();
        moderatedSection.setId(8L);
        moderatedSection.setName("Academic");
        moderatedSection.setModerator(moderator);

        hiddenPost = new Post();
        hiddenPost.setId(9L);
        hiddenPost.setAuthor(author);
        hiddenPost.setSection(moderatedSection);
        hiddenPost.setStatus(PostService.STATUS_HIDDEN);
        hiddenPost.setViewCount(12);
    }

    @Test
    void guestCannotReadNonPublicPost() {
        when(postRepository.findById(9L)).thenReturn(Optional.of(hiddenPost));

        assertThatThrownBy(() -> postService.getPostById(9L, null))
                .isInstanceOf(NotFoundException.class)
                .hasMessage("帖子不存在");
    }

    @Test
    void authorCanReadOwnNonPublicPostWithoutIncreasingViews() {
        userService.setUser(author);
        when(postRepository.findById(9L)).thenReturn(Optional.of(hiddenPost));
        when(postBrowseHistoryRepository.findByUserAndPost(author, hiddenPost)).thenReturn(Optional.empty());

        Post result = postService.getPostById(9L, "author");

        assertThat(result).isSameAs(hiddenPost);
        assertThat(result.getViewCount()).isEqualTo(12);
        verify(postRepository, never()).save(any(Post.class));
    }

    @Test
    void assignedModeratorCanReadHiddenPost() {
        userService.setUser(moderator);
        when(postRepository.findById(9L)).thenReturn(Optional.of(hiddenPost));
        when(postBrowseHistoryRepository.findByUserAndPost(moderator, hiddenPost)).thenReturn(Optional.empty());

        Post result = postService.getPostById(9L, "moderator");

        assertThat(result).isSameAs(hiddenPost);
    }

    private static class StubUserService extends UserService {
        private User user;

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
    }

    private static class StubContentModerationService extends ContentModerationService {
    }
}
