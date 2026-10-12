"""DES 分组密码实验程序。

本程序面向课程实验，提供一个模块化的 DES 实现，便于理解：
- 位串与十六进制转换
- 各类置换操作
- 密钥调度（子密钥生成）
- 轮函数 F
- 单块加密/解密
- 实验报告自动生成

运行示例：
    python des_lab.py --mode report --output report.txt
    python des_lab.py --mode single --key 133457799BBCDFF1 --plaintext 0123456789ABCDEF
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

# --- DES 标准置换表与 S 盒 ---
# 这些表均来自 DES 标准，是实现加密、解密和子密钥生成的核心常量。
IP = [
    58, 50, 42, 34, 26, 18, 10, 2,
    60, 52, 44, 36, 28, 20, 12, 4,
    62, 54, 46, 38, 30, 22, 14, 6,
    64, 56, 48, 40, 32, 24, 16, 8,
    57, 49, 41, 33, 25, 17, 9, 1,
    59, 51, 43, 35, 27, 19, 11, 3,
    61, 53, 45, 37, 29, 21, 13, 5,
    63, 55, 47, 39, 31, 23, 15, 7,
]
IP_INV = [
    40, 8, 48, 16, 56, 24, 64, 32,
    39, 7, 47, 15, 55, 23, 63, 31,
    38, 6, 46, 14, 54, 22, 62, 30,
    37, 5, 45, 13, 53, 21, 61, 29,
    36, 4, 44, 12, 52, 20, 60, 28,
    35, 3, 43, 11, 51, 19, 59, 27,
    34, 2, 42, 10, 50, 18, 58, 26,
    33, 1, 41, 9, 49, 17, 57, 25,
]
E = [
    32, 1, 2, 3, 4, 5,
    4, 5, 6, 7, 8, 9,
    8, 9, 10, 11, 12, 13,
    12, 13, 14, 15, 16, 17,
    16, 17, 18, 19, 20, 21,
    20, 21, 22, 23, 24, 25,
    24, 25, 26, 27, 28, 29,
    28, 29, 30, 31, 32, 1,
]
P = [
    16, 7, 20, 21,
    29, 12, 28, 17,
    1, 15, 23, 26,
    5, 18, 31, 10,
    2, 8, 24, 14,
    32, 27, 3, 9,
    19, 13, 30, 6,
    22, 11, 4, 25,
]
PC1 = [
    57, 49, 41, 33, 25, 17, 9,
    1, 58, 50, 42, 34, 26, 18,
    10, 2, 59, 51, 43, 35, 27,
    19, 11, 3, 60, 52, 44, 36,
    63, 55, 47, 39, 31, 23, 15,
    7, 62, 54, 46, 38, 30, 22,
    14, 6, 61, 53, 45, 37, 29,
    21, 13, 5, 28, 20, 12, 4,
]
PC2 = [
    14, 17, 11, 24, 1, 5,
    3, 28, 15, 6, 21, 10,
    23, 19, 12, 4, 26, 8,
    16, 7, 27, 20, 13, 2,
    41, 52, 31, 37, 47, 55,
    30, 40, 51, 45, 33, 48,
    44, 49, 39, 56, 34, 53,
    46, 42, 50, 36, 29, 32,
]
SHIFT_SCHEDULE = [1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1]
S_BOXES = [
    [
        [14, 4, 13, 1, 2, 15, 11, 8, 3, 10, 6, 12, 5, 9, 0, 7],
        [0, 15, 7, 4, 14, 2, 13, 1, 10, 6, 12, 11, 9, 5, 3, 8],
        [4, 1, 14, 8, 13, 6, 2, 11, 15, 12, 9, 7, 3, 10, 5, 0],
        [15, 12, 8, 2, 4, 9, 1, 7, 5, 11, 3, 14, 10, 0, 6, 13],
    ],
    [
        [15, 1, 8, 14, 6, 11, 3, 4, 9, 7, 2, 13, 12, 0, 5, 10],
        [3, 13, 4, 7, 15, 2, 8, 14, 12, 0, 1, 10, 6, 9, 11, 5],
        [0, 14, 7, 11, 10, 4, 13, 1, 5, 8, 12, 6, 9, 3, 2, 15],
        [13, 8, 10, 1, 3, 15, 4, 2, 11, 6, 7, 12, 0, 5, 14, 9],
    ],
    [
        [10, 0, 9, 14, 6, 3, 15, 5, 1, 13, 12, 7, 11, 4, 2, 8],
        [13, 7, 0, 9, 3, 4, 6, 10, 2, 8, 5, 14, 12, 11, 15, 1],
        [13, 6, 4, 9, 8, 15, 3, 0, 11, 1, 2, 12, 5, 10, 14, 7],
        [1, 10, 13, 0, 6, 9, 8, 7, 4, 15, 14, 3, 11, 5, 2, 12],
    ],
    [
        [7, 13, 14, 3, 0, 6, 9, 10, 1, 2, 8, 5, 11, 12, 4, 15],
        [13, 8, 11, 5, 6, 15, 0, 3, 4, 7, 2, 12, 1, 10, 14, 9],
        [10, 6, 9, 0, 12, 11, 7, 13, 15, 1, 3, 14, 5, 2, 8, 4],
        [3, 15, 0, 6, 10, 1, 13, 8, 9, 4, 5, 11, 12, 7, 2, 14],
    ],
    [
        [2, 12, 4, 1, 7, 10, 11, 6, 8, 5, 3, 15, 13, 0, 14, 9],
        [14, 11, 2, 12, 4, 7, 13, 1, 5, 0, 15, 10, 3, 9, 8, 6],
        [4, 2, 1, 11, 10, 13, 7, 8, 15, 9, 12, 5, 6, 3, 0, 14],
        [11, 8, 12, 7, 1, 14, 2, 13, 6, 15, 0, 9, 10, 4, 5, 3],
    ],
    [
        [12, 1, 10, 15, 9, 2, 6, 8, 0, 13, 3, 4, 14, 7, 5, 11],
        [10, 15, 4, 2, 7, 12, 9, 5, 6, 1, 13, 14, 0, 11, 3, 8],
        [9, 14, 15, 5, 2, 8, 12, 3, 7, 0, 4, 10, 1, 13, 11, 6],
        [4, 3, 2, 12, 9, 5, 15, 10, 11, 14, 1, 7, 6, 0, 8, 13],
    ],
    [
        [4, 11, 2, 14, 15, 0, 8, 13, 3, 12, 9, 7, 5, 10, 6, 1],
        [13, 0, 11, 7, 4, 9, 1, 10, 14, 3, 5, 12, 2, 15, 8, 6],
        [1, 4, 11, 13, 12, 3, 7, 14, 10, 15, 6, 8, 0, 5, 9, 2],
        [6, 11, 13, 8, 1, 4, 10, 7, 9, 5, 0, 15, 14, 2, 3, 12],
    ],
    [
        [13, 2, 8, 4, 6, 15, 11, 1, 10, 9, 3, 14, 5, 0, 12, 7],
        [1, 15, 13, 8, 10, 3, 7, 4, 12, 5, 6, 11, 0, 14, 9, 2],
        [7, 11, 4, 1, 9, 12, 14, 2, 0, 6, 10, 13, 15, 3, 5, 8],
        [2, 1, 14, 7, 4, 10, 8, 13, 15, 12, 9, 0, 3, 5, 6, 11],
    ],
]


# --- 位串辅助函数 ---
# 这一部分负责十六进制/二进制转换、置换、异或、拆分和左移等基础操作。

def hex_to_bits(hex_str: str, width: int | None = None) -> str:
    """将十六进制字符串转换为固定长度的二进制字符串。"""
    value = int(hex_str, 16)
    if width is None:
        width = len(hex_str) * 4
    return f"{value:0{width}b}"


def bits_to_hex(bits: str, width: int | None = None) -> str:
    """将二进制字符串转换为固定宽度的十六进制字符串。"""
    if width is None:
        width = (len(bits) + 3) // 4
    return f"{int(bits, 2):0{width}X}"


def permute(bits: str, table: Sequence[int]) -> str:
    """按照给定置换表重新排列位序。"""
    return "".join(bits[i - 1] for i in table)


def xor_bits(a: str, b: str) -> str:
    """对两个等长位串逐位异或。"""
    return "".join("1" if x != y else "0" for x, y in zip(a, b))


def left_shift(bits: str, n: int) -> str:
    """对位串做循环左移。"""
    n %= len(bits)
    return bits[n:] + bits[:n]


def split_bits(bits: str, n: int) -> Tuple[str, str]:
    """将位串按指定长度拆分为左右两部分。"""
    return bits[:n], bits[n:]


def s_box_substitution(bits48: str) -> str:
    """将 48 bit 输入按 8 个 S 盒压缩为 32 bit。

    每 6 bit 作为一个分组：
    - 首尾两位确定行号
    - 中间四位确定列号
    """
    output = []
    for i in range(8):
        chunk = bits48[i * 6 : (i + 1) * 6]
        row = int(chunk[0] + chunk[5], 2)
        col = int(chunk[1:5], 2)
        value = S_BOXES[i][row][col]
        output.append(f"{value:04b}")
    return "".join(output)


# --- 密钥调度模块 ---
# 负责将 64 bit 原始密钥转换成 16 个 48 bit 子密钥。

def generate_subkeys(key_hex: str) -> List[str]:
    """根据 DES 密钥调度规则生成 16 个子密钥。"""
    key_bits = hex_to_bits(key_hex, 64)
    permuted = permute(key_bits, PC1)
    c, d = split_bits(permuted, 28)
    subkeys = []
    for shift in SHIFT_SCHEDULE:
        c = left_shift(c, shift)
        d = left_shift(d, shift)
        subkey = permute(c + d, PC2)
        subkeys.append(subkey)
    return subkeys


# --- 轮函数 F ---
# 按照 E 扩展 → 异或 → S 盒代换 → P 置换 的顺序实现。

def round_function(r32: str, subkey48: str) -> str:
    """DES 单轮中的核心变换函数 F。"""
    expanded = permute(r32, E)
    mixed = xor_bits(expanded, subkey48)
    substituted = s_box_substitution(mixed)
    return permute(substituted, P)


# --- DES 核心加密/解密流程 ---
# 加密与解密结构相同，只是子密钥的使用顺序相反。

def des_encrypt_block(plaintext_hex: str, key_hex: str, trace: bool = False):
    """对单个 64 bit 明文分组执行 DES 加密。"""
    block = hex_to_bits(plaintext_hex, 64)
    subkeys = generate_subkeys(key_hex)
    state = permute(block, IP)
    l, r = split_bits(state, 32)
    rounds = []
    for i, subkey in enumerate(subkeys, start=1):
        # Feistel 结构：下一轮左半部分来自上一轮右半部分
        new_l = r
        # 下一轮右半部分 = 左半部分 XOR F(右半部分, 子密钥)
        new_r = xor_bits(l, round_function(r, subkey))
        l, r = new_l, new_r
        if trace:
            rounds.append((i, l, r, bits_to_hex(l + r, 16)))
    # 16 轮后要交换左右半部，再进行逆初始置换
    preoutput = r + l
    ciphertext = bits_to_hex(permute(preoutput, IP_INV), 16)
    return ciphertext, rounds


def des_decrypt_block(ciphertext_hex: str, key_hex: str, trace: bool = False):
    """对单个 64 bit 密文分组执行 DES 解密。"""
    block = hex_to_bits(ciphertext_hex, 64)
    subkeys = list(reversed(generate_subkeys(key_hex)))
    state = permute(block, IP)
    l, r = split_bits(state, 32)
    rounds = []
    for i, subkey in enumerate(subkeys, start=1):
        new_l = r
        new_r = xor_bits(l, round_function(r, subkey))
        l, r = new_l, new_r
        if trace:
            rounds.append((i, l, r, bits_to_hex(l + r, 16)))
    preoutput = r + l
    plaintext = bits_to_hex(permute(preoutput, IP_INV), 16)
    return plaintext, rounds


@dataclass
class TestVector:
    """实验测试向量，保存名称、密钥和明文。"""
    name: str
    key: str
    plaintext: str


TEST_VECTORS = [
    TestVector("标准向量", "133457799BBCDFF1", "0123456789ABCDEF"),
    TestVector("全0向量", "0000000000000000", "0000000000000000"),
    TestVector("交替位型1", "AAAAAAAAAAAAAAAA", "5555555555555555"),
    TestVector("随机样例", "0123456789ABCDEF", "FEDCBA9876543210"),
]


def build_report() -> str:
    """根据预设测试向量生成课程实验报告文本。"""
    lines = []
    lines.append("《网络空间安全技术》课程报告")
    lines.append("")
    lines.append("实验名称：DES 分组密码加密与解密实验")
    lines.append("")
    lines.append("一、实验名称")
    lines.append("DES 分组密码加密与解密实验。")
    lines.append("")
    lines.append("二、实验目的")
    lines.append("（1）理解 DES 的基本参数、Feistel 网络结构以及加密与解密结构相同、子密钥顺序相反的核心特点。")
    lines.append("（2）掌握 DES 中初始置换 IP、轮函数 F、8 个 S 盒、P 置换、逆初始置换 IP^-1 以及密钥调度的作用。")
    lines.append("（3）学会将 DES 的实现拆分为位串处理、置换、异或、子密钥生成、单轮运算、整体加密与整体解密等模块。")
    lines.append("（4）能够设计实验程序，对单个 64 bit 分组完成加密、解密与往返一致性验证。")
    lines.append("")
    lines.append("三、实验原理")
    lines.append("1. DES 加密流程：明文分组经 IP 置换后分为 L0 和 R0，随后进行 16 轮 Feistel 迭代，轮间只交换左右半部并引入轮函数 F，最终交换左右并执行 IP^-1 得到密文。")
    lines.append("2. 轮函数 F 的构成：E 扩展、与子密钥异或、S 盒代换、P 置换。")
    lines.append("3. 子密钥生成原理：原始 64 bit 密钥经 PC-1 去掉奇偶校验位，得到 56 bit，分成 C0、D0 后按照移位表循环左移，再经 PC-2 压缩成 16 个 48 bit 子密钥。")
    lines.append("4. DES 解密流程：与加密流程结构相同，只需将 16 个子密钥逆序使用即可。")
    lines.append("")
    lines.append("四、实验环境")
    lines.append("操作系统：Windows / Linux / macOS 均可。")
    lines.append("编程语言：Python 3.x。")
    lines.append("开发工具：PyCharm、VS Code、Jupyter Notebook 等。")
    lines.append("建议模块：仅使用基础语法与常规库完成，不依赖现成 DES 封装。")
    lines.append("")
    lines.append("五、实验内容与任务要求")
    lines.append("（1）完成位串表示与辅助运算模块：十六进制/二进制转换、置换、分组拆分、循环左移、异或；")
    lines.append("（2）完成密钥调度模块：根据 PC-1、移位表与 PC-2 生成 16 个子密钥；")
    lines.append("（3）完成轮函数 F：实现 E 扩展、与 Ki 异或、S 盒代换与 P 置换；")
    lines.append("（4）完成 DES 单块加密模块：按照 IP、16 轮、交换、IP^-1 的顺序处理；")
    lines.append("（5）完成 DES 单块解密模块：复用相同框架，使用逆序子密钥；")
    lines.append("（6）设计实验验证：记录输入、输出、是否成功复原原文、关键轮状态或调试信息。")
    lines.append("")
    lines.append("六、程序设计")
    lines.append("本实验采用字符串形式的 0/1 位串作为内部表示，便于实现置换与异或；所有标准表集中放置，通用置换函数复用于 IP、IP^-1、E、P、PC-1、PC-2 等步骤。")
    lines.append("密钥调度通过 PC-1、循环左移和 PC-2 生成 16 个子密钥；轮函数 F 严格按 E 扩展、异或、S 盒和 P 置换的顺序实现。")
    lines.append("加密时执行 IP、16 轮 Feistel 迭代、末轮交换和 IP^-1；解密时仅将子密钥逆序输入。")
    lines.append("")
    lines.append("七、实验结果")
    for vec in TEST_VECTORS:
        cipher, _ = des_encrypt_block(vec.plaintext, vec.key)
        recovered, _ = des_decrypt_block(cipher, vec.key)
        lines.append(f"【{vec.name}】")
        lines.append(f"Key：{vec.key}")
        lines.append(f"Plaintext：{vec.plaintext}")
        lines.append(f"Ciphertext：{cipher}")
        lines.append(f"Decrypt：{recovered}")
        lines.append(f"往返一致性：{'成功' if recovered.upper() == vec.plaintext.upper() else '失败'}")
        lines.append("")
    lines.append("八、总结")
    lines.append("通过本实验，完整实现了 DES 的分组加密与解密流程，掌握了 Feistel 网络、子密钥生成、S 盒代换和置换操作的具体实现方式。程序支持参数化输入，并可自动生成 txt 结果报告，便于课程提交与实验展示。")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """命令行入口：支持单次测试与报告生成两种模式。"""
    parser = argparse.ArgumentParser(description="DES experiment implementation")
    parser.add_argument("--mode", choices=["single", "report"], default="report")
    parser.add_argument("--key", help="64-bit hex key")
    parser.add_argument("--plaintext", help="64-bit hex plaintext")
    parser.add_argument("--ciphertext", help="64-bit hex ciphertext")
    parser.add_argument("--output", default="des_report.txt", help="Output txt file for report mode")
    args = parser.parse_args()

    if args.mode == "single":
        if not args.key:
            raise SystemExit("--key is required in single mode")
        if not args.plaintext and not args.ciphertext:
            raise SystemExit("Provide --plaintext for encryption or --ciphertext for decryption")
        if args.plaintext:
            cipher, rounds = des_encrypt_block(args.plaintext, args.key, trace=True)
            print(f"Key: {args.key}")
            print(f"Plaintext: {args.plaintext}")
            print(f"Ciphertext: {cipher}")
            print(f"Round count: {len(rounds)}")
            print(f"Round16 state: {rounds[-1][3] if rounds else 'N/A'}")
        else:
            plain, rounds = des_decrypt_block(args.ciphertext, args.key, trace=True)
            print(f"Key: {args.key}")
            print(f"Ciphertext: {args.ciphertext}")
            print(f"Plaintext: {plain}")
            print(f"Round count: {len(rounds)}")
            print(f"Round16 state: {rounds[-1][3] if rounds else 'N/A'}")
        return

    report = build_report()
    output_path = Path(args.output)
    output_path.write_text(report, encoding="utf-8")
    print(f"Report written to {output_path.resolve()}")


if __name__ == "__main__":
    main()
