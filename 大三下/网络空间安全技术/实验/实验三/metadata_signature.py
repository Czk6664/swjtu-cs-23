from datetime import datetime

from crypto_utils import (
    b64decode,
    b64encode,
    canonical_json_bytes,
    get_hash_algorithm,
    random_nonce_hex,
    rsa_pss_padding,
    utc_timestamp,
)
from cryptography.exceptions import InvalidSignature


def build_metadata(sender_id: str, algorithm: str) -> dict:
    """
    功能：构造签名元数据，包括时间戳、随机数、算法标识等。
    """
    return {
        "sender_id": sender_id,
        "receiver_id": "Bob",
        "algorithm_suite": algorithm,
        "timestamp": utc_timestamp(),
        "nonce": random_nonce_hex(16),
    }


def serialize_signed_content(message: bytes, metadata: dict) -> bytes:
    """
    功能：按固定规范序列化消息和元数据。
    注意：验签时必须使用完全相同的序列化规则。
    """
    return canonical_json_bytes(
        {
            "message_b64": b64encode(message),
            "metadata": metadata,
        }
    )


def sign_with_metadata(private_key, message: bytes, metadata: dict) -> dict:
    """
    功能：对消息和元数据整体生成签名数据包。
    """
    serialized = serialize_signed_content(message, metadata)
    signature = private_key.sign(
        serialized,
        rsa_pss_padding("SHA256"),
        get_hash_algorithm("SHA256"),
    )
    return {
        "format": "metadata-signature-v1",
        "message_b64": b64encode(message),
        "metadata": metadata,
        "sign_alg": "RSA-PSS",
        "hash_alg": "SHA256",
        "signature_b64": b64encode(signature),
    }


def _metadata_format_ok(metadata: dict) -> bool:
    required = ["sender_id", "receiver_id", "algorithm_suite", "timestamp", "nonce"]
    if not isinstance(metadata, dict) or any(key not in metadata for key in required):
        return False
    try:
        datetime.fromisoformat(metadata["timestamp"])
        bytes.fromhex(metadata["nonce"])
    except (TypeError, ValueError):
        return False
    return True


def verify_metadata_signature(public_key, package: dict) -> bool:
    """
    功能：解析签名数据包，重新序列化并验证签名。
    """
    try:
        metadata = package["metadata"]
        if not _metadata_format_ok(metadata):
            return False
        message = b64decode(package["message_b64"])
        signature = b64decode(package["signature_b64"])
        public_key.verify(
            signature,
            serialize_signed_content(message, metadata),
            rsa_pss_padding(package.get("hash_alg", "SHA256")),
            get_hash_algorithm(package.get("hash_alg", "SHA256")),
        )
        return True
    except (InvalidSignature, KeyError, ValueError, TypeError):
        return False
