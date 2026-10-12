import argparse
from time import perf_counter
from typing import Sequence

from caesar_attack import brute_force_caesar
from common import format_results
from substitution_attack import backtracking_with_dictionary, brute_force_reduced_alphabet, factorial_26_description
from vigenere_attack import brute_force_vigenere, encrypt_vigenere


def print_section(title: str) -> None:
    print(f"\n{'=' * 20} {title} {'=' * 20}")


def verify_cases() -> None:
    total_start = perf_counter()
    
    print_section("凯撒加密破解(前10个)")
    caesar_start = perf_counter()
    caesar_cipher_1 = "WKHTXLFN EURZQ IRA MXPSV RYHU WKH ODCB GRJ"
    print("密文 1:", caesar_cipher_1)
    print(format_results(brute_force_caesar(caesar_cipher_1, top_n=10)))
    caesar_elapsed_1 = perf_counter() - caesar_start
    print(f"运行时间: {caesar_elapsed_1:.4f} 秒")

    caesar_start = perf_counter()
    caesar_cipher_2 = "C FIPY SIO"
    print("\n密文 2:", caesar_cipher_2)
    print(format_results(brute_force_caesar(caesar_cipher_2, top_n=10)))
    caesar_elapsed_2 = perf_counter() - caesar_start
    print(f"运行时间: {caesar_elapsed_2:.4f} 秒")

    print_section("单表替换加密破解(前10个)")
    print(factorial_26_description())

    substitution_start = perf_counter()
    reduced_cipher = "I LOVE YOU"
    reduced_start = perf_counter()
    reduced_results = brute_force_reduced_alphabet(
        reduced_cipher,
        ["I", "L", "O", "V", "E", "Y", "U"],
        ["I", "L", "O", "V", "E", "Y", "U"],
        top_n=10,
    )
    reduced_elapsed = perf_counter() - reduced_start
    print("\n（缩小字母集）密文:", reduced_cipher)
    print(format_results(reduced_results))
    print(f"缩小字母集运行时间: {reduced_elapsed:.4f} 秒")

    pruned_cipher = "A NICE BOY"
    pruned_start = perf_counter()
    pruned_results = backtracking_with_dictionary(pruned_cipher, top_n=10)
    pruned_elapsed = perf_counter() - pruned_start
    print("\n（束搜索剪枝）密文:", pruned_cipher)
    print(format_results(pruned_results))
    print(f"束搜索剪枝运行时间: {pruned_elapsed:.4f} 秒")
    substitution_elapsed = perf_counter() - substitution_start
    print(f"\n单表替换破解总运行时间: {substitution_elapsed:.4f} 秒")

    print_section("维吉尼亚加密破解(前10个)")
    vigenere_start = perf_counter()
    plaintext = "I AM A STUDENT"
    cipher = encrypt_vigenere(plaintext, "KEY")
    print("示例明文:", plaintext)
    print("加密后密文:", cipher)
    results = brute_force_vigenere(cipher, max_key_len=3, top_n=10)
    print(format_results(results))
    vigenere_elapsed = perf_counter() - vigenere_start
    print(f"运行时间: {vigenere_elapsed:.4f} 秒")
    
    total_elapsed = perf_counter() - total_start
    print(f"\n所有破解总运行时间: {total_elapsed:.4f} 秒")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Classical cipher brute-force lab CLI")
    parser.add_argument("--ciphertext", help="Ciphertext to crack")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top candidates to show")
    parser.add_argument("--run-caesar", action="store_true", help="Run Caesar brute force")
    parser.add_argument("--run-vigenere", action="store_true", help="Run Vigenere brute force")
    parser.add_argument(
        "--run-substitution-reduced",
        action="store_true",
        help="Run substitution brute force on a reduced alphabet",
    )
    parser.add_argument(
        "--run-substitution-dictionary",
        action="store_true",
        help="Run substitution beam search with dictionary constraints",
    )
    parser.add_argument("--cipher-letters", help="Cipher alphabet letters for reduced substitution mode")
    parser.add_argument("--plain-letters", help="Plain alphabet letters for reduced substitution mode")
    parser.add_argument("--words", nargs="+", help="Optional candidate words for dictionary substitution mode")
    parser.add_argument("--beam-width", type=int, help="Beam width for substitution dictionary mode")
    parser.add_argument("--max-key-len", type=int, default=3, help="Maximum Vigenere key length")
    return parser


def has_cli_request(args: argparse.Namespace) -> bool:
    return any(
        [
            args.run_caesar,
            args.run_vigenere,
            args.run_substitution_reduced,
            args.run_substitution_dictionary,
        ]
    )


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    selected_modes = [
        args.run_caesar,
        args.run_vigenere,
        args.run_substitution_reduced,
        args.run_substitution_dictionary,
    ]
    if not any(selected_modes):
        parser.error("Select at least one run mode, or run without arguments to execute the built-in demo cases.")
    if args.ciphertext is None:
        parser.error("--ciphertext is required when using CLI run modes.")
    if args.top_k < 1:
        parser.error("--top-k must be at least 1.")
    if args.beam_width is not None and args.beam_width < 1:
        parser.error("--beam-width must be at least 1.")
    if args.run_substitution_reduced and (not args.cipher_letters or not args.plain_letters):
        parser.error("Reduced substitution mode requires both --cipher-letters and --plain-letters.")
    if args.run_substitution_reduced:
        cipher_letters = args.cipher_letters.upper()
        plain_letters = args.plain_letters.upper()
        if len(cipher_letters) != len(plain_letters):
            parser.error("--cipher-letters and --plain-letters must have the same length.")
        if len(set(cipher_letters)) != len(cipher_letters) or len(set(plain_letters)) != len(plain_letters):
            parser.error("Reduced substitution alphabets must not contain duplicate letters.")
def run_cli(args: argparse.Namespace) -> None:
    if args.run_caesar:
        print_section("Caesar attack")
        print("ciphertext:", args.ciphertext)
        print(format_results(brute_force_caesar(args.ciphertext, top_n=args.top_k)))

    if args.run_substitution_reduced:
        print_section("Substitution attack (reduced alphabet)")
        print(factorial_26_description())
        start = perf_counter()
        results = brute_force_reduced_alphabet(
            args.ciphertext,
            list(args.cipher_letters.upper()),
            list(args.plain_letters.upper()),
            top_n=args.top_k,
        )
        elapsed = perf_counter() - start
        print("ciphertext:", args.ciphertext)
        print(format_results(results))
        print(f"elapsed: {elapsed:.4f} s")

    if args.run_substitution_dictionary:
        print_section("Substitution attack (dictionary beam search)")
        print(factorial_26_description())
        if args.words:
            print("dictionary source: custom --words")
        else:
            print("dictionary source: built-in COMMON_WORDS")
        start = perf_counter()
        results = backtracking_with_dictionary(
            args.ciphertext,
            args.words,
            top_n=args.top_k,
            beam_width=args.beam_width,
        )
        elapsed = perf_counter() - start
        print("ciphertext:", args.ciphertext)
        print(format_results(results))
        print(f"elapsed: {elapsed:.4f} s")

    if args.run_vigenere:
        print_section("Vigenere attack")
        print("ciphertext:", args.ciphertext)
        start = perf_counter()
        results = brute_force_vigenere(args.ciphertext, max_key_len=args.max_key_len, top_n=args.top_k)
        elapsed = perf_counter() - start
        print(format_results(results))
        print(f"elapsed: {elapsed:.4f} s")


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not has_cli_request(args):
        verify_cases()
        return
    validate_args(args, parser)
    run_cli(args)


if __name__ == "__main__":
    main()
