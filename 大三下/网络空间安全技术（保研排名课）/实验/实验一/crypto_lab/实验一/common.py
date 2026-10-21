import re
import time
from collections import Counter
from typing import Callable, Dict, Iterable, List, Sequence

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ENGLISH_FREQ = {
    "A": 8.167, "B": 1.492, "C": 2.782, "D": 4.253, "E": 12.702,
    "F": 2.228, "G": 2.015, "H": 6.094, "I": 6.966, "J": 0.153,
    "K": 0.772, "L": 4.025, "M": 2.406, "N": 6.749, "O": 7.507,
    "P": 1.929, "Q": 0.095, "R": 5.987, "S": 6.327, "T": 9.056,
    "U": 2.758, "V": 0.978, "W": 2.360, "X": 0.150, "Y": 1.974,
    "Z": 0.074,
}
COMMON_WORDS = {
    "THE", "BE", "TO", "OF", "AND", "A", "IN", "THAT", "HAVE", "I",
    "IT", "FOR", "NOT", "ON", "WITH", "HE", "AS", "YOU", "DO", "AT",
    "THIS", "BUT", "HIS", "BY", "FROM", "THEY", "WE", "SAY", "HER",
    "SHE", "OR", "AN", "WILL", "MY", "ONE", "ALL", "WOULD", "THERE",
    "THEIR", "IS", "ARE", "AM", "STUDENT", "LOVE", "QUICK", "BROWN",
    "FOX", "JUMPS", "OVER", "LAZY", "DOG", "NICE", "BOY", "HELLO",
    "WORLD", "ATTACK", "DAWN", "KEY", "SECRET", "MESSAGE", "TEST"
}
COMMON_BIGRAMS = {
    "TH", "HE", "IN", "ER", "AN", "RE", "ON", "AT", "EN", "ND",
    "TI", "ES", "OR", "TE", "OF", "ED", "IS", "IT", "AL", "AR",
    "ST", "TO", "NT", "NG", "SE", "HA", "AS", "OU", "IO", "LE"
}
COMMON_TRIGRAMS = {
    "THE", "AND", "ING", "HER", "ERE", "ENT", "THA", "NTH", "WAS",
    "ETH", "FOR", "HAT", "ION", "TIO", "VER"
}


def normalize_text(text: str, keep_spaces: bool = True) -> str:
    text = text.upper()
    if keep_spaces:
        text = re.sub(r"[^A-Z\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()
    return re.sub(r"[^A-Z]", "", text)


def letters_only(text: str) -> str:
    return normalize_text(text, keep_spaces=False)


def frequency_score(text: str) -> float:
    cleaned = letters_only(text)
    if not cleaned:
        return float("-inf")
    total = len(cleaned)
    counts = Counter(cleaned)
    chi_square = 0.0
    for letter in ALPHABET:
        observed = counts.get(letter, 0)
        expected = total * ENGLISH_FREQ[letter] / 100
        if expected > 0:
            chi_square += ((observed - expected) ** 2) / expected
    return -chi_square


def word_score(text: str) -> float:
    words = normalize_text(text, keep_spaces=True).split()
    if not words:
        return 0.0
    score = 0.0
    for word in words:
        if word in COMMON_WORDS:
            score += 6.0 + len(word) * 0.3
        elif len(word) == 1 and word in {"A", "I"}:
            score += 2.0
        elif len(word) >= 3 and any(token in word for token in ("THE", "ING", "ION")):
            score += 1.5
    return score


def ngram_score(text: str) -> float:
    cleaned = letters_only(text)
    bigrams = sum(1 for i in range(len(cleaned) - 1) if cleaned[i:i + 2] in COMMON_BIGRAMS)
    trigrams = sum(1 for i in range(len(cleaned) - 2) if cleaned[i:i + 3] in COMMON_TRIGRAMS)
    return bigrams * 1.2 + trigrams * 2.0


def vowel_ratio_score(text: str) -> float:
    cleaned = letters_only(text)
    if not cleaned:
        return 0.0
    ratio = sum(1 for ch in cleaned if ch in "AEIOU") / len(cleaned)
    return -abs(ratio - 0.38) * 20


def score_plaintext(text: str) -> float:
    return (
        frequency_score(text) * 0.45
        + word_score(text) * 1.8
        + ngram_score(text) * 1.5
        + vowel_ratio_score(text) * 0.6
    )


def timed_call(func: Callable, *args, **kwargs):
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return result, elapsed


def top_results(results: Sequence[Dict], top_n: int = 5) -> List[Dict]:
    return sorted(results, key=lambda item: item["score"], reverse=True)[:top_n]


def format_results(results: Iterable[Dict]) -> str:
    lines = []
    for index, item in enumerate(results, start=1):
        lines.append(
            f"{index}. key={item['key']} | score={item['score']:.2f} | text={item['plaintext']}"
        )
    return "\n".join(lines)
