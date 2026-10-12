import hashlib

from common import auth_result, normalize_user_id, random_nonce, safe_compare
from user_store import get_user_record


def hash_password(password: str, salt: bytes) -> bytes:
    """构造加盐口令摘要。"""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000,
        dklen=32,
    )


def build_password_record(user_id: str, password: str, status: str = "active") -> dict:
    """注册阶段构造用户口令记录。"""
    salt = random_nonce(16)
    return {
        "id": normalize_user_id(user_id),
        "salt": salt,
        "password_hash": hash_password(password, salt),
        "status": status,
    }


def verify_password(user_id: str, password: str, db: dict) -> dict:
    """验证静态口令并返回审计信息。"""
    uid = normalize_user_id(user_id)
    record = get_user_record(uid, db)
    before = "password_hash: stored; nonce/counter: none"
    if record is None:
        return auth_result(uid, "password", False, "user_not_found", "record: none", "record: none")
    if record.get("status") != "active":
        return auth_result(uid, "password", False, "account_inactive", before, before)

    candidate = hash_password(password, record["salt"])
    ok = safe_compare(candidate, record["password_hash"])
    reason = "ok" if ok else "password_mismatch"
    return auth_result(uid, "password", ok, reason, before, before)

