import base64
import copy
import json
import os
from datetime import datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


RSA_KEY_SIZE = 2048
AES_GCM_KEY_SIZE = 32
AES_GCM_NONCE_SIZE = 12
AES_GCM_TAG_SIZE = 16


def generate_rsa_key_pair(key_size: int = RSA_KEY_SIZE):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    return private_key, private_key.public_key()


def get_hash_algorithm(name: str = "SHA256"):
    normalized = name.upper().replace("-", "")
    if normalized == "SHA256":
        return hashes.SHA256()
    if normalized == "SHA384":
        return hashes.SHA384()
    if normalized == "SHA512":
        return hashes.SHA512()
    raise ValueError(f"Unsupported hash algorithm: {name}")


def rsa_pss_padding(hash_alg: str = "SHA256"):
    return padding.PSS(
        mgf=padding.MGF1(get_hash_algorithm(hash_alg)),
        salt_length=padding.PSS.MAX_LENGTH,
    )


def rsa_oaep_padding(hash_alg: str = "SHA256"):
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=get_hash_algorithm(hash_alg)),
        algorithm=get_hash_algorithm(hash_alg),
        label=None,
    )


def hash_bytes(data: bytes, hash_alg: str = "SHA256") -> bytes:
    digest = hashes.Hash(get_hash_algorithm(hash_alg))
    digest.update(data)
    return digest.finalize()


def b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"), validate=True)


def preview_bytes(data: bytes, size: int = 16) -> str:
    return data[:size].hex()


def canonical_json_bytes(obj: dict) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def canonical_json_text(obj: dict) -> str:
    return canonical_json_bytes(obj).decode("utf-8")


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def random_nonce_hex(size: int = 16) -> str:
    return os.urandom(size).hex()


def public_key_fingerprint(public_key) -> str:
    der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return hash_bytes(der, "SHA256").hex()[:32]


def rsa_encrypt(public_key, plaintext: bytes) -> bytes:
    return public_key.encrypt(plaintext, rsa_oaep_padding("SHA256"))


def rsa_decrypt(private_key, ciphertext: bytes) -> bytes:
    return private_key.decrypt(ciphertext, rsa_oaep_padding("SHA256"))


def aes_gcm_encrypt(plaintext: bytes, associated_data: bytes | None = None) -> dict:
    key = os.urandom(AES_GCM_KEY_SIZE)
    nonce = os.urandom(AES_GCM_NONCE_SIZE)
    encrypted = AESGCM(key).encrypt(nonce, plaintext, associated_data)
    return {
        "key": key,
        "nonce": nonce,
        "ciphertext": encrypted[:-AES_GCM_TAG_SIZE],
        "tag": encrypted[-AES_GCM_TAG_SIZE:],
    }


def aes_gcm_decrypt(
    key: bytes,
    nonce: bytes,
    ciphertext: bytes,
    tag: bytes,
    associated_data: bytes | None = None,
) -> bytes:
    return AESGCM(key).decrypt(nonce, ciphertext + tag, associated_data)


def copy_package(package: dict) -> dict:
    return copy.deepcopy(package)


def flip_b64_field(package: dict, field_name: str) -> dict:
    tampered = copy_package(package)
    raw = bytearray(b64decode(tampered[field_name]))
    if not raw:
        raw.append(0)
    raw[0] ^= 0x01
    tampered[field_name] = b64encode(bytes(raw))
    return tampered


def sign_canonical_dict(private_key, data: dict, hash_alg: str = "SHA256") -> bytes:
    return private_key.sign(
        canonical_json_bytes(data),
        rsa_pss_padding(hash_alg),
        get_hash_algorithm(hash_alg),
    )


def verify_canonical_dict(
    public_key,
    data: dict,
    signature: bytes,
    hash_alg: str = "SHA256",
) -> bool:
    try:
        public_key.verify(
            signature,
            canonical_json_bytes(data),
            rsa_pss_padding(hash_alg),
            get_hash_algorithm(hash_alg),
        )
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False
