package com.swjtu.forum.controller;

import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.Report;
import com.swjtu.forum.entity.Section;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.exception.GlobalExceptionHandler;
import com.swjtu.forum.service.AdminOpsService;
import com.swjtu.forum.service.GrowthDiscoveryService;
import com.swjtu.forum.service.ReportService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@ExtendWith(MockitoExtension.class)
class AdminControllerTest {

    private MockMvc mockMvc;

    @Mock
    private AdminOpsService adminOpsService;

    @Mock
    private GrowthDiscoveryService growthDiscoveryService;

    @Mock
    private ReportService reportService;

    @Mock
    private com.swjtu.forum.service.AnalyticsService analyticsService;

    @BeforeEach
    void setUp() {
        AdminController controller = new AdminController(adminOpsService, growthDiscoveryService, reportService, analyticsService);
        mockMvc = MockMvcBuilders.standaloneSetup(controller)
                .setControllerAdvice(new GlobalExceptionHandler())
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
        post.setTitle("待审核帖子");
        post.setContent("内容");
        post.setAuthor(author);
        post.setSection(section);
        post.setStatus(0); // PENDING
        return post;
    }

    @Test
    void getPendingPostsReturnsPage() throws Exception {
        Post post = createSamplePost();
        Page<Post> page = new PageImpl<>(List.of(post), PageRequest.of(0, 20), 1);

        when(adminOpsService.getPendingPosts(any())).thenReturn(page);

        mockMvc.perform(get("/admin/posts/pending").principal(() -> "moderator"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.content[0].status").value(0));
    }

    @Test
    void getReportsReturnsPage() throws Exception {
        Report report = new Report();
        report.setId(1L);
        report.setStatus(0);

        Page<Report> page = new PageImpl<>(List.of(report), PageRequest.of(0, 20), 1);

        when(reportService.listReports(any(), any(), any(), any())).thenReturn(page);

        mockMvc.perform(get("/admin/reports").principal(() -> "moderator"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    void listUsersReturnsPage() throws Exception {
        User user = new User();
        user.setId(1L);
        user.setUsername("testuser");
        user.setRole("USER");

        Page<User> page = new PageImpl<>(List.of(user), PageRequest.of(0, 20), 1);

        when(adminOpsService.listUsers(any())).thenReturn(page);

        mockMvc.perform(get("/admin/users").principal(() -> "admin"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.content[0].username").value("testuser"));
    }

    @Test
    void getLogsReturnsPage() throws Exception {
        Page<com.swjtu.forum.entity.OperationLog> page = new PageImpl<>(List.of(), PageRequest.of(0, 20), 0);

        when(adminOpsService.getLogs(any())).thenReturn(page);

        mockMvc.perform(get("/admin/logs").principal(() -> "admin"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }
}
