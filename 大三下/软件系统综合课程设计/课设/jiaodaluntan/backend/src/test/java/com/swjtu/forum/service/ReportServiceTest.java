package com.swjtu.forum.service;

import com.swjtu.forum.dto.BulkReportReviewResponse;
import com.swjtu.forum.dto.BulkReviewReportRequest;
import com.swjtu.forum.dto.CreateReportRequest;
import com.swjtu.forum.dto.ReviewReportRequest;
import com.swjtu.forum.entity.OperationLog;
import com.swjtu.forum.entity.Post;
import com.swjtu.forum.entity.Report;
import com.swjtu.forum.entity.ReportReviewLog;
import com.swjtu.forum.entity.User;
import com.swjtu.forum.exception.ApiException;
import com.swjtu.forum.exception.NotFoundException;
import com.swjtu.forum.repository.OperationLogRepository;
import com.swjtu.forum.repository.PostRepository;
import com.swjtu.forum.repository.ReportRepository;
import com.swjtu.forum.repository.ReportReviewLogRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ReportServiceTest {

    @Mock
    private ReportRepository reportRepository;
    @Mock
    private PostRepository postRepository;
    @Mock
    private OperationLogRepository operationLogRepository;
    @Mock
    private ReportReviewLogRepository reportReviewLogRepository;
    @Mock
    private NotificationService notificationService;

    private ReportService reportService;
    private StubUserService userService;
    private User reporter;
    private User reviewer;
    private Post post;

    @BeforeEach
    void setUp() {
        userService = new StubUserService();
        reportService = new ReportService(reportRepository, postRepository, operationLogRepository, reportReviewLogRepository, userService, notificationService);

        reporter = new User();
        reporter.setId(1L);
        reporter.setUsername("reporter");

        reviewer = new User();
        reviewer.setId(2L);
        reviewer.setUsername("moderator");
        reviewer.setRole("MODERATOR");

        post = new Post();
        post.setId(10L);
        post.setTitle("帖子");
        post.setCommentCount(6);
    }

    @Test
    void createPostReportRejectsMissingPost() {
        CreateReportRequest request = new CreateReportRequest();
        request.setReason("垃圾广告");
        userService.setUser(reporter);

        when(postRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> reportService.createPostReport(99L, request, "reporter"))
                .isInstanceOf(NotFoundException.class)
                .hasMessage("帖子不存在");

        verify(reportRepository, never()).save(any(Report.class));
    }

    @Test
    void createPostReportRejectsInvalidReason() {
        CreateReportRequest request = new CreateReportRequest();
        request.setReason("无效原因");
        userService.setUser(reporter);

        when(postRepository.findById(10L)).thenReturn(Optional.of(post));

        assertThatThrownBy(() -> reportService.createPostReport(10L, request, "reporter"))
                .isInstanceOf(ApiException.class)
                .hasMessage("举报原因不合法");

        verify(reportRepository, never()).existsByReporterAndPostAndStatus(any(User.class), any(Post.class), any());
        verify(reportRepository, never()).save(any(Report.class));
    }

    @Test
    void createPostReportRejectsSelfReport() {
        CreateReportRequest request = new CreateReportRequest();
        request.setReason("垃圾广告");
        post.setAuthor(reporter);
        userService.setUser(reporter);

        when(postRepository.findById(10L)).thenReturn(Optional.of(post));

        assertThatThrownBy(() -> reportService.createPostReport(10L, request, "reporter"))
                .isInstanceOf(ApiException.class)
                .hasMessage("不能举报自己的帖子");

        verify(reportRepository, never()).save(any(Report.class));
    }

    @Test
    void createPostReportRejectsDuplicatePendingReport() {
        CreateReportRequest request = new CreateReportRequest();
        request.setReason("骚扰辱骂");
        post.setAuthor(otherUser(3L, "author"));
        userService.setUser(reporter);

        when(postRepository.findById(10L)).thenReturn(Optional.of(post));
        when(reportRepository.existsByReporterAndPostAndStatus(reporter, post, Report.STATUS_PENDING)).thenReturn(true);

        assertThatThrownBy(() -> reportService.createPostReport(10L, request, "reporter"))
                .isInstanceOf(ApiException.class)
                .hasMessage("你已举报过该帖子，请等待处理");

        verify(reportRepository, never()).save(any(Report.class));
    }

    @Test
    void createPostReportTrimsReasonAndDetailBeforeSavingPendingReport() {
        CreateReportRequest request = new CreateReportRequest();
        request.setReason("  虚假信息  ");
        request.setDetail("  证据链接在评论区  ");
        post.setAuthor(otherUser(3L, "author"));
        userService.setUser(reporter);

        when(postRepository.findById(10L)).thenReturn(Optional.of(post));
        when(reportRepository.existsByReporterAndPostAndStatus(reporter, post, Report.STATUS_PENDING)).thenReturn(false);
        when(reportRepository.save(any(Report.class))).thenAnswer(invocation -> invocation.getArgument(0));

        Report saved = reportService.createPostReport(10L, request, "reporter");

        assertThat(saved.getReporter()).isEqualTo(reporter);
        assertThat(saved.getPost()).isEqualTo(post);
        assertThat(saved.getReason()).isEqualTo("虚假信息");
        assertThat(saved.getDetail()).isEqualTo("证据链接在评论区");
        assertThat(saved.getStatus()).isEqualTo(Report.STATUS_PENDING);
    }

    @Test
    void listReportsFiltersByReasonAndSortsByPriority() {
        Report older = buildPendingReport(1L, "垃圾广告", LocalDateTime.now().minusHours(20), null);
        Report newerWithDetail = buildPendingReport(2L, "垃圾广告", LocalDateTime.now().minusHours(5), "有补充说明");

        when(reportRepository.findAll(any(org.springframework.data.jpa.domain.Specification.class), eq(PageRequest.of(0, 10))))
                .thenReturn(new PageImpl<>(List.of(newerWithDetail, older), PageRequest.of(0, 10), 2));
        when(reportReviewLogRepository.findByReportOrderByCreatedAtDesc(any(Report.class))).thenReturn(List.of());

        List<Report> result = reportService.listReports(0, "垃圾广告", "priority", PageRequest.of(0, 10)).getContent();

        assertThat(result).hasSize(2);
        assertThat(result.get(0).getId()).isEqualTo(1L);
        assertThat(result.get(1).getId()).isEqualTo(2L);
    }

    @Test
    void reviewReportSavesHistoryAndOperationLog() {
        Report report = buildPendingReport(3L, "违法违规", LocalDateTime.now().minusHours(2), "举报详情");
        userService.setUser(reviewer);

        ReviewReportRequest request = new ReviewReportRequest();
        request.setAccept(true);
        request.setReviewNote("属实，已处理");

        when(reportRepository.findById(3L)).thenReturn(Optional.of(report));
        when(reportRepository.save(any(Report.class))).thenAnswer(invocation -> invocation.getArgument(0));
        when(reportReviewLogRepository.findByReportOrderByCreatedAtDesc(any(Report.class))).thenReturn(List.of());

        Report saved = reportService.reviewReport(3L, request, "moderator");

        assertThat(saved.getStatus()).isEqualTo(Report.STATUS_ACCEPTED);
        assertThat(saved.getReviewNote()).isEqualTo("属实，已处理");

        ArgumentCaptor<OperationLog> operationLogCaptor = ArgumentCaptor.forClass(OperationLog.class);
        verify(operationLogRepository).save(operationLogCaptor.capture());
        assertThat(operationLogCaptor.getValue().getAction()).isEqualTo("ACCEPT_REPORT");

        ArgumentCaptor<ReportReviewLog> reviewLogCaptor = ArgumentCaptor.forClass(ReportReviewLog.class);
        verify(reportReviewLogRepository).save(reviewLogCaptor.capture());
        assertThat(reviewLogCaptor.getValue().getAction()).isEqualTo("ACCEPT");
        assertThat(reviewLogCaptor.getValue().getNote()).isEqualTo("属实，已处理");
    }

    @Test
    void acceptingReportHidesTheReportedPost() {
        post.setStatus(PostService.STATUS_PUBLISHED);
        Report report = buildPendingReport(7L, "违法违规", LocalDateTime.now().minusHours(1), null);
        userService.setUser(reviewer);

        ReviewReportRequest request = new ReviewReportRequest();
        request.setAccept(true);

        when(reportRepository.findById(7L)).thenReturn(Optional.of(report));
        when(reportRepository.save(any(Report.class))).thenAnswer(invocation -> invocation.getArgument(0));
        when(reportReviewLogRepository.findByReportOrderByCreatedAtDesc(any(Report.class))).thenReturn(List.of());

        reportService.reviewReport(7L, request, "moderator");

        assertThat(post.getStatus()).isEqualTo(PostService.STATUS_HIDDEN);
        verify(postRepository).save(post);
    }

    @Test
    void rejectingReportLeavesPostUntouched() {
        post.setStatus(PostService.STATUS_PUBLISHED);
        Report report = buildPendingReport(8L, "违法违规", LocalDateTime.now().minusHours(1), null);
        userService.setUser(reviewer);

        ReviewReportRequest request = new ReviewReportRequest();
        request.setAccept(false);

        when(reportRepository.findById(8L)).thenReturn(Optional.of(report));
        when(reportRepository.save(any(Report.class))).thenAnswer(invocation -> invocation.getArgument(0));
        when(reportReviewLogRepository.findByReportOrderByCreatedAtDesc(any(Report.class))).thenReturn(List.of());

        reportService.reviewReport(8L, request, "moderator");

        assertThat(post.getStatus()).isEqualTo(PostService.STATUS_PUBLISHED);
        verify(postRepository, never()).save(any(Post.class));
    }

    @Test
    void bulkReviewRejectsNonPendingReports() {
        Report pending = buildPendingReport(4L, "其他", LocalDateTime.now().minusHours(1), null);
        Report handled = buildPendingReport(5L, "其他", LocalDateTime.now().minusHours(1), null);
        handled.setStatus(Report.STATUS_REJECTED);
        userService.setUser(reviewer);

        BulkReviewReportRequest request = new BulkReviewReportRequest();
        request.setReportIds(List.of(4L, 5L));
        request.setAccept(false);
        request.setReviewNote("批量驳回");

        when(reportRepository.findAllById(List.of(4L, 5L))).thenReturn(List.of(pending, handled));

        assertThatThrownBy(() -> reportService.bulkReviewReports(request, "moderator"))
                .isInstanceOf(ApiException.class)
                .hasMessage("仅支持批量处理待处理举报");
    }

    @Test
    void bulkReviewProcessesAllPendingReports() {
        Report first = buildPendingReport(6L, "骚扰辱骂", LocalDateTime.now().minusHours(2), null);
        Report second = buildPendingReport(7L, "骚扰辱骂", LocalDateTime.now().minusHours(3), "补充信息");
        userService.setUser(reviewer);

        BulkReviewReportRequest request = new BulkReviewReportRequest();
        request.setReportIds(List.of(6L, 7L));
        request.setAccept(true);
        request.setReviewNote("批量采纳");

        when(reportRepository.findAllById(List.of(6L, 7L))).thenReturn(List.of(first, second));
        when(reportRepository.save(any(Report.class))).thenAnswer(invocation -> invocation.getArgument(0));

        BulkReportReviewResponse response = reportService.bulkReviewReports(request, "moderator");

        assertThat(response.getProcessedCount()).isEqualTo(2);
        assertThat(first.getStatus()).isEqualTo(Report.STATUS_ACCEPTED);
        assertThat(second.getStatus()).isEqualTo(Report.STATUS_ACCEPTED);
        verify(reportReviewLogRepository, org.mockito.Mockito.times(2)).save(any(ReportReviewLog.class));
    }

    private Report buildPendingReport(Long id, String reason, LocalDateTime createdAt, String detail) {
        Report report = new Report();
        report.setId(id);
        report.setReporter(reporter);
        report.setPost(post);
        report.setReason(reason);
        report.setDetail(detail);
        report.setStatus(Report.STATUS_PENDING);
        report.setCreatedAt(createdAt);
        return report;
    }

    private User otherUser(Long id, String username) {
        User user = new User();
        user.setId(id);
        user.setUsername(username);
        return user;
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
}
