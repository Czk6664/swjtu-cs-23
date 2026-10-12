# -*- coding: utf-8 -*-
"""
app.py —— Flask Web 登录系统主应用

设计者：程泽凯  学号：2023112621
路由：
  /            首页（跳转登录）
  /register    用户注册
  /login       用户登录
  /dashboard   登录后的个人页（需会话）
  /logout      退出登录
  /audit       安全审计页（运行全量审计 + 展示告警与日志）

声明：本系统仅在本地授权环境（本机 + 本地浏览器）中完成与测试，
      未对任何真实第三方系统、公网或校园网服务器造成影响。
"""

import os
import sys
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash)

import config
import db
import security
import audit


def resource_path(relative_path):
    """兼容源码运行与 PyInstaller 打包后的资源路径。"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)

app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
    static_url_path="/static",
)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0  # 禁用静态文件缓存
app.config["TEMPLATES_AUTO_RELOAD"] = True  # 自动重载模板


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            flash("请先登录", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def client_ip():
    """获取客户端 IP。支持通过 ?ip= 模拟异地登录（仅本地实验用途）。"""
    # 实验便利：允许用查询参数模拟来源 IP，便于演示“异地登录”规则
    sim = request.args.get("ip") or request.form.get("sim_ip")
    if sim:
        return sim
    return request.headers.get("X-Forwarded-For", request.remote_addr or "0.0.0.0")


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        ok, msg = security.register_user(username, password)
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        otp_code = request.form.get("otp_code", "").strip()
        ip = client_ip()
        ua = request.headers.get("User-Agent", "unknown")

        if otp_code != config.SIMULATED_OTP_CODE:
            flash("二次验证失败：请输入本地实验验证码 12345", "danger")
            return render_template("login.html")

        result = security.authenticate(username, password, ip, ua)
        if result["success"]:
            session["username"] = username
            flash(result["message"], "success")
            for a in result["alerts"]:
                flash("⚠ 异常登录提醒 —— " + a, "warning")
            return redirect(url_for("dashboard"))
        else:
            flash(result["message"], "danger")
            for a in result["alerts"]:
                flash("⚠ " + a, "warning")
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    username = session["username"]
    with db.get_conn() as conn:
        user = db.get_user(conn, username)
        logs = [l for l in db.get_recent_logs(conn, 20) if l["username"] == username]
    return render_template("dashboard.html", user=user, logs=logs)


@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("已退出登录", "info")
    return redirect(url_for("login"))


@app.route("/audit")
def audit_page():
    """运行全量安全审计并展示结果。开放访问以便演示。"""
    report = audit.run_full_audit()
    with db.get_conn() as conn:
        logs = db.get_recent_logs(conn, 50)
    return render_template("audit.html", report=report, logs=logs,
                           type_names=config.ALERT_TYPE_NAMES)


if __name__ == "__main__":
    db.init_db()
    port = int(os.environ.get("APP_PORT", "5000"))
    print("数据库已初始化：", config.DB_PATH)
    print(f"访问 http://127.0.0.1:{port}/ 开始体验")
    app.run(
        host="127.0.0.1",
        port=port,
        debug=not getattr(sys, "frozen", False),
        use_reloader=False,
    )
