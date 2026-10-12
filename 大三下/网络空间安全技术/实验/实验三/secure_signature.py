from cryptography.exceptions import InvalidTag

from crypto_utils import (
    aes_gcm_decrypt,
    aes_gcm_encrypt,
    b64decode,
    b64encode,
    canonical_json_bytes,
    copy_package,
    flip_b64_field,
    get_hash_algorithm,
    random_nonce_hex,
    rsa_decrypt,
    rsa_encrypt,
    rsa_pss_padding,
    sign_canonical_dict,
    utc_timestamp,
    verify_canonical_dict,
)


SIGNATURE_SUITE = "RSA-PSS+SHA256"
ENCRYPTION_SUITE = "RSA-OAEP-SHA256+AES-256-GCM"


def _sign_then_encrypt_signed_data(plaintext: bytes, metadata: dict) -> dict:
    return {
        "plaintext_b64": b64encode(plaintext),
        "metadata": metadata,
    }


def sign_then_encrypt(
    sender_private_key,
    receiver_public_key,
    plaintext: bytes,
    metadata: dict,
) -> dict:
    """
    功能：先签名，再对消息、签名和元数据整体加密。
    输出：安全消息包，不输出固定密文答案。
    """
    signed_data = _sign_then_encrypt_signed_data(plaintext, metadata)
    signature = sign_canonical_dict(sender_private_key, signed_data)
    inner_package = {
        "format": "sign-then-encrypt-inner-v1",
        "plaintext_b64": b64encode(plaintext),
        "metadata": metadata,
        "sign_alg": "RSA-PSS",
        "hash_alg": "SHA256",
        "signature_b64": b64encode(signature),
    }
    encrypted = aes_gcm_encrypt(canonical_json_bytes(inner_package))
    encrypted_key = rsa_encrypt(receiver_public_key, encrypted["key"])
    return {
        "format": "sign-then-encrypt-v1",
        "algorithm_suite": ENCRYPTION_SUITE,
        "encrypted_key_b64": b64encode(encrypted_key),
        "nonce_b64": b64encode(encrypted["nonce"]),
        "ciphertext_b64": b64encode(encrypted["ciphertext"]),
        "tag_b64": b64encode(encrypted["tag"]),
    }


def decrypt_then_verify(receiver_private_key, sender_public_key, secure_package: dict) -> dict:
    """
    功能：先解密安全消息包，再验证数字签名。
    返回：明文、解密结果、验签结果和错误原因。
    """
    try:
        session_key = rsa_decrypt(receiver_private_key, b64decode(secure_package["encrypted_key_b64"]))
        inner_bytes = aes_gcm_decrypt(
            session_key,
            b64decode(secure_package["nonce_b64"]),
            b64decode(secure_package["ciphertext_b64"]),
            b64decode(secure_package["tag_b64"]),
        )
        import json

        inner_package = json.loads(inner_bytes.decode("utf-8"))
        plaintext = b64decode(inner_package["plaintext_b64"])
        signed_data = _sign_then_encrypt_signed_data(plaintext, inner_package["metadata"])
        verify_ok = verify_canonical_dict(
            sender_public_key,
            signed_data,
            b64decode(inner_package["signature_b64"]),
        )
        return {
            "decrypt_success": True,
            "verify_success": verify_ok,
            "plaintext": plaintext,
            "metadata": inner_package["metadata"],
            "error": None if verify_ok else "signature verification failed",
        }
    except Exception as exc:
        return {
            "decrypt_success": False,
            "verify_success": False,
            "plaintext": None,
            "metadata": None,
            "error": type(exc).__name__,
        }


def _encrypt_then_sign_fields(package: dict) -> dict:
    return {
        "algorithm_suite": package["algorithm_suite"],
        "encrypted_key_b64": package["encrypted_key_b64"],
        "nonce_b64": package["nonce_b64"],
        "ciphertext_b64": package["ciphertext_b64"],
        "tag_b64": package["tag_b64"],
        "metadata": package["metadata"],
    }


