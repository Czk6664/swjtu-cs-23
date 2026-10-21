import json
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import utils

from crypto_utils import (
    b64decode,
    b64encode,
    get_hash_algorithm,
    preview_bytes,
    rsa_pss_padding,
    utc_timestamp,
)


def digest_file(file_path: str, hash_alg: str = "SHA256") -> bytes:
    """
    功能：分块读取文件并计算文件摘要。
    """
    digest = hashes.Hash(get_hash_algorithm(hash_alg))
    with open(file_path, "rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.finalize()


def sign_file(private_key, file_path: str, sign_path: str) -> None:
    """
    功能：对文件生成分离式签名，并写入签名文件。
    """
    hash_alg = "SHA256"
    digest = digest_file(file_path, hash_alg)
    signature = private_key.sign(
        digest,
        rsa_pss_padding(hash_alg),
        utils.Prehashed(get_hash_algorithm(hash_alg)),
    )
    package = {
        "format": "detached-file-signature-v1",
        "sign_alg": "RSA-PSS",
        "hash_alg": hash_alg,
        "created_at": utc_timestamp(),
        "file_digest_hex": digest.hex(),
        "signature_b64": b64encode(signature),
    }
    Path(sign_path).write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")


def verify_file_signature(public_key, file_path: str, sign_path: str) -> bool:
    """
    功能：读取原文件和签名文件，验证签名是否有效。
    """
    try:
        package = json.loads(Path(sign_path).read_text(encoding="utf-8"))
        hash_alg = package.get("hash_alg", "SHA256")
        digest = digest_file(file_path, hash_alg)
        signature = b64decode(package["signature_b64"])
        public_key.verify(
            signature,
            digest,
            rsa_pss_padding(hash_alg),
            utils.Prehashed(get_hash_algorithm(hash_alg)),
        )
        return True
    except (InvalidSignature, OSError, KeyError, ValueError, TypeError, json.JSONDecodeError):
        return False


def build_file_signature_report(
    file_path: str,
    sign_path: str,
    verify_result: bool,
) -> dict:
    """
    功能：整理文件签名实验结果，供实验报告引用。
    """
    digest = digest_file(file_path)
    file_stat = Path(file_path).stat()
    sign_stat = Path(sign_path).stat()
    return {
        "file_path": str(file_path),
        "sign_path": str(sign_path),
        "file_size": file_stat.st_size,
        "sign_file_size": sign_stat.st_size,
        "digest_hex": digest.hex(),
        "digest_preview": preview_bytes(digest),
        "verify_result": verify_result,
    }
