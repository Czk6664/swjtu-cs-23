from __future__ import annotations

from .common import (
    constant_time_equal,
    is_reused,
    mark_used,
    normalize_user_id,
    public_state,
    record_event,
    result,
)


def init_shared_list(user_id: str, otp_list: list[str]) -> dict:
    return {
        "user_id": normalize_user_id(user_id),
        "otp_list": [str(item) for item in otp_list],
        "pos": 0,
        "used": {},
    }


def get_current_list_otp(state: dict) -> str:
    pos = int(state.get("pos", 0))
    otp_list = state["otp_list"]
    if pos < 0 or pos >= len(otp_list):
        raise IndexError("list OTP position is exhausted")
    return otp_list[pos]


def generate_list_message(user_id: str, state: dict) -> dict:
    return {
        "mode": "list",
        "id": normalize_user_id(user_id),
        "otp": get_current_list_otp(state),
        "pos": int(state.get("pos", 0)),
    }


def verify_list_message(
    message: dict,
    server_state: dict,
    log_path: str | None = None,
) -> dict:
    user_id = normalize_user_id(message.get("id", ""))
    expected_user = server_state.get("user_id")
    pos = int(server_state.get("pos", 0))
    msg_pos = int(message.get("pos", -1))
    otp = str(message.get("otp", ""))
    marker = f"list:{msg_pos}:{otp}"
    before = public_state(server_state, ["pos"])
    expected_otp = (
        server_state["otp_list"][pos]
        if 0 <= pos < len(server_state.get("otp_list", []))
        else None
    )

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
            "OTP_REUSED_OR_EXPIRED",
            "复用失败",
            "list position and OTP were already accepted",
            before,
        )
    elif pos >= len(server_state["otp_list"]):
        verification = result(
            False,
            "OTP_REUSED_OR_EXPIRED",
            "新鲜性失败",
            "shared OTP list is exhausted",
            before,
        )
    elif msg_pos != pos:
        code = "OTP_REUSED_OR_EXPIRED" if msg_pos < pos else "POSITION_OUT_OF_SYNC"
        reason = "复用失败" if msg_pos < pos else "新鲜性失败"
        verification = result(
            False,
            code,
            reason,
            f"message pos={msg_pos}, server pos={pos}",
            before,
        )
    elif not constant_time_equal(otp, expected_otp):
        verification = result(
            False,
            "OTP_MISMATCH",
            "比较失败",
            "message OTP does not equal current list entry",
            before,
        )
    else:
        mark_used(user_id, marker, server_state["used"])
        advance_list_state(server_state)
        verification = result(
            True,
            "OK",
            "none",
            "current list OTP matched; server advanced pos",
            public_state(server_state, ["pos"]),
        )

    if log_path:
        record_event(
            log_path,
            {
                "mode": "list",
                "id": user_id,
                "user": user_id,
                "message_pos": msg_pos,
                "client_pos": msg_pos,
                "pos": before.get("pos"),
                "current_pos": before.get("pos"),
                "server_pos_before": before.get("pos"),
                "server_pos_after": server_state.get("pos"),
                "server_pos": before.get("pos"),
                "received_otp": otp,
                "expected_otp": expected_otp,
                "code": verification["code"],
                "reason": verification["reason"],
                "result": "pass" if verification["ok"] else "reject",
            },
        )
    return verification


def advance_list_state(state: dict) -> None:
    state["pos"] = int(state.get("pos", 0)) + 1
