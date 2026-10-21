# -*- coding: utf-8 -*-
"""
audit.py —— 异常登录检测与安全审计

设计者：程泽凯  学号：2023112621
职责：
  1. 实时检测：登录成功瞬间判断异地 / 非工作时间 / 高频（detect_realtime）
  2. 离线审计：扫描全部登录日志，匹配 4 类异常规则，生成审计报告
     （对应“异常登录审计流程图”）

所有阈值均来自 config.py，可现场修改后重新审计。
"""

from datetime import timedelta

import config
import db


# --------------------------- 单条规则判断 ---------------------------

def is_off_hours(dt):
    """规则三：非工作时间登录。23:00-06:00 之间视为异常。"""
    h = dt.hour
    start, end = config.OFF_HOURS_START, config.OFF_HOURS_END
    # 跨午夜区间：hour >= 23 或 hour < 6
    if start > end:
        return h >= start or h < end
    return start <= h < end


def distinct_ips_in_window(conn, username, end_dt, minutes):
    """规则二辅助：统计窗口内该账号出现的不同 IP 集合。"""
    start = (end_dt - timedelta(minutes=minutes)).isoformat(sep=" ")
    end = end_dt.isoformat(sep=" ")
    cur = conn.execute(
        "SELECT DISTINCT ip FROM login_logs "
        "WHERE username = ? AND created_at >= ? AND created_at <= ?",
        (username, start, end),
    )
    return [row["ip"] for row in cur.fetchall()]


def count_attempts_in_window(conn, username, end_dt, seconds):
    """规则四辅助：统计窗口内（秒级）该账号的登录请求次数。"""
    start = (end_dt - timedelta(seconds=seconds)).isoformat(sep=" ")
    end = end_dt.isoformat(sep=" ")
    cur = conn.execute(
        "SELECT COUNT(*) AS c FROM login_logs "
        "WHERE username = ? AND created_at >= ? AND created_at <= ?",
        (username, start, end),
    )
    return cur.fetchone()["c"]


# --------------------------- 实时检测（登录成功时） ---------------------------

def detect_realtime(conn, username, ip, dt):
    """
    登录成功瞬间运行的轻量检测，返回触发的异常提醒列表，
    同时写入 audit_alerts 表（对应“异常登录提醒”功能）。
    """
    alerts = []
    ts = dt.isoformat(sep=" ")

    # 异地登录：窗口内不同 IP 数达到阈值
    ips = distinct_ips_in_window(conn, username, dt, config.MULTI_IP_WINDOW_MINUTES)
    if len(ips) >= config.MULTI_IP_THRESHOLD:
        detail = (f"{config.MULTI_IP_WINDOW_MINUTES} 分钟内出现 {len(ips)} 个不同 IP："
                  + ", ".join(ips))
        db.add_alert(conn, username, "multi_ip", detail, ts)
        alerts.append("异地登录：" + detail)

    # 非工作时间登录
    if is_off_hours(dt):
        detail = f"于 {ts} 登录，处于非工作时段({config.OFF_HOURS_START}:00-{config.OFF_HOURS_END}:00)"
        db.add_alert(conn, username, "off_hours", detail, ts)
        alerts.append("非工作时间登录：" + detail)

    # 高频登录
    cnt = count_attempts_in_window(conn, username, dt, config.HIGH_FREQ_WINDOW_SECONDS)
    if cnt >= config.HIGH_FREQ_THRESHOLD:
        detail = f"{config.HIGH_FREQ_WINDOW_SECONDS} 秒内请求 {cnt} 次"
        db.add_alert(conn, username, "high_freq", detail, ts)
        alerts.append("高频登录：" + detail)

    return alerts


# --------------------------- 离线全量审计 ---------------------------

def run_full_audit():
    """
    扫描全部登录日志，按 4 类规则逐条匹配并生成告警，
    返回结构化审计报告。对应“异常登录审计流程图”。

    采用“逐事件回放”方式：按时间顺序遍历每条日志，
    对每条日志判断其所在窗口是否命中规则，命中则记一条告警。
    """
    report = {
        "total_logs": 0,
        "success_logs": 0,
        "failed_logs": 0,
        "alerts": [],
        "summary": {k: 0 for k in config.ALERT_TYPE_NAMES},
    }

    with db.get_conn() as conn:
        db.clear_alerts(conn)                       # 审计前清空旧告警，保证可重复执行
        logs = db.get_all_logs(conn)
        report["total_logs"] = len(logs)

        # 用于暴力尝试去重：同一锁定事件只告警一次
        brute_flagged = set()

        for log in logs:
            username = log["username"]
            ts = log["created_at"]
            dt = _parse(ts)

            if log["success"]:
                report["success_logs"] += 1
            else:
                report["failed_logs"] += 1

            # —— 规则一：暴力尝试（仅看失败日志）——
            if not log["success"]:
                win_start = (dt - timedelta(minutes=config.BRUTE_FORCE_WINDOW_MINUTES))
                fails = sum(
                    1 for l in logs
                    if l["username"] == username and not l["success"]
                    and win_start.isoformat(sep=" ") <= l["created_at"] <= ts
                )
                if fails >= config.MAX_FAILED_ATTEMPTS:
                    key = (username, dt.strftime("%Y%m%d%H%M"))
                    if key not in brute_flagged:
                        brute_flagged.add(key)
                        _record(report, conn, username, "brute_force",
                                f"截至 {ts}，{config.BRUTE_FORCE_WINDOW_MINUTES} 分钟内失败 {fails} 次", ts)

            # —— 规则三：非工作时间登录（成功登录才算有效异常）——
            if log["success"] and is_off_hours(dt):
                _record(report, conn, username, "off_hours",
                        f"于 {ts} 在非工作时段成功登录", ts)

            # —— 规则二：异地登录（成功登录时检查窗口内多 IP）——
            if log["success"]:
                ips = distinct_ips_in_window(conn, username, dt, config.MULTI_IP_WINDOW_MINUTES)
                if len(ips) >= config.MULTI_IP_THRESHOLD:
                    _record(report, conn, username, "multi_ip",
                            f"截至 {ts}，{config.MULTI_IP_WINDOW_MINUTES} 分钟内出现 {len(ips)} 个 IP: "
                            + ", ".join(ips), ts)

            # —— 规则四：高频登录 ——
            cnt = count_attempts_in_window(conn, username, dt, config.HIGH_FREQ_WINDOW_SECONDS)
            if cnt >= config.HIGH_FREQ_THRESHOLD:
                _record(report, conn, username, "high_freq",
                        f"截至 {ts}，{config.HIGH_FREQ_WINDOW_SECONDS} 秒内请求 {cnt} 次", ts)

    return report


def _parse(ts):
    from datetime import datetime
    return datetime.fromisoformat(ts)


def _record(report, conn, username, alert_type, detail, ts):
    """记录一条告警到报告与数据库，并去重（同账号同类型同细节只记一次）。"""
    sig = (username, alert_type, detail)
    if sig in report.get("_seen", set()):
        return
    report.setdefault("_seen", set()).add(sig)

    db.add_alert(conn, username, alert_type, detail, ts)
    report["alerts"].append({
        "username": username,
        "type": alert_type,
        "type_name": config.ALERT_TYPE_NAMES[alert_type],
        "detail": detail,
        "time": ts,
    })
    report["summary"][alert_type] += 1
