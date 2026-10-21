import hmac
from hashlib import sha256

from common import auth_result, b64d, b64e, normalize_user_id, now_unix_ts, random_nonce, safe_compare
from user_store import get_user_record


def issue_challenge(user_id: str, db: dict, ttl: int = 5, issued_at: int | None = None) -> dict:
    """为用户生成 nonce 与过期信息。"""
    uid = normalize_user_id(user_id)
    record = get_user_record(uid, db)
    if record is None:
        raise ValueError(f"unknown user: {uid}")
    ts = issued_at if issued_at is not None else now_unix_ts()
    nonce = random_nonce(16)
    nonce_id = b64e(nonce)
    record.setdefault("issued_nonces", {})[nonce_id] = {
        "expires_at": ts + ttl,
        "consumed": False,
    }
    return {"id": uid, "nonce": nonce_id, "expires_at": ts + ttl}


def compute_challenge_proof(shared_key: bytes, nonce: bytes, context: bytes) -> bytes:
    """客户端计算 proof。"""
    return hmac.new(shared_key, nonce + context, sha256).digest()


def verify_challenge_response(packet: dict, db: dict, now_ts: int | None = None) -> dict:
    """服务器验证 challenge 响应。"""
    uid = normalize_user_id(packet.get("id", ""))
    ts = now_ts if now_ts is not None else now_unix_ts()
    record = get_user_record(uid, db)
    if record is None:
        return auth_result(uid, "challenge", False, "user_not_found", "record: none", "record: none", ts)
    if record.get("status") != "active":
        return auth_result(uid, "challenge", False, "account_inactive", "status: inactive", "status: inactive", ts)

    nonce_id = packet.get("nonce", "")
    slot = record.setdefault("issued_nonces", {}).get(nonce_id)
    before = f'nonce "{nonce_id}": ' + ("not issued" if slot is None else f"issued(consumed={slot['consumed']})")
    if slot is None:
        return auth_result(uid, "challenge", False, "nonce_not_issued", before, before, ts)
    if slot["expires_at"] < ts:
        return auth_result(uid, "challenge", False, "nonce_expired", before, before, ts)
    if slot["consumed"]:
        return auth_result(uid, "challenge", False, "nonce_reused", before, before, ts)

    expected = compute_challenge_proof(record["shared_key"], b64d(nonce_id), packet.get("context", b""))
    proof = packet.get("proof", b"")
    if not safe_compare(expected, proof):
        return auth_result(uid, "challenge", False, "proof_mismatch", before, before, ts)

    slot["consumed"] = True
    after = f'nonce "{nonce_id}": issued -> consumed; nonce_used includes "{nonce_id}"'
    return auth_result(uid, "challenge", True, "ok", before, after, ts)

