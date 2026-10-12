# -*- coding: utf-8 -*-
"""
db.py —— SQLite 数据访问层

设计者：程泽凯  学号：2023112621
说明：直接使用标准库 sqlite3，不引入 ORM，使所有 SQL 透明可审计。
      所有查询均使用参数化（占位符 ?），防止 SQL 注入。
"""

import os
import sqlite3
from contextlib import contextmanager

import config


def _ensure_data_dir():
    """确保数据目录存在。"""
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)


@contextmanager
def get_conn():
    """获取数据库连接的上下文管理器，自动提交/回滚并关闭。"""
    _ensure_data_dir()
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row          # 以字典方式访问列
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """创建数据库表结构（幂等，可重复执行）。"""
    with get_conn() as conn:
        # 用户表：保存账号、口令哈希、失败计数与锁定状态
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                created_at    TEXT    NOT NULL,
                failed_count  INTEGER NOT NULL DEFAULT 0,
                locked_until  TEXT,                       -- 锁定截止时间(ISO)，NULL 表示未锁定
                last_login_at TEXT                        -- 最近一次成功登录时间
            )
            """
        )

        # 登录日志表：记录每一次登录尝试（成功/失败）的审计信息
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS login_logs (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT    NOT NULL,
                ip         TEXT    NOT NULL,
                user_agent TEXT,
                success    INTEGER NOT NULL,               -- 1 成功 / 0 失败
                reason     TEXT    NOT NULL,               -- ok / wrong_password / user_not_found / locked
                created_at TEXT    NOT NULL                -- 事件时间(ISO)
            )
            """
        )

        # 审计告警表：异常登录审计后生成的告警条目
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_alerts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT    NOT NULL,
                alert_type TEXT    NOT NULL,               -- brute_force / multi_ip / off_hours / high_freq
                detail     TEXT    NOT NULL,               -- 命中规则的具体描述
                created_at TEXT    NOT NULL
            )
            """
        )

        # 为高频查询字段建立索引，加速审计扫描
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_logs_user_time "
            "ON login_logs(username, created_at)"
        )


# --------------------------- 用户相关操作 ---------------------------

def create_user(conn, username, password_hash, created_at):
    conn.execute(
        "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
        (username, password_hash, created_at),
    )


def get_user(conn, username):
    cur = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cur.fetchone()


def update_failed_count(conn, username, count):
    conn.execute(
        "UPDATE users SET failed_count = ? WHERE username = ?", (count, username)
    )


def set_lock(conn, username, locked_until):
    conn.execute(
        "UPDATE users SET locked_until = ? WHERE username = ?",
        (locked_until, username),
    )


def reset_user_security(conn, username, last_login_at):
    """登录成功后：清零失败计数、解除锁定、更新最近登录时间。"""
    conn.execute(
        "UPDATE users SET failed_count = 0, locked_until = NULL, last_login_at = ? "
        "WHERE username = ?",
        (last_login_at, username),
    )


# --------------------------- 日志相关操作 ---------------------------

def add_login_log(conn, username, ip, user_agent, success, reason, created_at):
    conn.execute(
        "INSERT INTO login_logs (username, ip, user_agent, success, reason, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (username, ip, user_agent, 1 if success else 0, reason, created_at),
    )


def get_recent_logs(conn, limit=50):
    cur = conn.execute(
        "SELECT * FROM login_logs ORDER BY id DESC LIMIT ?", (limit,)
    )
    return cur.fetchall()


def get_all_logs(conn):
    cur = conn.execute("SELECT * FROM login_logs ORDER BY created_at ASC")
    return cur.fetchall()


# --------------------------- 告警相关操作 ---------------------------

def add_alert(conn, username, alert_type, detail, created_at):
    conn.execute(
        "INSERT INTO audit_alerts (username, alert_type, detail, created_at) "
        "VALUES (?, ?, ?, ?)",
        (username, alert_type, detail, created_at),
    )


def clear_alerts(conn):
    conn.execute("DELETE FROM audit_alerts")


def get_alerts(conn):
    cur = conn.execute("SELECT * FROM audit_alerts ORDER BY id DESC")
    return cur.fetchall()
