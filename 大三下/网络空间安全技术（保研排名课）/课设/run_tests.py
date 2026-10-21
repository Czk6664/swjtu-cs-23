# -*- coding: utf-8 -*-
"""
run_tests.py —— 自动化测试用例（≥5 条，覆盖不同类型）

设计者：程泽凯  学号：2023112621

测试用例清单：
  TC1 注册 + 口令哈希存储验证（密码不得明文）
  TC2 正确口令登录成功
  TC3 二次验证模拟码验证（12345）
  TC4 错误口令累计失败 → 触发账号临时锁定（登录失败限制）
  TC5 锁定期内即使口令正确也被拒绝
  TC6 异地登录检测（短时间多 IP）
  TC7 非工作时间登录检测
  TC8 高频登录检测
  TC9 全量审计输出汇总

运行： python run_tests.py
说明：每条用例独立重建数据库，互不污染。
"""

import os
from datetime import timedelta

import config

# 测试脚本使用独立数据库，避免删除或覆盖 Web 演示时注册的账号。
config.DB_PATH = os.path.join(config.BASE_DIR, "data", "secure_login_test.db")

import db
import security
import audit
from security import now, iso


PASS, FAIL = "  [通过]", "  [失败]"
_results = []


def fresh_db():
    if os.path.exists(config.DB_PATH):
        os.remove(config.DB_PATH)
    db.init_db()


def check(name, condition, extra=""):
    tag = PASS if condition else FAIL
    print(f"{tag} {name} {extra}")
    _results.append((name, condition))
    return condition


def insert_log(username, ip, success, reason, dt):
    with db.get_conn() as conn:
        db.add_login_log(conn, username, ip, "pytest", success, reason, iso(dt))


# --------------------------------------------------------------------------
def tc1_register_hash():
    print("\nTC1 注册与口令哈希存储")
    fresh_db()
    ok, msg = security.register_user("czk2023", "Czk@2023112621")
    check("注册成功", ok, msg)

    with db.get_conn() as conn:
        user = db.get_user(conn, "czk2023")
    stored = user["password_hash"]
    check("数据库中不含明文口令", "Czk@2023112621" not in stored)
    check("使用 pbkdf2 加盐哈希", stored.startswith("pbkdf2:sha256"),
          f"-> {stored[:32]}...")
    check("正确口令可校验通过", security.verify_password(stored, "Czk@2023112621"))
    check("错误口令校验失败", not security.verify_password(stored, "wrongpass1"))

    # 弱口令应被拒绝
    ok2, _ = security.register_user("weakuser", "123")
    check("弱口令(过短)被拒绝", not ok2)


def tc2_login_success():
    print("\nTC2 正确口令登录成功")
    fresh_db()
    security.register_user("czk2023", "Czk@2023112621")
    r = security.authenticate("czk2023", "Czk@2023112621", "127.0.0.1", "pytest")
    check("登录成功", r["success"], r["message"])


def tc3_simulated_otp():
    print("\nTC3 二次验证模拟码")
    fresh_db()
    security.register_user("czk2023", "Czk@2023112621")
    import app as webapp
    webapp.app.config["TESTING"] = True
    with webapp.app.test_client() as client:
        bad = client.post("/login", data={
            "username": "czk2023",
            "password": "Czk@2023112621",
            "otp_code": "00000",
        }, follow_redirects=True)
        ok = client.post("/login", data={
            "username": "czk2023",
            "password": "Czk@2023112621",
            "otp_code": config.SIMULATED_OTP_CODE,
        }, follow_redirects=False)
    check("错误二次验证码被拒绝", b"12345" in bad.data)
    check("输入 12345 后进入登录认证流程", ok.status_code == 302,
          f"status={ok.status_code}")


