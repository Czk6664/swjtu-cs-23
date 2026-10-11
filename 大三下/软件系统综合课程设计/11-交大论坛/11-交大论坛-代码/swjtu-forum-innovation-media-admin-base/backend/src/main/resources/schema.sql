-- Phase 1 aligned schema for the campus forum demo.
-- Source of truth in this file follows the entities and admin/user flows already used by the app.

CREATE DATABASE IF NOT EXISTS swjtu_forum DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE swjtu_forum;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '加密密码',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    student_id VARCHAR(20) COMMENT '学号',
    college VARCHAR(50) COMMENT '学院',
    major VARCHAR(50) COMMENT '专业',
    campus_email VARCHAR(100) COMMENT '校园邮箱',
    campus_identity_status VARCHAR(20) NOT NULL DEFAULT 'UNVERIFIED' COMMENT '校园身份状态: UNVERIFIED/VERIFIED/FAILED',
    campus_verified BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否已完成校园认证',
    campus_verification_message VARCHAR(200) COMMENT '最近一次校园认证结果说明',
    campus_verified_at TIMESTAMP NULL COMMENT '校园认证完成时间',
    campus_profile_synced_at TIMESTAMP NULL COMMENT '校园资料同步时间',
    avatar VARCHAR(200) COMMENT '头像 URL',
    bio VARCHAR(500) COMMENT '个人简介',
    level INT NOT NULL DEFAULT 1 COMMENT '等级',
    exp INT NOT NULL DEFAULT 0 COMMENT '经验值',
    points INT NOT NULL DEFAULT 0 COMMENT '积分',
    consecutive_days INT NOT NULL DEFAULT 0 COMMENT '连续签到天数',
    role VARCHAR(20) NOT NULL DEFAULT 'USER' COMMENT '角色: USER/MODERATOR/ADMIN',
    enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '账号是否可用',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_users_username (username),
    INDEX idx_users_email (email),
    INDEX idx_users_role_enabled (role, enabled),
    INDEX idx_users_campus_status (campus_identity_status, campus_verified)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

