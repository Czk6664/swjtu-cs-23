# -*- coding: utf-8 -*-
"""
security.py —— 安全加固核心逻辑

设计者：程泽凯  学号：2023112621
职责：
  1. 密码哈希存储与校验（PBKDF2-SHA256，自带随机盐）
  2. 口令强度校验（注册时的输入验证）
  3. 登录失败计数与账号临时锁定
  4. 完整的登录认证流程（对应“用户登录认证流程图”）
"""

import re
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash

import config
import db


# --------------------------- 时间工具 ---------------------------

def now():
    """返回当前时间（不含微秒，便于日志可读）。"""
    return datetime.now().replace(microsecond=0)


def iso(dt):
    return dt.isoformat(sep=" ")


def parse(ts):
    return datetime.fromisoformat(ts)


# --------------------------- 密码哈希 ---------------------------

def hash_password(plain):
    """对明文口令生成加盐哈希。绝不明文存储。"""
    return generate_password_hash(plain, method=config.PASSWORD_HASH_METHOD)


def verify_password(stored_hash, plain):
    """校验口令是否匹配（恒定时间比较，防时序攻击）。"""
    return check_password_hash(stored_hash, plain)


# --------------------------- 口令强度校验 ---------------------------

def validate_password_strength(password):
    """
    校验口令是否满足强度策略。
    返回 (是否合格: bool, 错误信息: str)
    """
    if len(password) < config.PASSWORD_MIN_LENGTH:
        return False, f"口令长度至少 {config.PASSWORD_MIN_LENGTH} 位"
    if config.PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", password):
        return False, "口令必须包含数字"
    if config.PASSWORD_REQUIRE_LETTER and not re.search(r"[A-Za-z]", password):
        return False, "口令必须包含字母"
    return True, ""


def validate_username(username):
    """用户名输入验证：3-20 位字母数字下划线。"""
    if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", username or ""):
        return False, "用户名须为 3-20 位字母、数字或下划线"
    return True, ""


# --------------------------- 失败计数与锁定 ---------------------------

def count_recent_failures(conn, username):
    """统计暴力尝试窗口内该账号的连续失败次数（基于日志，时间精确）。"""
    window_start = iso(now() - timedelta(minutes=config.BRUTE_FORCE_WINDOW_MINUTES))
    cur = conn.execute(
        "SELECT COUNT(*) AS c FROM login_logs "
        "WHERE username = ? AND success = 0 AND created_at >= ?",
        (username, window_start),
    )
    return cur.fetchone()["c"]


def is_locked(user):
    """判断账号当前是否处于锁定状态。"""
    if user is None or user["locked_until"] is None:
        return False
    return now() < parse(user["locked_until"])


def lock_remaining_seconds(user):
    """返回锁定剩余秒数（用于提示）。"""
    if not is_locked(user):
        return 0
    return int((parse(user["locked_until"]) - now()).total_seconds())


# --------------------------- 注册 ---------------------------

def register_user(username, password):
    """
    注册新用户。返回 (成功: bool, 信息: str)
    """
    ok, msg = validate_username(username)
    if not ok:
        return False, msg
    ok, msg = validate_password_strength(password)
    if not ok:
        return False, msg

    with db.get_conn() as conn:
        if db.get_user(conn, username) is not None:
            return False, "用户名已存在"
        db.create_user(conn, username, hash_password(password), iso(now()))
    return True, "注册成功"


# --------------------------- 登录认证流程 ---------------------------

def authenticate(username, password, ip, user_agent):
    """
    核心登录认证流程，对应“用户登录认证流程图”。

    返回 dict: {
        "success": bool,
        "reason": str,        # ok / user_not_found / wrong_password / locked
        "message": str,       # 给用户的提示
        "alerts": list[str],  # 本次登录触发的实时异常提醒
    }
    """
    # 延迟导入避免循环依赖
    import audit

    ts = iso(now())

    with db.get_conn() as conn:
        user = db.get_user(conn, username)

        # 分支 1：账号已锁定 —— 直接拒绝（不泄露口令是否正确）
        if user is not None and is_locked(user):
            db.add_login_log(conn, username, ip, user_agent, False, "locked", ts)
            remain = lock_remaining_seconds(user)
            return {
                "success": False,
                "reason": "locked",
                "message": f"账号已锁定，请 {remain} 秒后再试",
                "alerts": [],
            }

        # 分支 2：用户名不存在 —— 记录失败日志（统一提示，防用户枚举）
        if user is None:
            db.add_login_log(conn, username, ip, user_agent, False, "user_not_found", ts)
            return {
                "success": False,
                "reason": "user_not_found",
                "message": "用户名或口令错误",
                "alerts": [],
            }

        # 分支 3：口令错误 —— 失败计数 +1，达阈值则锁定
        if not verify_password(user["password_hash"], password):
            db.add_login_log(conn, username, ip, user_agent, False, "wrong_password", ts)
            failures = count_recent_failures(conn, username)
            db.update_failed_count(conn, username, failures)

            if failures >= config.MAX_FAILED_ATTEMPTS:
                locked_until = iso(now() + timedelta(minutes=config.ACCOUNT_LOCK_MINUTES))
                db.set_lock(conn, username, locked_until)
                db.add_alert(
                    conn, username, "brute_force",
                    f"{config.BRUTE_FORCE_WINDOW_MINUTES} 分钟内失败 {failures} 次，"
                    f"已锁定至 {locked_until}", ts,
                )
                return {
                    "success": False,
                    "reason": "wrong_password",
                    "message": f"口令错误次数过多，账号已锁定 {config.ACCOUNT_LOCK_MINUTES} 分钟",
                    "alerts": [f"暴力尝试：{config.BRUTE_FORCE_WINDOW_MINUTES} 分钟内失败 {failures} 次"],
                }

            remain = config.MAX_FAILED_ATTEMPTS - failures
            return {
                "success": False,
                "reason": "wrong_password",
                "message": f"用户名或口令错误（还可尝试 {remain} 次）",
                "alerts": [],
            }

        # 分支 4：认证成功 —— 记录成功日志、清零失败计数、运行实时异常检测
        db.add_login_log(conn, username, ip, user_agent, True, "ok", ts)
        db.reset_user_security(conn, username, ts)
        realtime_alerts = audit.detect_realtime(conn, username, ip, now())

    return {
        "success": True,
        "reason": "ok",
        "message": "登录成功",
        "alerts": realtime_alerts,
    }
