import itertools
from typing import Dict, List, Sequence

from common import COMMON_WORDS, frequency_score, score_plaintext, top_results


def apply_substitution_mapping(ciphertext: str, mapping: Dict[str, str]) -> str:
    output = []
    for ch in ciphertext.upper():
        if "A" <= ch <= "Z":
            output.append(mapping.get(ch, "_"))
        else:
            output.append(ch)
    return "".join(output)


def brute_force_reduced_alphabet(ciphertext: str, cipher_letters: Sequence[str], plain_letters: Sequence[str], top_n: int = 10) -> List[Dict]:
    if len(cipher_letters) != len(plain_letters):
        raise ValueError("cipher_letters and plain_letters must have the same length")
    results = []
    for perm in itertools.permutations(plain_letters):
        mapping = dict(zip(cipher_letters, perm))
        plaintext = apply_substitution_mapping(ciphertext, mapping)
        results.append({"key": mapping, "plaintext": plaintext, "score": score_plaintext(plaintext)})
    return top_results(results, top_n)


def word_pattern(word: str) -> tuple[int, ...]:
    indices: Dict[str, int] = {}
    pattern = []
    next_index = 0
    for ch in word:
        if ch not in indices:
            indices[ch] = next_index
            next_index += 1
        pattern.append(indices[ch])
    return tuple(pattern)


def backtracking_with_dictionary(
    ciphertext: str,
    candidate_words: Sequence[str] | None = None,
    top_n: int = 10,
    beam_width: int | None = None,
) -> List[Dict]:
    words = [word for word in ciphertext.upper().split() if word]
    source_words = candidate_words if candidate_words else COMMON_WORDS
    dictionary = sorted({word.upper() for word in source_words if word.isalpha()})
    if beam_width is None:
        beam_width = max(top_n * 10, 100)
    if beam_width < 1:
        raise ValueError("beam_width must be at least 1")
    candidate_buckets: Dict[tuple[int, tuple[int, ...]], List[str]] = {}
    for word in dictionary:
        bucket_key = (len(word), word_pattern(word))
        candidate_buckets.setdefault(bucket_key, []).append(word)

    def extend_mapping(current_map: Dict[str, str], reverse_map: Dict[str, str], cipher_word: str, plain_word: str):
        if len(cipher_word) != len(plain_word):
            return None
        next_map = dict(current_map)
        next_reverse = dict(reverse_map)
        for cipher_char, plain_char in zip(cipher_word, plain_word):
            existing_plain = next_map.get(cipher_char)
            existing_cipher = next_reverse.get(plain_char)
            if existing_plain is not None and existing_plain != plain_char:
                return None
            if existing_cipher is not None and existing_cipher != cipher_char:
                return None
            next_map[cipher_char] = plain_char
            next_reverse[plain_char] = cipher_char
        return next_map, next_reverse

    if not words or not dictionary:
        return []

    beam = [{"key": {}, "reverse_key": {}, "plain_words": [], "score": 0.0}]
    for cipher_word in words:
        bucket_key = (len(cipher_word), word_pattern(cipher_word))
        candidates = candidate_buckets.get(bucket_key, [])
        if not candidates:
            return []
        expanded = {}
        for state in beam:
            current_map = state["key"]
            reverse_map = state["reverse_key"]
            for plain_word in candidates:
                extended = extend_mapping(current_map, reverse_map, cipher_word, plain_word)
                if extended is None:
                    continue
                next_map, next_reverse = extended
                next_plain_words = state["plain_words"] + [plain_word]
                score = frequency_score(" ".join(next_plain_words))
                signature = tuple(sorted(next_map.items()))
                existing = expanded.get(signature)
                if existing is None or score > existing["score"]:
                    expanded[signature] = {
                        "key": next_map,
                        "reverse_key": next_reverse,
                        "plain_words": next_plain_words,
                        "score": score,
                    }
        if not expanded:
            return []
        beam = sorted(expanded.values(), key=lambda item: item["score"], reverse=True)[:beam_width]

    results = []
    for state in beam:
        plaintext = apply_substitution_mapping(ciphertext, state["key"])
        if "_" in plaintext:
            continue
        results.append(
            {
                "key": dict(sorted(state["key"].items())),
                "plaintext": plaintext,
                "score": frequency_score(plaintext),
            }
        )
    return top_results(results, top_n)


def factorial_26_description() -> str:
    value = 1
    for number in range(2, 27):
        value *= number
    return f"26! = {value} ≈ 4.03e26"
