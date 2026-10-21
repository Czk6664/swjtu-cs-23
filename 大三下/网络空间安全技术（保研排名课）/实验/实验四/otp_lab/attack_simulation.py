from __future__ import annotations

from copy import deepcopy

from .otp_counter_mode import verify_counter_message
from .otp_list_mode import verify_list_message
from .otp_time_mode import verify_time_message


def replay_attack(captured_message: dict, verifier_state: dict) -> dict:
    message = deepcopy(captured_message)
    mode = verifier_state.get("mode") or message.get("mode")
    state = verifier_state["state"]
    params = verifier_state.get("params", {})

    if mode == "list":
        return verify_list_message(message, state, log_path=params.get("log_path"))
    if mode == "counter":
        return verify_counter_message(
            message,
            state,
            look_ahead=params.get("look_ahead", 3),
            log_path=params.get("log_path"),
        )
    if mode == "time":
        return verify_time_message(
            message,
            state,
            step=params.get("step", 30),
            allowed_window=params.get("allowed_window", 1),
            log_path=params.get("log_path"),
        )
    raise ValueError(f"unsupported replay mode: {mode}")


def tamper_field(message: dict, field_name: str, new_value) -> dict:
    tampered = deepcopy(message)
    tampered[field_name] = new_value
    return tampered


def simulate_counter_drift(client_state: dict, delta: int) -> None:
    client_state["counter"] = int(client_state.get("counter", 0)) + int(delta)


def simulate_clock_drift(base_timestamp: int, delta_seconds: int) -> int:
    return int(base_timestamp) + int(delta_seconds)


def summarize_fail_reason(results: list[dict]) -> dict:
    summary: dict[str, int] = {}
    for item in results:
        if item.get("ok"):
            continue
        reason = item.get("reason", "未知失败")
        summary[reason] = summary.get(reason, 0) + 1
    return summary

