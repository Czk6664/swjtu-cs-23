import hmac
from hashlib import sha1

from common import auth_result, normalize_user_id, now_unix_ts
from user_store import get_user_record


def generate_hotp(secret: bytes, counter: int, digits: int = 6) -> str:
    """生成 RFC 4226 计数器同步型 OTP。"""
    msg = counter.to_bytes(8, "big")
    digest = hmac.new(secret, msg, sha1).digest()
    offset = digest[-1] & 0x0F
    code = int.from_bytes(digest[offset : offset + 4], "big") & 0x7FFFFFFF
    return str(code % (10**digits)).zfill(digits)


def generate_totp(secret: bytes, unix_ts: int, step: int = 30) -> str:
    """生成 RFC 6238 时间同步型 OTP。"""
    return generate_hotp(secret, unix_ts // step)


def verify_otp(
    user_id: str,
    otp_value: str,
    db: dict,
    mode: str = "totp",
    unix_ts: int | None = None,
    step: int = 30,
    window: int = 1,
    lookahead: int = 3,
) -> dict:
    """验证 OTP 并处理窗口/状态更新。"""
    uid = normalize_user_id(user_id)
    ts = unix_ts if unix_ts is not None else now_unix_ts()
    record = get_user_record(uid, db)
    if record is None:
        return auth_result(uid, f"otp({mode})", False, "user_not_found", "record: none", "record: none", ts)
    if record.get("status") != "active":
        return auth_result(uid, f"otp({mode})", False, "account_inactive", "status: inactive", "status: inactive", ts)

    if mode == "hotp":
        current = record.get("counter", 0)
        used_values = record.setdefault("used_hotp_values", set())
        before = f"counter: {current}; used_hotp_values: {len(used_values)}"
        if otp_value in used_values:
            return auth_result(uid, "otp(hotp)", False, "otp_reused", before, before, ts)
        for candidate_counter in range(current, current + lookahead + 1):
            if generate_hotp(record["otp_secret"], candidate_counter) == otp_value:
                record["counter"] = candidate_counter + 1
                used_values.add(otp_value)
                after = f"counter: {current} -> {record['counter']}; accepted counter={candidate_counter}"
                return auth_result(uid, "otp(hotp)", True, "ok", before, after, ts)
        return auth_result(uid, "otp(hotp)", False, "counter_window_miss_or_otp_mismatch", before, before, ts)

    if mode == "totp":
        current_slot = ts // step
        used_slots = record.setdefault("used_totp_slots", set())
        before = f"last_used_slot: {record.get('last_used_slot', 'none')}; used_slots: {sorted(used_slots)}"
        for slot in range(current_slot - window, current_slot + window + 1):
            if generate_hotp(record["otp_secret"], slot) == otp_value:
                if slot in used_slots:
                    return auth_result(uid, "otp(totp)", False, "totp_slot_reused", before, before, ts)
                used_slots.add(slot)
                record["last_used_slot"] = slot
                after = f"last_used_slot: {before} -> {slot}; used_slots includes {slot}"
                return auth_result(uid, "otp(totp)", True, "ok", before, after, ts)
        return auth_result(uid, "otp(totp)", False, "time_window_miss_or_otp_mismatch", before, before, ts)

    return auth_result(uid, f"otp({mode})", False, "unsupported_otp_mode", "mode unsupported", "mode unsupported", ts)


def resync_counter(user_id: str, observed: int, db: dict) -> None:
    """处理计数器失步恢复。"""
    record = get_user_record(user_id, db)
    if record is not None:
        record["counter"] = observed

