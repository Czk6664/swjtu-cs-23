from __future__ import annotations

import hashlib
import hmac
import json
import time
from pathlib import Path
from typing import Any


def normalize_user_id(user_id: str) -> str:
    return str(user_id).strip().lower()


def derive_value(secret: bytes, moving_factor: str) -> str:
    if isinstance(secret, str):
        secret = secret.encode("utf-8")
    message = str(moving_factor).encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def truncate_otp(raw_value: str, digits: int = 6) -> str:
    if digits <= 0:
        raise ValueError("digits must be positive")
    try:
        number = int(raw_value, 16)
    except ValueError:
        number = int.from_bytes(str(raw_value).encode("utf-8"), "big")
    return f"{number % (10 ** digits):0{digits}d}"


def constant_time_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(str(a), str(b))


def is_reused(user_id: str, marker: str, used_state: dict) -> bool:
    uid = normalize_user_id(user_id)
    return marker in used_state.get(uid, set())


def mark_used(user_id: str, marker: str, used_state: dict) -> None:
    uid = normalize_user_id(user_id)
    used_state.setdefault(uid, set()).add(marker)


def result(
    ok: bool,
    code: str,
    reason: str,
    detail: str,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": ok,
        "ok": ok,
        "code": code,
        "reason": reason,
        "detail": detail,
        "state": state or {},
    }


def public_state(state: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: state.get(key) for key in keys if key in state}


def record_event(log_path: str, event: dict) -> None:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "log_time": int(time.time()),
        **_json_safe(event),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    if isinstance(value, bytes):
        return value.hex()
    return value
