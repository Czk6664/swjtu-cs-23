from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import utils

from crypto_utils import get_hash_algorithm, hash_bytes, preview_bytes, rsa_pss_padding


def sign_with_digest(
    private_key,
    message: bytes,
    hash_alg: str = "SHA256",
    sign_alg: str = "RSA-PSS",
) -> dict:
    """
    功能：计算消息摘要并生成数字签名。
    返回：摘要展示值、签名值、算法标识等。
    """
    if sign_alg != "RSA-PSS":
        raise ValueError(f"Unsupported signature algorithm: {sign_alg}")
    digest = hash_bytes(message, hash_alg)
    signature = private_key.sign(
        digest,
        rsa_pss_padding(hash_alg),
        utils.Prehashed(get_hash_algorithm(hash_alg)),
    )
    return {
        "hash_alg": hash_alg,
        "sign_alg": sign_alg,
        "digest": digest,
        "digest_hex": digest.hex(),
        "digest_preview": preview_bytes(digest),
        "signature": signature,
        "signature_preview": preview_bytes(signature),
    }


def verify_with_digest(
    public_key,
    message: bytes,
    signature: bytes,
    hash_alg: str = "SHA256",
    sign_alg: str = "RSA-PSS",
) -> bool:
    """
    功能：重新计算摘要并验证签名。
    """
    if sign_alg != "RSA-PSS":
        raise ValueError(f"Unsupported signature algorithm: {sign_alg}")
    digest = hash_bytes(message, hash_alg)
    try:
        public_key.verify(
            signature,
            digest,
            rsa_pss_padding(hash_alg),
            utils.Prehashed(get_hash_algorithm(hash_alg)),
        )
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def tamper_message(message: bytes, mode: str = "flip_one_byte") -> bytes:
    """
    功能：构造被篡改的消息，用于完整性检测实验。
    """
    if not message:
        return b"x"
    data = bytearray(message)
    if mode == "flip_one_byte":
        data[-1] ^= 0x01
    elif mode == "replace_student_id":
        data = bytearray(message.replace(b"20260001", b"20260002"))
    else:
        raise ValueError(f"Unsupported tamper mode: {mode}")
    return bytes(data)


def compare_digest_before_after(
    original: bytes,
    tampered: bytes,
    hash_alg: str = "SHA256",
) -> dict:
    """
    功能：比较篡改前后摘要，用于实验分析。
    """
    original_digest = hash_bytes(original, hash_alg)
    tampered_digest = hash_bytes(tampered, hash_alg)
    return {
        "hash_alg": hash_alg,
        "original_digest_hex": original_digest.hex(),
        "tampered_digest_hex": tampered_digest.hex(),
        "original_digest_preview": preview_bytes(original_digest),
        "tampered_digest_preview": preview_bytes(tampered_digest),
        "same": original_digest == tampered_digest,
    }
