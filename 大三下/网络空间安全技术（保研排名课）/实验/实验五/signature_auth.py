import copy
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from common import auth_result, b64e, normalize_user_id, now_unix_ts, random_nonce
from user_store import get_user_record


def generate_ec_key_pair() -> tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    return ec.generate_private_key(ec.SECP256R1()), None


def public_key_pem(private_key: ec.EllipticCurvePrivateKey) -> bytes:
    return private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def load_public_key(public_pem: bytes):
    return serialization.load_pem_public_key(public_pem)


def _signed_message(user_id: str, data: bytes, meta: dict) -> bytes:
    canonical_meta = json.dumps(meta, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return b"|".join([normalize_user_id(user_id).encode("utf-8"), data, canonical_meta])


def sign_message_digest(private_key, message: bytes) -> bytes:
    """发送方对消息签名。"""
    return private_key.sign(message, ec.ECDSA(hashes.SHA256()))


def build_signed_packet(user_id: str, payload: bytes, private_key, meta: dict) -> dict:
    """构造数字签名报文。"""
    uid = normalize_user_id(user_id)
    signature = sign_message_digest(private_key, _signed_message(uid, payload, meta))
    return {"id": uid, "data": payload, "meta": meta, "signature": signature}


def verify_signed_packet(packet: dict, db: dict, now_ts: int | None = None) -> dict:
    """依据公钥执行验签并检查新鲜性。"""
    uid = normalize_user_id(packet.get("id", ""))
    ts_now = now_ts if now_ts is not None else now_unix_ts()
    record = get_user_record(uid, db)
    if record is None:
        return auth_result(uid, "signature", False, "user_not_found", "record: none", "record: none", ts_now)
    if record.get("status") != "active":
        return auth_result(uid, "signature", False, "account_inactive", "status: inactive", "status: inactive", ts_now)

    meta = packet.get("meta", {})
    nonce = meta.get("nonce")
    ts = meta.get("ts")
    before = f"nonce: {nonce}; used_sig_nonces: {sorted(record.setdefault('used_sig_nonces', set()))}"
    try:
        load_public_key(record["pub_key"]).verify(
            packet.get("signature", b""),
            _signed_message(uid, packet.get("data", b""), meta),
            ec.ECDSA(hashes.SHA256()),
        )
    except InvalidSignature:
        return auth_result(uid, "signature", False, "signature_invalid", before, before, ts_now)

    if ts is None or nonce is None:
        return auth_result(uid, "signature", False, "freshness_fields_missing", before, before, ts_now)
    if abs(ts_now - int(ts)) > 60:
        return auth_result(uid, "signature", False, "timestamp_expired", before, before, ts_now)
    used = record.setdefault("used_sig_nonces", set())
    if nonce in used:
        return auth_result(uid, "signature", False, "nonce_reused", before, before, ts_now)
    used.add(nonce)
    after = f"ts: {ts} within ±60s; nonce {nonce}: fresh -> consumed"
    return auth_result(uid, "signature", True, "ok", before, after, ts_now)


def make_signature_meta(ts: int | None = None) -> dict:
    return {"ts": ts if ts is not None else now_unix_ts(), "nonce": b64e(random_nonce(16))}


def inject_data_tamper(packet: dict) -> dict:
    tampered = copy.deepcopy(packet)
    tampered["data"] = b"amount=9999&to=mallory"
    return tampered

