from __future__ import annotations

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


def init_counter_state(user_id: str, secret: bytes, counter: int = 0) -> dict:
    return {
        "user_id": normalize_user_id(user_id),
        "secret": secret,
        "counter": int(counter),
        "used": {},
    }


def generate_counter_otp(secret: bytes, counter: int, digits: int = 6) -> str:
    raw = derive_value(secret, f"counter:{int(counter)}")
    return truncate_otp(raw, digits)


def build_counter_message(user_id: str, otp: str, counter: int) -> dict:
    return {
        "mode": "counter",
        "id": normalize_user_id(user_id),
        "otp": str(otp),
        "counter": int(counter),
    }


def verify_counter_message(
    message: dict,
    server_state: dict,
    look_ahead: int = 3,
    log_path: str | None = None,
) -> dict:
    user_id = normalize_user_id(message.get("id", ""))
    expected_user = server_state.get("user_id")
    counter = int(message.get("counter", -1))
    server_counter = int(server_state.get("counter", 0))
    otp = str(message.get("otp", ""))
    marker = f"counter:{counter}"
    before = public_state(server_state, ["counter"])

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
            "COUNTER_REUSED",
            "复用失败",
            "counter was already accepted",
            before,
        )
    elif counter < server_counter:
        verification = result(
            False,
            "COUNTER_REUSED",
            "复用失败",
            f"message counter={counter}, server counter={server_counter}",
            before,
        )
    elif counter > server_counter + int(look_ahead):
        verification = result(
            False,
            "COUNTER_OUT_OF_WINDOW",
            "新鲜性失败",
            f"message counter={counter}, allowed max={server_counter + int(look_ahead)}",
            before,
        )
    else:
        expected_otp = generate_counter_otp(server_state["secret"], counter)
        if not constant_time_equal(otp, expected_otp):
            verification = result(
                False,
                "OTP_COUNTER_MISMATCH",
                "比较失败",
                "OTP is not bound to the supplied counter",
                before,
            )
        else:
            mark_used(user_id, marker, server_state["used"])
            server_state["counter"] = counter + 1
            code = "OK_WITH_RESYNC" if counter != server_counter else "OK"
            verification = result(
                True,
                code,
                "none",
                "counter OTP matched; server advanced to counter+1",
                public_state(server_state, ["counter"]),
            )

    if log_path:
        record_event(
            log_path,
            {
                "mode": "counter",
                "id": user_id,
                "user": user_id,
                "message_counter": counter,
                "received_counter": counter,
                "server_counter": before.get("counter"),
                "server_counter_before": before.get("counter"),
                "server_counter_after": server_state.get("counter"),
                "look_ahead": look_ahead,
                "allowed_range": f"{before.get('counter')}-{before.get('counter') + look_ahead}",
                "otp_generated_counter": message.get("otp_generated_counter"),
                "code": verification["code"],
                "reason": verification["reason"],
                "result": "pass" if verification["ok"] else "reject",
            },
        )
    return verification


def resync_counter(server_state: dict, observed_counter: int) -> None:
    observed_counter = int(observed_counter)
    if observed_counter > int(server_state.get("counter", 0)):
        server_state["counter"] = observed_counter