def tc4_lockout():
    print("\nTC4 连续失败触发账号临时锁定")
    fresh_db()
    security.register_user("victim7", "Victim#0001")

    locked = False
    for i in range(config.MAX_FAILED_ATTEMPTS):
        r = security.authenticate("victim7", "badpassword0", "192.168.1.50", "pytest")
        if "锁定" in r["message"]:
            locked = True
    check(f"第 {config.MAX_FAILED_ATTEMPTS} 次失败后账号被锁定", locked)

    with db.get_conn() as conn:
        user = db.get_user(conn, "victim7")
    check("锁定状态已写入数据库", security.is_locked(user),
          f"locked_until={user['locked_until']}")


def tc5_locked_rejects_correct_pwd():
    print("\nTC5 锁定期内正确口令仍被拒绝")
    fresh_db()
    security.register_user("victim7", "Victim#0001")
    for _ in range(config.MAX_FAILED_ATTEMPTS):
        security.authenticate("victim7", "badpassword0", "192.168.1.50", "pytest")
    r = security.authenticate("victim7", "Victim#0001", "192.168.1.50", "pytest")
    check("锁定期内正确口令被拒绝", (not r["success"]) and r["reason"] == "locked",
          r["message"])


def tc6_multi_ip():
    print("\nTC6 异地登录检测（短时多 IP）")
    fresh_db()
    security.register_user("alice99", "Alice#pass01")
    base = now()
    insert_log("alice99", "10.0.0.5", True, "ok", base - timedelta(minutes=4))
    insert_log("alice99", "172.16.8.9", True, "ok", base - timedelta(minutes=2))
    insert_log("alice99", "203.0.113.7", True, "ok", base - timedelta(minutes=1))
    report = audit.run_full_audit()
    check("检测到异地登录告警", report["summary"]["multi_ip"] >= 1,
          f"multi_ip={report['summary']['multi_ip']}")


def tc7_off_hours():
    print("\nTC7 非工作时间登录检测")
    fresh_db()
    security.register_user("bob_dev", "BobDev2024!")
    off = now().replace(hour=2, minute=30, second=0)
    insert_log("bob_dev", "192.168.1.77", True, "ok", off)
    report = audit.run_full_audit()
    check("检测到非工作时间登录", report["summary"]["off_hours"] >= 1,
          f"off_hours={report['summary']['off_hours']}")


def tc8_high_freq():
    print("\nTC8 高频登录检测")
    fresh_db()
    security.register_user("czk2023", "Czk@2023112621")
    base = now()
    for i in range(config.HIGH_FREQ_THRESHOLD + 2):
        insert_log("czk2023", "127.0.0.1", False, "wrong_password",
                   base - timedelta(seconds=50 - 3 * i))
    report = audit.run_full_audit()
    check("检测到高频登录", report["summary"]["high_freq"] >= 1,
          f"high_freq={report['summary']['high_freq']}")


def tc9_full_audit():
    print("\nTC9 全量审计汇总输出")
    fresh_db()
    # 复用种子数据逻辑
    import seed_data
    seed_data.seed_users()
    seed_data.seed_logs()
    report = audit.run_full_audit()
    total_alerts = report["alerts"]
    check("审计生成了告警", len(total_alerts) >= 1, f"共 {len(total_alerts)} 条告警")
    check("覆盖暴力尝试", report["summary"]["brute_force"] >= 1)
    check("覆盖异地登录", report["summary"]["multi_ip"] >= 1)
    check("覆盖非工作时间", report["summary"]["off_hours"] >= 1)
    check("覆盖高频登录", report["summary"]["high_freq"] >= 1)
    print(f"     审计汇总: 日志 {report['total_logs']} 条, "
          f"成功 {report['success_logs']}, 失败 {report['failed_logs']}, "
          f"告警 {len(total_alerts)}")


def main():
    print("=" * 60)
    print(" Web 登录系统安全加固 —— 自动化测试")
    print(" 设计者：程泽凯  学号：2023112621")
    print("=" * 60)

    tc1_register_hash()
    tc2_login_success()
    tc3_simulated_otp()
    tc4_lockout()
    tc5_locked_rejects_correct_pwd()
    tc6_multi_ip()
    tc7_off_hours()
    tc8_high_freq()
    tc9_full_audit()

    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print("\n" + "=" * 60)
    print(f" 测试结果：{passed}/{total} 项断言通过")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
