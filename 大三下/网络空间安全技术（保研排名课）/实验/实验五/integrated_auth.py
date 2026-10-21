import copy

from challenge_auth import verify_challenge_response
from mac_auth import verify_mac_packet
from otp_auth import verify_otp
from password_auth import verify_password
from signature_auth import verify_signed_packet


def run_auth_trial(mode: str, packet: dict, db: dict) -> dict:
    """统一执行一次鉴别并返回结果。"""
    if mode == "password":
        return verify_password(packet["id"], packet["password"], db)
    if mode == "challenge":
        return verify_challenge_response(packet, db, packet.get("server_time"))
    if mode == "otp(hotp)":
        return verify_otp(packet["id"], packet["otp"], db, mode="hotp", unix_ts=packet.get("server_time"))
    if mode == "otp(totp)":
        return verify_otp(packet["id"], packet["otp"], db, mode="totp", unix_ts=packet.get("server_time"))
    if mode == "mac":
        return verify_mac_packet(packet, db, packet.get("server_time"), packet.get("require_freshness", True))
    if mode == "signature":
        return verify_signed_packet(packet, db, packet.get("server_time"))
    return {
        "result": "reject",
        "reason": "unsupported_mode",
        "state_before": "mode unsupported",
        "state_after": "mode unsupported",
        "log": {"id": packet.get("id", ""), "mode": mode, "result": "reject", "reason": "unsupported_mode"},
    }


def replay_packet(packet: dict) -> dict:
    """构造重放测试输入。"""
    return copy.deepcopy(packet)


def summarize_results(records: list[dict]) -> dict:
    """统计各机制的通过率与拒绝原因。"""
    summary: dict[str, dict] = {}
    for row in records:
        mode = row["mode"]
        bucket = summary.setdefault(mode, {"total": 0, "accept": 0, "reject": 0, "reasons": {}})
        bucket["total"] += 1
        bucket[row["actual"]["result"]] += 1
        reason = row["actual"]["reason"]
        bucket["reasons"][reason] = bucket["reasons"].get(reason, 0) + 1
    return summary