CREATE TABLE IF NOT EXISTS sections (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '版块名称',
    description VARCHAR(200) COMMENT '版块描述',
    icon VARCHAR(200) COMMENT '图标 URL',
    post_count INT NOT NULL DEFAULT 0 COMMENT '帖子数缓存',
    moderator_id BIGINT COMMENT '版主用户 ID',
    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序值',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_sections_moderator FOREIGN KEY (moderator_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_sections_sort_order (sort_order),
    INDEX idx_sections_moderator_id (moderator_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='版块表';

CREATE TABLE IF NOT EXISTS tags (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '标签名称',
    category VARCHAR(50) COMMENT '标签分类',
    use_count INT NOT NULL DEFAULT 0 COMMENT '使用次数',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_tags_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='标签表';

CREATE TABLE IF NOT EXISTS posts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '作者 ID',
    section_id BIGINT NOT NULL COMMENT '版块 ID',
    title VARCHAR(200) NOT NULL COMMENT '标题',
    content TEXT NOT NULL COMMENT '正文',
    cover_image VARCHAR(500) COMMENT '封面图 URL',
    view_count INT NOT NULL DEFAULT 0 COMMENT '浏览量',
    like_count INT NOT NULL DEFAULT 0 COMMENT '点赞数',
    comment_count INT NOT NULL DEFAULT 0 COMMENT '评论数',
    collect_count INT NOT NULL DEFAULT 0 COMMENT '收藏数',
    heat_score INT NOT NULL DEFAULT 0 COMMENT '热度分',
    status INT NOT NULL DEFAULT 1 COMMENT '状态: 0待审核 1已发布 2已隐藏 3已驳回',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_posts_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_posts_section FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE,
    INDEX idx_posts_section_status_created (section_id, status, created_at),
    INDEX idx_posts_user_created (user_id, created_at),
    INDEX idx_posts_status_created (status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帖子表';

CREATE TABLE IF NOT EXISTS post_tags (
    post_id BIGINT NOT NULL COMMENT '帖子 ID',
    tag_id BIGINT NOT NULL COMMENT '标签 ID',
    PRIMARY KEY (post_id, tag_id),
    CONSTRAINT fk_post_tags_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    CONSTRAINT fk_post_tags_tag FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    INDEX idx_post_tags_tag_id (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帖子标签关联表';

CREATE TABLE IF NOT EXISTS user_tags (
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    tag_id BIGINT NOT NULL COMMENT '标签 ID',
    PRIMARY KEY (user_id, tag_id),
    CONSTRAINT fk_user_tags_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_tags_tag FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    INDEX idx_user_tags_tag_id (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户兴趣标签关联表';

CREATE TABLE IF NOT EXISTS comments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    post_id BIGINT NOT NULL COMMENT '帖子 ID',
    user_id BIGINT NOT NULL COMMENT '评论作者 ID',
    parent_id BIGINT COMMENT '父评论 ID',
    content TEXT NOT NULL COMMENT '评论内容',
    like_count INT NOT NULL DEFAULT 0 COMMENT '点赞数',
    status INT NOT NULL DEFAULT 1 COMMENT '状态: 1显示 2隐藏',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_comments_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    CONSTRAINT fk_comments_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_comments_parent FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE,
    INDEX idx_comments_post_status_created (post_id, status, created_at),
    INDEX idx_comments_user_id (user_id),
    INDEX idx_comments_parent_id (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论表';

CREATE TABLE IF NOT EXISTS post_likes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    post_id BIGINT NOT NULL COMMENT '帖子 ID',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_post_likes_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_post_likes_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    UNIQUE KEY uk_post_likes_user_post (user_id, post_id),
    INDEX idx_post_likes_post_id (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帖子点赞表';

CREATE TABLE IF NOT EXISTS comment_likes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    comment_id BIGINT NOT NULL COMMENT '评论 ID',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_comment_likes_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_comment_likes_comment FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE,
    UNIQUE KEY uk_comment_likes_user_comment (user_id, comment_id),
    INDEX idx_comment_likes_comment_id (comment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论点赞表';

CREATE TABLE IF NOT EXISTS post_favorites (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    post_id BIGINT NOT NULL COMMENT '帖子 ID',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_post_favorites_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_post_favorites_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    UNIQUE KEY uk_post_favorites_user_post (user_id, post_id),
    INDEX idx_post_favorites_post_id (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帖子收藏表';

CREATE TABLE IF NOT EXISTS post_browse_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    post_id BIGINT NOT NULL COMMENT '帖子 ID',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次浏览时间',
    last_viewed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近浏览时间',
    CONSTRAINT fk_post_browse_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_post_browse_history_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    UNIQUE KEY uk_post_browse_history_user_post (user_id, post_id),
    INDEX idx_post_browse_history_last_viewed (user_id, last_viewed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帖子浏览记录表';

CREATE TABLE IF NOT EXISTS operation_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    actor_id BIGINT COMMENT '操作者 ID',
    action VARCHAR(64) NOT NULL COMMENT '动作编码',
    target_type VARCHAR(64) NOT NULL COMMENT '对象类型',
    target_id BIGINT COMMENT '对象 ID',
    detail VARCHAR(500) COMMENT '详情',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_operation_logs_actor FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_operation_logs_created_at (created_at),
    INDEX idx_operation_logs_target (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

CREATE TABLE IF NOT EXISTS points_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    change_type VARCHAR(64) NOT NULL COMMENT '积分变动类型',
    points_delta INT NOT NULL DEFAULT 0 COMMENT '积分变化值',
    exp_delta INT NOT NULL DEFAULT 0 COMMENT '经验变化值',
    current_points INT NOT NULL DEFAULT 0 COMMENT '当前积分',
    current_exp INT NOT NULL DEFAULT 0 COMMENT '当前经验',
    note VARCHAR(200) COMMENT '备注',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_points_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_points_history_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='积分历史表';

CREATE TABLE IF NOT EXISTS reward_items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '奖励名称',
    description VARCHAR(500) COMMENT '奖励说明',
    cost_points INT NOT NULL DEFAULT 0 COMMENT '兑换所需积分',
    stock INT NOT NULL DEFAULT 0 COMMENT '库存',
    status INT NOT NULL DEFAULT 1 COMMENT '状态: 1启用 0停用',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_reward_items_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='奖励项表';

CREATE TABLE IF NOT EXISTS redemption_requests (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '申请用户 ID',
    reward_id BIGINT NOT NULL COMMENT '奖励 ID',
    points_cost INT NOT NULL DEFAULT 0 COMMENT '积分消耗',
    status INT NOT NULL DEFAULT 0 COMMENT '状态: 0待审核 1通过 2驳回',
    review_note VARCHAR(300) COMMENT '审核备注',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_redemption_requests_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_redemption_requests_reward FOREIGN KEY (reward_id) REFERENCES reward_items(id) ON DELETE CASCADE,
    INDEX idx_redemption_requests_status_created (status, created_at),
    INDEX idx_redemption_requests_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='兑换申请表';

CREATE TABLE IF NOT EXISTS reports (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reporter_id BIGINT NOT NULL COMMENT '举报用户 ID',
    post_id BIGINT NOT NULL COMMENT '被举报帖子 ID',
    reviewer_id BIGINT COMMENT '处理人 ID',
    reason VARCHAR(32) NOT NULL COMMENT '举报原因',
    detail VARCHAR(300) COMMENT '补充说明',
    status INT NOT NULL DEFAULT 0 COMMENT '状态: 0待处理 1已采纳 2已驳回 3已关闭',
    review_note VARCHAR(300) COMMENT '处理备注',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_reports_reporter FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_reports_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    CONSTRAINT fk_reports_reviewer FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_reports_status_created (status, created_at),
    INDEX idx_reports_post_status (post_id, status),
    INDEX idx_reports_reporter_created (reporter_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帖子举报表';

CREATE TABLE IF NOT EXISTS report_review_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    report_id BIGINT NOT NULL COMMENT '举报 ID',
    actor_id BIGINT COMMENT '处理人 ID',
    action VARCHAR(32) NOT NULL COMMENT '处理动作',
    note VARCHAR(300) COMMENT '处理备注',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_report_review_logs_report FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    CONSTRAINT fk_report_review_logs_actor FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_report_review_logs_report_created (report_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='举报处理历史表';

CREATE TABLE IF NOT EXISTS recommendation_configs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tag_weight INT NOT NULL DEFAULT 50 COMMENT '兴趣标签权重',
    engagement_weight INT NOT NULL DEFAULT 30 COMMENT '互动热度权重',
    recency_weight INT NOT NULL DEFAULT 20 COMMENT '内容新鲜度权重',
    explainability_enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否展示推荐说明',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='推荐策略配置表';

INSERT INTO recommendation_configs (id, tag_weight, engagement_weight, recency_weight, explainability_enabled)
VALUES (1, 50, 30, 20, TRUE)
ON DUPLICATE KEY UPDATE
    id = id;

-- In-app notifications generated by domain events (replies, report decisions, level-ups, redemptions).
CREATE TABLE IF NOT EXISTS notifications (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    recipient_id BIGINT NOT NULL COMMENT '接收用户 ID',
    type VARCHAR(30) NOT NULL COMMENT '通知类型',
    title VARCHAR(120) NOT NULL COMMENT '标题',
    content VARCHAR(500) COMMENT '内容',
    target_id BIGINT COMMENT '关联实体 ID',
    target_type VARCHAR(30) COMMENT '关联实体类型',
    is_read BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否已读',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_notifications_recipient FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_notification_recipient (recipient_id),
    INDEX idx_notification_recipient_read (recipient_id, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='站内通知表';

-- Directed follow edges for the social graph (follower subscribes to following).
CREATE TABLE IF NOT EXISTS user_follows (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    follower_id BIGINT NOT NULL COMMENT '关注者 ID',
    following_id BIGINT NOT NULL COMMENT '被关注者 ID',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_user_follows_follower FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_follows_following FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_follows_pair (follower_id, following_id),
    INDEX idx_follow_follower (follower_id),
    INDEX idx_follow_following (following_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户关注关系表';

INSERT INTO sections (name, description, sort_order) VALUES
('学术科研', '学术交流、实验室资源、科研项目', 1),
('校园生活', '社团活动、宿舍生活、美食分享', 2),
('课程讨论', '专业课程、选修推荐、考试经验', 3),
('校园资讯', '通知公告、讲座信息、就业招聘', 4)
ON DUPLICATE KEY UPDATE description = VALUES(description), sort_order = VALUES(sort_order);
