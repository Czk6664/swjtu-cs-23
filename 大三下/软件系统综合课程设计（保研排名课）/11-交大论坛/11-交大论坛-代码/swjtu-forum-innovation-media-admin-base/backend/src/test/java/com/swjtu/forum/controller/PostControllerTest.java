package com.swjtu.forum.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.swjtu.forum.dto.CommentRequest;
import com.swjtu.forum.dto.PostRequest;
import com.swjtu.forum.entity.Comment;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.exception.GlobalExceptionHandler;
import com.swjtu.forum.service.AnalyticsService;
import com.swjtu.forum.service.GrowthDiscoveryService;
import com.swjtu.forum.service.PostService;
import com.swjtu.forum.service.ReportService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@ExtendWith(MockitoExtension.class)
class PostControllerTest {

    private MockMvc mockMvc;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Mock
    private PostService postService;

    @Mock
    private GrowthDiscoveryService growthDiscoveryService;

    @Mock
    private ReportService reportService;

    @Mock
    private AnalyticsService analyticsService;

    @BeforeEach
    void setUp() {
        LocalValidatorFactoryBean validator = new LocalValidatorFactoryBean();
        validator.afterPropertiesSet();
        PostController controller = new PostController(postService, growthDiscoveryService, reportService, analyticsService);
        mockMvc = MockMvcBuilders.standaloneSetup(controller)
                .setControllerAdvice(new GlobalExceptionHandler())
                .setValidator(validator)
                .build();
    }

    private Post createSamplePost() {
        User author = new User();
        author.setId(1L);
        author.setUsername("author");

        Section section = new Section();
        section.setId(1L);
        section.setName("学术交流");

        Post post = new Post();
        post.setId(1L);
        post.setTitle("测试帖子");
        post.setContent("帖子内容");
        post.setAuthor(author);
        post.setSection(section);
        post.setStatus(1); // PUBLISHED
        post.setLikeCount(0);
        post.setCommentCount(0);
        post.setCollectCount(0);
        post.setCreatedAt(LocalDateTime.now());
        return post;
    }

    @Test
    void getPostsReturnsPage() throws Exception {
        Post post = createSamplePost();
        Page<Post> page = new PageImpl<>(List.of(post), PageRequest.of(0, 20), 1);

        when(postService.getPosts(any())).thenReturn(page);

        mockMvc.perform(get("/posts"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.content[0].title").value("测试帖子"));
    }

    @Test
    void getPostByIdReturnsPost() throws Exception {
        Post post = createSamplePost();

        when(postService.getPostById(eq(1L), any())).thenReturn(post);

        mockMvc.perform(get("/posts/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.title").value("测试帖子"));
    }

    @Test
    void getCommentsReturnsPage() throws Exception {
        Comment comment = new Comment();
        comment.setId(1L);
        comment.setContent("评论内容");
        Page<Comment> page = new PageImpl<>(List.of(comment), PageRequest.of(0, 20), 1);

        when(postService.getComments(eq(1L), any(), any())).thenReturn(page);

        mockMvc.perform(get("/posts/1/comments"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.content[0].content").value("评论内容"));
    }

    @Test
    void getHotPostsReturnsPage() throws Exception {
        Post post = createSamplePost();
        Page<Post> page = new PageImpl<>(List.of(post), PageRequest.of(0, 20), 1);

        when(postService.getHotPosts(any())).thenReturn(page);

        mockMvc.perform(get("/posts/hot"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    void searchPostsReturnsPage() throws Exception {
        Post post = createSamplePost();
        Page<Post> page = new PageImpl<>(List.of(post), PageRequest.of(0, 20), 1);

        when(growthDiscoveryService.searchPosts(eq("测试"), any())).thenReturn(page);

        mockMvc.perform(get("/posts/search").param("keyword", "测试"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    void trendingTagsReturnsPublicReadonlyData() throws Exception {
        when(analyticsService.trendingTags()).thenReturn(List.of(Map.of("tag", "考研", "count", 3)));

        mockMvc.perform(get("/posts/trending-tags"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data[0].tag").value("考研"));
    }
}
