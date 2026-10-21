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
import jakarta.persistence.criteria.Predicate;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.Comparator;
import java.util.List;
import java.util.Set;

@Service
@RequiredArgsConstructor
public class ReportService {

    private static final Set<String> ALLOWED_REASONS = Set.of("垃圾广告", "骚扰辱骂", "违法违规", "虚假信息", "其他");
    private static final String SORT_PRIORITY = "priority";

    private final ReportRepository reportRepository;
    private final PostRepository postRepository;
    private final OperationLogRepository operationLogRepository;
    private final ReportReviewLogRepository reportReviewLogRepository;
    private final UserService userService;
    private final NotificationService notificationService;

    @Transactional
    public Report createPostReport(Long postId, CreateReportRequest request, String username) {
        User reporter = userService.getUserByUsername(username);
        Post post = postRepository.findById(postId).orElseThrow(() -> new NotFoundException("帖子不存在"));
        String reason = request.getReason().trim();
        if (!ALLOWED_REASONS.contains(reason)) {
            throw new ApiException(400, "举报原因不合法");
        }
        if (post.getAuthor() != null && post.getAuthor().getId().equals(reporter.getId())) {
            throw new ApiException(400, "不能举报自己的帖子");
        }
        if (reportRepository.existsByReporterAndPostAndStatus(reporter, post, Report.STATUS_PENDING)) {
            throw new ApiException(400, "你已举报过该帖子，请等待处理");
        }

        Report report = new Report();
        report.setReporter(reporter);
        report.setPost(post);
        report.setReason(reason);
        report.setDetail(trimToNull(request.getDetail()));
        return reportRepository.save(report);
    }

    public Page<Report> listReports(Integer status, String reason, String sort, Pageable pageable) {
        Specification<Report> specification = (root, query, criteriaBuilder) -> {
            Predicate predicate = criteriaBuilder.conjunction();
            if (status != null) {
                predicate = criteriaBuilder.and(predicate, criteriaBuilder.equal(root.get("status"), status));
            }
            if (StringUtils.hasText(reason)) {
                predicate = criteriaBuilder.and(predicate, criteriaBuilder.equal(root.get("reason"), reason.trim()));
            }
            return predicate;
        };

        Page<Report> page = reportRepository.findAll(specification, pageable);
        List<Report> reports = page.getContent().stream()
                .peek(this::attachReviewHistory)
                .toList();
        if (!SORT_PRIORITY.equalsIgnoreCase(sort)) {
            return new PageImpl<>(reports, pageable, page.getTotalElements());
        }

        List<Report> sorted = reports.stream()
                .sorted(reportPriorityComparator())
                .toList();
        return new PageImpl<>(sorted, pageable, page.getTotalElements());
    }

    @Transactional
    public Report reviewReport(Long reportId, ReviewReportRequest request, String username) {
        Report report = reportRepository.findById(reportId).orElseThrow(() -> new NotFoundException("举报不存在"));
        User reviewer = userService.getUserByUsername(username);
        Report saved = applyReview(report, Boolean.TRUE.equals(request.getAccept()), request.getReviewNote(), reviewer);
        attachReviewHistory(saved);
        return saved;
    }

    @Transactional
    public BulkReportReviewResponse bulkReviewReports(BulkReviewReportRequest request, String username) {
        User reviewer = userService.getUserByUsername(username);
        List<Long> reportIds = request.getReportIds().stream().distinct().toList();
        if (reportIds.isEmpty()) {
            throw new ApiException(400, "批量处理的举报不能为空");
        }

        List<Report> reports = reportRepository.findAllById(reportIds);
        if (reports.size() != reportIds.size()) {
            throw new NotFoundException("部分举报不存在");
        }
        if (reports.stream().anyMatch(report -> report.getStatus() != Report.STATUS_PENDING)) {
            throw new ApiException(400, "仅支持批量处理待处理举报");
        }

        reports.forEach(report -> applyReview(report, Boolean.TRUE.equals(request.getAccept()), request.getReviewNote(), reviewer));
        return new BulkReportReviewResponse(reports.size());
    }

    private Report applyReview(Report report, boolean accept, String reviewNote, User reviewer) {
        if (report.getStatus() != Report.STATUS_PENDING) {
            throw new ApiException(400, "举报已处理");
        }

        report.setReviewer(reviewer);
        report.setReviewNote(trimToNull(reviewNote));
        report.setStatus(accept ? Report.STATUS_ACCEPTED : Report.STATUS_REJECTED);
        Report saved = reportRepository.save(report);

        // Accepting a report must act on the reported content, not just close the ticket:
        // hide the offending post so the moderation loop actually removes it from view.
        if (accept) {
            Post reportedPost = saved.getPost();
            if (reportedPost != null && reportedPost.getStatus() != null
                    && reportedPost.getStatus() == PostService.STATUS_PUBLISHED) {
                reportedPost.setStatus(PostService.STATUS_HIDDEN);
                postRepository.save(reportedPost);
            }
        }

        OperationLog log = new OperationLog();
        log.setActor(reviewer);
        log.setAction(accept ? "ACCEPT_REPORT" : "REJECT_REPORT");
        log.setTargetType("REPORT");
        log.setTargetId(saved.getId());
        log.setDetail("处理帖子举报: postId=" + (saved.getPost() == null ? null : saved.getPost().getId()));
        operationLogRepository.save(log);

        ReportReviewLog reviewLog = new ReportReviewLog();
        reviewLog.setReport(saved);
        reviewLog.setActor(reviewer);
        reviewLog.setAction(accept ? "ACCEPT" : "REJECT");
        reviewLog.setNote(trimToNull(reviewNote));
        reportReviewLogRepository.save(reviewLog);

        notificationService.notify(saved.getReporter(),
                com.swjtu.forum.entity.Notification.TYPE_REPORT,
                accept ? "你的举报已被采纳" : "你的举报已被驳回",
                accept ? "感谢反馈，被举报内容已下架处理。" : "经核实，被举报内容未违反社区规范。",
                saved.getPost() == null ? null : saved.getPost().getId(), "POST");
        return saved;
    }

    private void attachReviewHistory(Report report) {
        report.setReviewLogs(reportReviewLogRepository.findByReportOrderByCreatedAtDesc(report));
    }

    private Comparator<Report> reportPriorityComparator() {
        return Comparator.comparingInt(this::priorityScore)
                .reversed()
                .thenComparing(Report::getCreatedAt, Comparator.nullsLast(Comparator.reverseOrder()));
    }

    private int priorityScore(Report report) {
        int score = report.getStatus() == Report.STATUS_PENDING ? 100 : 0;
        if (report.getCreatedAt() != null) {
            long ageHours = Math.max(0, Duration.between(report.getCreatedAt(), LocalDateTime.now()).toHours());
            score += Math.min((int) ageHours, 72);
        }
        if (report.getPost() != null && report.getPost().getCommentCount() != null) {
            score += Math.min(report.getPost().getCommentCount(), 20);
        }
        if (StringUtils.hasText(report.getDetail())) {
            score += 5;
        }
        return score;
    }

    private String trimToNull(String value) {
        if (!StringUtils.hasText(value)) {
            return null;
        }
        return value.trim();
    }
}