def encrypt_then_sign(
    sender_private_key,
    receiver_public_key,
    plaintext: bytes,
    metadata: dict,
) -> dict:
    """
    功能：先加密明文，再对密文包进行数字签名。
    """
    encrypted = aes_gcm_encrypt(plaintext)
    encrypted_key = rsa_encrypt(receiver_public_key, encrypted["key"])
    package = {
        "format": "encrypt-then-sign-v1",
        "algorithm_suite": ENCRYPTION_SUITE,
        "encrypted_key_b64": b64encode(encrypted_key),
        "nonce_b64": b64encode(encrypted["nonce"]),
        "ciphertext_b64": b64encode(encrypted["ciphertext"]),
        "tag_b64": b64encode(encrypted["tag"]),
        "metadata": metadata,
        "sign_alg": "RSA-PSS",
        "hash_alg": "SHA256",
    }
    package["signature_b64"] = b64encode(
        sign_canonical_dict(sender_private_key, _encrypt_then_sign_fields(package))
    )
    return package


def verify_then_decrypt(
    receiver_private_key,
    sender_public_key,
    signed_cipher_package: dict,
) -> dict:
    """
    功能：先验证外层签名，再解密密文。
    """
    try:
        verify_ok = verify_canonical_dict(
            sender_public_key,
            _encrypt_then_sign_fields(signed_cipher_package),
            b64decode(signed_cipher_package["signature_b64"]),
        )
        if not verify_ok:
            return {
                "verify_success": False,
                "decrypt_success": False,
                "plaintext": None,
                "error": "signature verification failed",
            }
        session_key = rsa_decrypt(
            receiver_private_key,
            b64decode(signed_cipher_package["encrypted_key_b64"]),
        )
        plaintext = aes_gcm_decrypt(
            session_key,
            b64decode(signed_cipher_package["nonce_b64"]),
            b64decode(signed_cipher_package["ciphertext_b64"]),
            b64decode(signed_cipher_package["tag_b64"]),
        )
        return {
            "verify_success": True,
            "decrypt_success": True,
            "plaintext": plaintext,
            "error": None,
        }
    except Exception as exc:
        return {
            "verify_success": True,
            "decrypt_success": False,
            "plaintext": None,
            "error": type(exc).__name__,
        }


def _envelope_signed_fields(secure_envelope: dict) -> dict:
    return {
        "format": secure_envelope["format"],
        "algorithm_suite": secure_envelope["algorithm_suite"],
        "sender_id": secure_envelope["sender_id"],
        "receiver_id": secure_envelope["receiver_id"],
        "created_at": secure_envelope["created_at"],
        "nonce_b64": secure_envelope["nonce_b64"],
        "encrypted_key_b64": secure_envelope["encrypted_key_b64"],
        "ciphertext_b64": secure_envelope["ciphertext_b64"],
        "tag_b64": secure_envelope["tag_b64"],
    }


def build_secure_envelope(
    sender_private_key,
    receiver_public_key,
    plaintext: bytes,
    sender_id: str,
    receiver_id: str,
) -> dict:
    """
    功能：构造数字信封 + 数字签名安全包。
    输出：包含加密会话密钥、密文、完整性标签、签名和元数据的数据包。
    """
    encrypted = aes_gcm_encrypt(plaintext)
    encrypted_key = rsa_encrypt(receiver_public_key, encrypted["key"])
    secure_envelope = {
        "format": "secure-envelope-v1",
        "algorithm_suite": ENCRYPTION_SUITE,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "created_at": utc_timestamp(),
        "nonce_b64": b64encode(encrypted["nonce"]),
        "encrypted_key_b64": b64encode(encrypted_key),
        "ciphertext_b64": b64encode(encrypted["ciphertext"]),
        "tag_b64": b64encode(encrypted["tag"]),
        "sign_alg": "RSA-PSS",
        "hash_alg": "SHA256",
    }
    secure_envelope["signature_b64"] = b64encode(
        sign_canonical_dict(sender_private_key, _envelope_signed_fields(secure_envelope))
    )
    return secure_envelope


