from __future__ import annotations

from .common import constant_time_equal, normalize_user_id, record_event, result


def init_static_users(passwords: dict[str, str]) -> dict:
    return {
        "users": {
            normalize_user_id(user_id): str(password)
            for user_id, password in passwords.items()
        }
    }


def build_static_message(user_id: str, password: str) -> dict:
    return {
        "mode": "static",
        "id": normalize_user_id(user_id),
        "password": str(password),
    }


def verify_static_message(
    message: dict,
    server_state: dict,
    log_path: str | None = None,
) -> dict:
    user_id = normalize_user_id(message.get("id", ""))
    expected = server_state.get("users", {}).get(user_id)
    password = str(message.get("password", ""))

    if expected is None:
        verification = result(
            False,
            "ID_MISMATCH",
            "比较失败（id 不匹配）",
            "server has no static password for this id",
            {},
        )
    elif constant_time_equal(password, expected):
        verification = result(
            True,
            "OK",
            "none",
            "static password matched; no freshness state is checked",
            {},
        )
    else:
        verification = result(
            False,
            "PASSWORD_MISMATCH",
            "比较失败",
            "static password mismatch",
            {},
        )

    if log_path:
        record_event(
            log_path,
            {
                "mode": "static",
                "id": user_id,
                "user": user_id,
                "code": verification["code"],
                "reason": verification["reason"],
                "result": "pass" if verification["ok"] else "reject",
                "attack": message.get("attack"),
            },
        )
    return verification
