# -*- coding: utf-8 -*-
"""
seed_data.py —— 初始化数据库并生成个性化测试数据

设计者：程泽凯  学号：2023112621

生成内容：
  1. 4 个本人创建的测试账号（口令均加盐哈希存储）
  2. 一批带历史时间戳的登录日志，刻意覆盖 4 类异常场景，
     用于演示“异常登录审计”。所有数据均为本地模拟，无真实第三方信息。

运行： python seed_data.py
"""

from datetime import datetime, timedelta

import db
import security
from security import now, iso


# 本人设计的测试账号（用户名 + 口令）
TEST_USERS = [
    ("czk2023", "Czk@2023112621"),    # 主账号，程泽凯本人
    ("alice99", "Alice#pass01"),       # 普通用户
    ("bob_dev", "BobDev2024!"),        # 普通用户
    ("victim7", "Victim#0001"),        # 用于演示被暴力破解的受害账号
]


def reset_database():
    """删除旧库并重建，保证种子数据可重复生成。"""
    import os
    import config
    if os.path.exists(config.DB_PATH):
        os.remove(config.DB_PATH)
    db.init_db()


def seed_users():
    with db.get_conn() as conn:
        for username, pwd in TEST_USERS:
            db.create_user(conn, username, security.hash_password(pwd), iso(now()))
    print(f"[1] 已创建 {len(TEST_USERS)} 个测试账号：",
          ", ".join(u for u, _ in TEST_USERS))


def seed_logs():
    """
    插入带历史时间戳的登录日志，模拟 4 类异常 + 正常登录。
    base 为“现在”，所有事件相对 base 倒推，落入各规则窗口内。
    """
    # 固定基准时间，保证审计告警数量与报告截图/表格一致，避免跨分钟边界导致结果漂移。
    base = datetime(2026, 5, 26, 19, 14, 26)
    rows = []   # (username, ip, success, reason, dt)

    # 场景 A —— 暴力尝试：victim7 在 3 分钟内连续失败 6 次（≥5 触发锁定）
    for i in range(6):
        rows.append(("victim7", "192.168.1.50", 0, "wrong_password",
                     base - timedelta(minutes=3, seconds=30 * i)))

    # 场景 B —— 异地登录：alice99 在 4 分钟内来自 3 个不同 IP 成功登录
    rows.append(("alice99", "10.0.0.5", 1, "ok", base - timedelta(minutes=4)))
    rows.append(("alice99", "172.16.8.9", 1, "ok", base - timedelta(minutes=2)))
    rows.append(("alice99", "203.0.113.7", 1, "ok", base - timedelta(minutes=1)))

    # 场景 C —— 非工作时间登录：bob_dev 于凌晨 02:30 成功登录
    off = base.replace(hour=2, minute=30, second=0) - timedelta(days=1)
    rows.append(("bob_dev", "192.168.1.77", 1, "ok", off))

    # 场景 D —— 高频登录：czk2023 在 40 秒内尝试 12 次（≥10 触发）
    for i in range(12):
        rows.append(("czk2023", "127.0.0.1", 0 if i < 11 else 1,
                     "wrong_password" if i < 11 else "ok",
                     base - timedelta(seconds=50 - 3 * i)))

    # 场景 E —— 正常登录（白天、单一 IP、低频）：作为对照，不应告警
    normal = base.replace(hour=14, minute=0, second=0) - timedelta(days=1)
    rows.append(("czk2023", "127.0.0.1", 1, "ok", normal))

    with db.get_conn() as conn:
        for username, ip, success, reason, dt in rows:
            db.add_login_log(conn, username, ip, "SeedAgent/1.0",
                             bool(success), reason, iso(dt))
    print(f"[2] 已插入 {len(rows)} 条模拟登录日志（覆盖暴力/异地/非工时/高频/正常）")


if __name__ == "__main__":
    reset_database()
    seed_users()
    seed_logs()
    print("[3] 种子数据生成完成，可运行 python app.py 或 python run_tests.py")