def verify_secure_envelope_signature(sender_public_key, secure_envelope: dict) -> bool:
    """
    功能：验证安全包中外层签名是否有效。
    """
    try:
        if secure_envelope.get("algorithm_suite") != ENCRYPTION_SUITE:
            return False
        return verify_canonical_dict(
            sender_public_key,
            _envelope_signed_fields(secure_envelope),
            b64decode(secure_envelope["signature_b64"]),
        )
    except (KeyError, ValueError, TypeError):
        return False


def open_secure_envelope(
    receiver_private_key,
    sender_public_key,
    secure_envelope: dict,
) -> dict:
    """
    功能：验证签名，解密会话密钥，解密密文并检测完整性。
    返回：明文、签名验证结果、完整性检测结果、错误原因。
    """
    signature_ok = verify_secure_envelope_signature(sender_public_key, secure_envelope)
    if not signature_ok:
        return {
            "signature_valid": False,
            "decrypt_success": False,
            "integrity_valid": False,
            "plaintext": None,
            "error": "signature verification failed",
        }
    try:
        session_key = rsa_decrypt(receiver_private_key, b64decode(secure_envelope["encrypted_key_b64"]))
        plaintext = aes_gcm_decrypt(
            session_key,
            b64decode(secure_envelope["nonce_b64"]),
            b64decode(secure_envelope["ciphertext_b64"]),
            b64decode(secure_envelope["tag_b64"]),
        )
        return {
            "signature_valid": True,
            "decrypt_success": True,
            "integrity_valid": True,
            "plaintext": plaintext,
            "error": None,
        }
    except InvalidTag:
        return {
            "signature_valid": True,
            "decrypt_success": False,
            "integrity_valid": False,
            "plaintext": None,
            "error": "InvalidTag",
        }
    except Exception as exc:
        return {
            "signature_valid": True,
            "decrypt_success": False,
            "integrity_valid": False,
            "plaintext": None,
            "error": type(exc).__name__,
        }


def tamper_secure_envelope(secure_envelope: dict, field_name: str) -> dict:
    """
    功能：对指定字段做篡改，用于测试完整性检测和签名绑定效果。
    """
    if field_name in {"ciphertext_b64", "tag_b64", "encrypted_key_b64", "nonce_b64", "signature_b64"}:
        return flip_b64_field(secure_envelope, field_name)
    tampered = copy_package(secure_envelope)
    if field_name == "algorithm_suite":
        tampered[field_name] = "TAMPERED-" + tampered[field_name]
    elif field_name == "receiver_id":
        tampered[field_name] = tampered[field_name] + "-Mallory"
    elif field_name == "sender_id":
        tampered[field_name] = tampered[field_name] + "-Mallory"
    else:
        raise ValueError(f"Unsupported tamper field: {field_name}")
    return tampered


def tamper_package_b64_field(package: dict, field_name: str) -> dict:
    return flip_b64_field(package, field_name)


def tamper_sign_then_encrypt_inner_signature(
    receiver_private_key,
    receiver_public_key,
    secure_package: dict,
) -> dict:
    """
    解密实验五内部包，篡改内部签名后重新加密，专用于观察“解密成功但验签失败”。
    """
    import json

    session_key = rsa_decrypt(receiver_private_key, b64decode(secure_package["encrypted_key_b64"]))
    inner_bytes = aes_gcm_decrypt(
        session_key,
        b64decode(secure_package["nonce_b64"]),
        b64decode(secure_package["ciphertext_b64"]),
        b64decode(secure_package["tag_b64"]),
    )
    inner_package = json.loads(inner_bytes.decode("utf-8"))
    raw_signature = bytearray(b64decode(inner_package["signature_b64"]))
    raw_signature[0] ^= 0x01
    inner_package["signature_b64"] = b64encode(bytes(raw_signature))
    encrypted = aes_gcm_encrypt(canonical_json_bytes(inner_package))
    tampered = copy_package(secure_package)
    tampered["encrypted_key_b64"] = b64encode(rsa_encrypt(receiver_public_key, encrypted["key"]))
    tampered["nonce_b64"] = b64encode(encrypted["nonce"])
    tampered["ciphertext_b64"] = b64encode(encrypted["ciphertext"])
    tampered["tag_b64"] = b64encode(encrypted["tag"])
    return tampered
