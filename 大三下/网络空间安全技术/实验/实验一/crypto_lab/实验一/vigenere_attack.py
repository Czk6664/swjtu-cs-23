import itertools
from typing import Dict, List

from common import ALPHABET, score_plaintext, top_results


def encrypt_vigenere(plaintext: str, key: str) -> str:
    key = "".join(ch for ch in key.upper() if ch in ALPHABET)
    if not key:
        raise ValueError("key must contain at least one alphabetic character")
    output = []
    key_index = 0
    for ch in plaintext.upper():
        if ch in ALPHABET:
            shift = ALPHABET.index(key[key_index % len(key)])
            cipher_index = (ALPHABET.index(ch) + shift) % 26
            output.append(ALPHABET[cipher_index])
            key_index += 1
        else:
            output.append(ch)
    return "".join(output)


def decrypt_vigenere(ciphertext: str, key: str) -> str:
    key = "".join(ch for ch in key.upper() if ch in ALPHABET)
    if not key:
        raise ValueError("key must contain at least one alphabetic character")
    output = []
    key_index = 0
    for ch in ciphertext.upper():
        if ch in ALPHABET:
            shift = ALPHABET.index(key[key_index % len(key)])
            plain_index = (ALPHABET.index(ch) - shift) % 26
            output.append(ALPHABET[plain_index])
            key_index += 1
        else:
            output.append(ch)
    return "".join(output)


def brute_force_vigenere(ciphertext: str, max_key_len: int = 3, top_n: int = 10) -> List[Dict]:
    if max_key_len < 1:
        raise ValueError("max_key_len must be at least 1")
    if max_key_len > 3:
        raise ValueError("max_key_len above 3 is intentionally blocked in this lab demo to avoid explosive brute-force cost")
    results = []
    for key_len in range(1, max_key_len + 1):
        for key_tuple in itertools.product(ALPHABET, repeat=key_len):
            key = "".join(key_tuple)
            plaintext = decrypt_vigenere(ciphertext, key)
            results.append({"key": key, "plaintext": plaintext, "score": score_plaintext(plaintext)})
    return top_results(results, top_n)
