from typing import Dict, List

from common import ALPHABET, score_plaintext, top_results


def decrypt_caesar(ciphertext: str, shift: int) -> str:
    output = []
    for ch in ciphertext.upper():
        if ch in ALPHABET:
            index = (ALPHABET.index(ch) - shift) % 26
            output.append(ALPHABET[index])
        else:
            output.append(ch)
    return "".join(output)


def brute_force_caesar(ciphertext: str, top_n: int = 5) -> List[Dict]:
    results = []
    for shift in range(26):
        plaintext = decrypt_caesar(ciphertext, shift)
        results.append({"key": shift, "plaintext": plaintext, "score": score_plaintext(plaintext)})
    return top_results(results, top_n)
