import base64
import hmac
import json
import secrets
import time
from pathlib import Path
from typing import Any


def normalize_user_id(user_id: str) -> str:
    """标准化用户标识。"""
    return user_id.strip().lower()


def random_nonce(length: int = 16) -> bytes:
    """生成随机挑战值。"""
    return secrets.token_bytes(length)


def now_unix_ts() -> int:
    """返回当前 Unix 时间戳。"""
    return int(time.time())


def safe_compare(left: bytes, right: bytes) -> bool:
    """常量时间比较，避免普通字符串比较的计时侧信道。"""
    return hmac.compare_digest(left, right)


def b64e(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def b64d(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def write_auth_log(entry: dict[str, Any], path: str) -> None:
    """以 JSON Lines 方式写入鉴别审计日志。"""
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def auth_result(
    user_id: str,
    mode: str,
    accepted: bool,
    reason: str,
    state_before: str,
    state_after: str,
    server_time: int | None = None,
) -> dict[str, Any]:
    result = "accept" if accepted else "reject"
    log = {
        "id": normalize_user_id(user_id),
        "mode": mode,
        "result": result,
        "reason": reason,
        "server_time": server_time if server_time is not None else now_unix_ts(),
    }
    return {
        "result": result,
        "reason": reason,
        "state_before": state_before,
        "state_after": state_after,
        "log": log,
    }

