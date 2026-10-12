import json
import logging
import os
from datetime import datetime, timezone

import redis
import requests
from flask import Flask, jsonify, request


STUDENT = {
    "name": os.getenv("STUDENT_NAME", "程泽凯，王晨羽"),
    "student_id": os.getenv("STUDENT_ID", "2023112621,2023114337"),
    "class": os.getenv("STUDENT_CLASS", "2023-04班"),
}


def create_app() -> Flask:
    app = Flask(__name__)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    redis_client = build_redis_client()

    @app.get("/api/ping")
    def ping():
        app.logger.info("GET /api/ping from %s", request.remote_addr)
        return jsonify({"status": "ok"})

    @app.get("/api/visit")
    def visit():
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "student": STUDENT,
            "time_utc": now,
            "client": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", ""),
        }
        redis_status = "ok"
        visits = None
        try:
            visits = redis_client.incr("course-project:visits")
            redis_client.set("course-project:last-visit", json.dumps(payload, ensure_ascii=False))
        except redis.RedisError as exc:
            redis_status = f"error: {exc.__class__.__name__}"
            app.logger.warning("Redis visit write failed: %s", exc)

        app.logger.info("GET /api/visit redis=%s visits=%s", redis_status, visits)
        return jsonify(
            {
                "status": "ok",
                "redis": redis_status,
                "visits": visits,
                "student": STUDENT,
                "extra_package_demo": requests.__version__,
            }
        )

    @app.get("/api/redis/last")
    def last_visit():
        try:
            value = redis_client.get("course-project:last-visit")
            decoded = json.loads(value) if value else None
            redis_status = "ok"
        except (redis.RedisError, json.JSONDecodeError) as exc:
            decoded = None
            redis_status = f"error: {exc.__class__.__name__}"
            app.logger.warning("Redis read failed: %s", exc)

        app.logger.info("GET /api/redis/last redis=%s", redis_status)
        return jsonify({"status": "ok", "redis": redis_status, "last_visit": decoded})

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "healthy", "app_env": os.getenv("APP_ENV", "local")})

    return app


def build_redis_client() -> redis.Redis:
    password = os.getenv("REDIS_PASSWORD") or None
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=password,
        decode_responses=True,
        socket_timeout=2,
        socket_connect_timeout=2,
    )


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
