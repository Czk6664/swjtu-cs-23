from __future__ import annotations

import time

from .common import (
    constant_time_equal,
    derive_value,
    is_reused,
    mark_used,
    normalize_user_id,
    public_state,
    record_event,
    result,
    truncate_otp,
)


def get_time_slot(timestamp: int, step: int = 30) -> int:
    return int(timestamp) // int(step)


def generate_time_otp(
    secret: bytes,
    timestamp: int,
    step: int = 30,
    digits: int = 6,
) -> str:
    slot = get_time_slot(timestamp, step)
    raw = derive_value(secret, f"time:{slot}")
    return truncate_otp(raw, digits)


def build_time_message(user_id: str, otp: str, timestamp: int) -> dict:
    return {
        "mode": "time",
        "id": normalize_user_id(user_id),
        "otp": str(otp),
        "timestamp": int(timestamp),
    }


def verify_time_message(
    message: dict,
    server_state: dict,
    step: int = 30,
    allowed_window: int = 1,
    log_path: str | None = None,
) -> dict:
    user_id = normalize_user_id(message.get("id", ""))
    expected_user = server_state.get("user_id")
    timestamp = int(message.get("timestamp", 0))
    server_now = int(server_state.get("now", int(time.time())))
    message_slot = get_time_slot(timestamp, step)
    server_slot = get_time_slot(server_now, step)
    otp = str(message.get("otp", ""))
    marker = f"time:{message_slot}"
    before = public_state(server_state, ["now", "last_slot"])

    if user_id != expected_user:
        verification = result(
            False,
            "ID_MISMATCH",
            "比较失败",
            "message id does not match registered user",
            before,
        )
    elif is_reused(user_id, marker, server_state.setdefault("used", {})):
        verification = result(
            False,
            "TIME_SLOT_REUSED",
            "复用失败",
            "time slot was already accepted",
            before,
        )
    elif abs(message_slot - server_slot) > int(allowed_window):
        verification = result(
            False,
            "TIME_SLOT_OUT_OF_WINDOW",
            "新鲜性失败",
            f"message slot={message_slot}, server slot={server_slot}, allowed=±{allowed_window}",
            before,
        )
    else:
        expected_otp = generate_time_otp(server_state["secret"], timestamp, step)
        if not constant_time_equal(otp, expected_otp):
            verification = result(
                False,
                "OTP_TIMESTAMP_MISMATCH",
                "比较失败",
                "OTP is not bound to the supplied timestamp slot",
                before,
            )
        else:
            mark_time_slot_used(user_id, message_slot, server_state["used"])
            server_state["last_slot"] = message_slot
            code = "OK_WITH_TIME_WINDOW" if message_slot != server_slot else "OK"
            verification = result(
                True,
                code,
                "none",
                "time OTP matched inside allowed window; slot marked used",
                public_state(server_state, ["now", "last_slot"]),
            )

    if log_path:
        record_event(
            log_path,
            {
                "mode": "time",
                "id": user_id,
                "user": user_id,
                "received_ts": timestamp,
                "client_slot": message_slot,
                "message_slot": message_slot,
                "server_slot": server_slot,
                "slot": message_slot,
                "slot_delta": abs(message_slot - server_slot),
                "allowed_window": allowed_window,
                "otp_original_slot": message.get("otp_original_slot"),
                "code": verification["code"],
                "reason": verification["reason"],
                "result": "pass" if verification["ok"] else "reject",
            },
        )
    return verification


def mark_time_slot_used(user_id: str, slot: int, used_state: dict) -> None:
    mark_used(user_id, f"time:{int(slot)}", used_state)
