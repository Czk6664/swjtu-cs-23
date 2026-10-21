from cryptography.exceptions import InvalidSignature

from crypto_utils import (
    generate_rsa_key_pair,
    get_hash_algorithm,
    preview_bytes,
    public_key_fingerprint,
    rsa_pss_padding,
)


def sign_basic(private_key, message: bytes, algorithm: str = "RSA-PSS") -> bytes:
    """
    功能：使用私钥对消息进行基础签名。
    输入：私钥、消息、签名算法名称。
    输出：签名值。
    """
    if algorithm != "RSA-PSS":
        raise ValueError(f"Unsupported signature algorithm: {algorithm}")
    return private_key.sign(message, rsa_pss_padding("SHA256"), get_hash_algorithm("SHA256"))


def verify_basic(
    public_key,
    message: bytes,
    signature: bytes,
    algorithm: str = "RSA-PSS",
) -> bool:
    """
    功能：使用公钥验证签名。
    输出：True表示验证通过，False表示验证失败。
    """
    if algorithm != "RSA-PSS":
        raise ValueError(f"Unsupported signature algorithm: {algorithm}")
    try:
        public_key.verify(
            signature,
            message,
            rsa_pss_padding("SHA256"),
            get_hash_algorithm("SHA256"),
        )
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def run_basic_signature_case(message: bytes) -> dict:
    """
    功能：组织基础签名实验流程。
    返回：密钥信息摘要、签名展示片段、验签结果、异常情况记录。
    """
    private_key, public_key = generate_rsa_key_pair()
    wrong_private_key, wrong_public_key = generate_rsa_key_pair()
    signature = sign_basic(private_key, message)
    tampered = bytearray(message)
    tampered[-1] ^= 0x01

    return {
        "key_info": {
            "algorithm": "RSA-PSS + SHA256",
            "key_size": private_key.key_size,
            "public_key_fingerprint": public_key_fingerprint(public_key),
            "wrong_public_key_fingerprint": public_key_fingerprint(wrong_public_key),
            "wrong_private_key_size": wrong_private_key.key_size,
        },
        "signature_preview": preview_bytes(signature),
        "signature_length": len(signature),
        "verify_original": verify_basic(public_key, message, signature),
        "verify_tampered": verify_basic(public_key, bytes(tampered), signature),
        "verify_wrong_public_key": verify_basic(wrong_public_key, message, signature),
        "exceptions": [],
    }
