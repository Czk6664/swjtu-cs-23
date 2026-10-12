import copy
import hmac
from hashlib import sha256

from common import auth_result, b64e, normalize_user_id, now_unix_ts, random_nonce, safe_compare
from user_store import get_user_record


def _mac_message(user_id: str, ts: int | None, nonce: str | None, payload: bytes) -> bytes:
    parts = [normalize_user_id(user_id).encode("utf-8")]
    if ts is not None:
        parts.append(str(ts).encode("ascii"))
    if nonce is not None:
        parts.append(nonce.encode("ascii"))
    parts.append(payload)
    return b"|".join(parts)


def build_mac_packet(user_id: str, payload: bytes, shared_key: bytes, nonce: bytes | None, ts: int | None) -> dict:
    """构造带 MAC 的认证消息。"""
    nonce_id = b64e(nonce) if nonce is not None else None
    msg = _mac_message(user_id, ts, nonce_id, payload)
    return {
        "id": normalize_user_id(user_id),
        "ts": ts,
        "nonce": nonce_id,
        "payload": payload,
        "tag": hmac.new(shared_key, msg, sha256).digest(),
    }


def verify_mac_packet(packet: dict, db: dict, now_ts: int | None = None, require_freshness: bool = True) -> dict:
    """验证 MAC 并检查新鲜性。"""
    uid = normalize_user_id(packet.get("id", ""))
    ts_now = now_ts if now_ts is not None else now_unix_ts()
    record = get_user_record(uid, db)
    if record is None:
        return auth_result(uid, "mac", False, "user_not_found", "record: none", "record: none", ts_now)
    if record.get("status") != "active":
        return auth_result(uid, "mac", False, "account_inactive", "status: inactive", "status: inactive", ts_now)

    nonce = packet.get("nonce")
    ts = packet.get("ts")
    before = f"nonce: {nonce}; used_mac_nonces: {sorted(record.setdefault('used_mac_nonces', set()))}"

    expected = hmac.new(
        record["shared_key"],
        _mac_message(uid, ts, nonce, packet.get("payload", b"")),
        sha256,
    ).digest()
    if not safe_compare(expected, packet.get("tag", b"")):
        return auth_result(uid, "mac", False, "tag_mismatch", before, before, ts_now)

    if require_freshness:
        if ts is None or nonce is None:
            return auth_result(uid, "mac", False, "freshness_fields_missing", before, before, ts_now)
        if abs(ts_now - int(ts)) > 60:
            return auth_result(uid, "mac", False, "timestamp_expired", before, before, ts_now)
        used = record.setdefault("used_mac_nonces", set())
        if nonce in used:
            return auth_result(uid, "mac", False, "nonce_reused", before, before, ts_now)
        used.add(nonce)
        after = f"ts: {ts} within ±60s; nonce {nonce}: fresh -> consumed"
        return auth_result(uid, "mac", True, "ok", before, after, ts_now)

    after = "no freshness fields checked; replay remains acceptable"
    return auth_result(uid, "mac(no_freshness)", True, "ok_no_freshness", before, after, ts_now)


def inject_payload_tamper(packet: dict) -> dict:
    """复制报文并模拟篡改 payload。"""
    tampered = copy.deepcopy(packet)
    tampered["payload"] = b"amount=9999&to=mallory"
    return tampered


def new_mac_nonce() -> bytes:
    return random_nonce(16)

