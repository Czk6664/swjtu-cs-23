import json
from pathlib import Path

from basic_signature import sign_basic, verify_basic
from crypto_utils import (
    b64decode,
    b64encode,
    copy_package,
    generate_rsa_key_pair,
    hash_bytes,
    preview_bytes,
    public_key_fingerprint,
    utc_timestamp,
)
from digest_signature import (
    compare_digest_before_after,
    sign_with_digest,
    verify_with_digest,
)
from file_signature import (
    build_file_signature_report,
    sign_file,
    verify_file_signature,
)
from metadata_signature import (
    build_metadata,
    sign_with_metadata,
    verify_metadata_signature,
)
from secure_signature import (
    build_secure_envelope,
    decrypt_then_verify,
    encrypt_then_sign,
    open_secure_envelope,
    sign_then_encrypt,
    tamper_package_b64_field,
    tamper_secure_envelope,
    tamper_sign_then_encrypt_inner_signature,
    verify_then_decrypt,
)


MESSAGE_M1 = "2026-04-20 数字签名实验：Hello, World! 学号=20260001".encode("utf-8")
MESSAGE_M1_TAMPERED = "2026-04-20 数字签名实验：Hello, World! 学号=20260002".encode("utf-8")
MESSAGE_MBIN = MESSAGE_M1 + b"\x00"


def _yes_no(value: bool) -> str:
    return "通过" if value else "失败"


def _ok_fail(value: bool) -> str:
    return "成功" if value else "失败"


def _make_metadata(sender_id: str = "Alice", receiver_id: str = "Bob") -> dict:
    metadata = build_metadata(sender_id, "RSA-PSS+SHA256")
    metadata["receiver_id"] = receiver_id
    return metadata


def _tamper_signature_file(source: Path, target: Path) -> None:
    package = json.loads(source.read_text(encoding="utf-8"))
    raw_signature = bytearray(b64decode(package["signature_b64"]))
    raw_signature[0] ^= 0x01
    package["signature_b64"] = b64encode(bytes(raw_signature))
    target.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")


def _prepare_file_case() -> tuple[Path, Path, Path, Path]:
    file_path = Path("test_small.txt")
    tampered_file_path = Path("test_small_tampered.txt")
    sign_path = Path("test_small.txt.sig")
    tampered_sign_path = Path("test_small_tampered.sig")

    file_path.write_text(
        "test_small.txt for digital signature experiment, value=98\n",
        encoding="utf-8",
    )
    tampered_file_path.write_text(
        file_path.read_text(encoding="utf-8").replace("98", "99"),
        encoding="utf-8",
    )
    return file_path, tampered_file_path, sign_path, tampered_sign_path


def run_all_experiments():
    """
    实验入口：
    1. 读取或生成实验消息与文件
    2. 生成发送方和接收方密钥对
    3. 执行基础签名实验
    4. 执行摘要签名与篡改检测实验
    5. 执行文件分离式签名实验
    6. 执行带元数据签名实验
    7. 执行先签名后加密实验
    8. 执行先加密后签名实验
    9. 执行数字信封 + 签名综合实验
    10. 汇总结果并输出报告数据
    """
    # 生成 Alice 的 RSA 密钥对，作为发送方签名使用
    alice_private, alice_public = generate_rsa_key_pair()
    # 生成 Bob 的 RSA 密钥对，作为接收方解密使用
    bob_private, bob_public = generate_rsa_key_pair()
    # 额外生成一组错误密钥，用于错误公钥/错误私钥测试
    wrong_private, wrong_public = generate_rsa_key_pair()

    # 初始化总结果字典，用于保存所有实验结果
    results = {
        # 记录参与方和公钥指纹信息
        "participants": {
            # 发送方名称
            "sender": "Alice",
            # 接收方名称
            "receiver": "Bob",
            # Alice 公钥指纹，便于标识公钥
            "alice_public_key_fingerprint": public_key_fingerprint(alice_public),
            # Bob 公钥指纹，便于标识公钥
            "bob_public_key_fingerprint": public_key_fingerprint(bob_public),
            # 错误公钥指纹，用于报告错误公钥场景
            "wrong_public_key_fingerprint": public_key_fingerprint(wrong_public),
        },
        # 记录实验用统一消息
        "messages": {
            # 原始消息 M1
            "M1": MESSAGE_M1.decode("utf-8"),
            # 篡改消息 M1'
            "M1_tampered": MESSAGE_M1_TAMPERED.decode("utf-8"),
            # 二进制消息 Mbin 的长度
            "Mbin_length": len(MESSAGE_MBIN),
            # Mbin 末尾字节的 hex 展示
            "Mbin_tail_hex": MESSAGE_MBIN[-4:].hex(),
        },
    }

    # -------------------- 实验一：基础数字签名 --------------------

    # 使用 Alice 私钥对原始消息 M1 生成签名
    basic_signature = sign_basic(alice_private, MESSAGE_M1)
    # 保存实验一的结果
    results["experiment_1"] = {
        # 展示签名值前几个字节，便于报告展示
        "signature_preview": preview_bytes(basic_signature),
        # 记录签名长度
        "signature_length": len(basic_signature),
        # A1：正确消息 + 正确公钥验签
        "A1_correct_signature": verify_basic(alice_public, MESSAGE_M1, basic_signature),
        # A2：篡改消息后验签
        "A2_tampered_message": verify_basic(alice_public, MESSAGE_M1_TAMPERED, basic_signature),
        # A3：使用错误公钥验签
        "A3_wrong_public_key": verify_basic(wrong_public, MESSAGE_M1, basic_signature),
        # 额外测试：对包含 NUL 的二进制消息签名并验签
        "Mbin_signature_valid": verify_basic(
            alice_public,
            MESSAGE_MBIN,
            sign_basic(alice_private, MESSAGE_MBIN),
        ),
    }

    # -------------------- 实验二：摘要后签名与完整性检测 --------------------

    # 对原始消息 M1 进行“先摘要后签名”
    digest_package = sign_with_digest(alice_private, MESSAGE_M1)
    # 比较原始消息和篡改消息的摘要差异
    digest_compare = compare_digest_before_after(MESSAGE_M1, MESSAGE_M1_TAMPERED)
    # 保存实验二的结果
    results["experiment_2"] = {
        # 记录原始消息摘要
        "Hash(M1)": digest_compare["original_digest_hex"],
        # 记录篡改消息摘要
        "Hash(M1')": digest_compare["tampered_digest_hex"],
        # 判断两个摘要是否相同
        "digest_same": digest_compare["same"],
        # 展示签名前几个字节
        "signature_preview": digest_package["signature_preview"],
        # B1：原始消息验签
        "B1_original_message": verify_with_digest(
            alice_public,
            MESSAGE_M1,
            digest_package["signature"],
        ),
        # B2：篡改消息验签
        "B2_tampered_message": verify_with_digest(
            alice_public,
            MESSAGE_M1_TAMPERED,
            digest_package["signature"],
        ),
        # B3：摘要对比是否不同
        "B3_digest_compare": not digest_compare["same"],
    }

    # -------------------- 实验三：文件分离式数字签名 --------------------

    # 准备文件实验所需的原文件、篡改文件、签名文件路径
    file_path, tampered_file_path, sign_path, tampered_sign_path = _prepare_file_case()
    # 对原文件生成独立签名文件
    sign_file(alice_private, str(file_path), str(sign_path))
    # 对签名文件做篡改，生成一个错误签名文件
    _tamper_signature_file(sign_path, tampered_sign_path)
    # 验证原文件与原签名是否匹配
    file_verify_result = verify_file_signature(alice_public, str(file_path), str(sign_path))
    # 保存实验三的结果
    results["experiment_3"] = {
        # 生成实验报告用的文件签名摘要信息
        "report": build_file_signature_report(str(file_path), str(sign_path), file_verify_result),
        # C1：签名文件是否生成成功
        "C1_signature_file_generated": sign_path.exists(),
        # C2：原文件 + 原签名验证
        "C2_original_file_verify": file_verify_result,
        # C3：篡改文件内容后再验证
        "C3_tampered_file_verify": verify_file_signature(
            alice_public,
            str(tampered_file_path),
            str(sign_path),
        ),
        # C4：篡改签名文件后再验证
        "C4_tampered_signature_verify": verify_file_signature(
            alice_public,
            str(file_path),
            str(tampered_sign_path),
        ),
    }

    # -------------------- 实验四：带元数据的数字签名 --------------------

    # 构造 Alice -> Bob 的元数据
    metadata = _make_metadata()
    # 对消息和元数据整体签名，生成签名数据包
    metadata_package = sign_with_metadata(alice_private, MESSAGE_M1, metadata)
    # 复制一份正常包，用于构造“修改时间戳”场景
    timestamp_tampered = copy_package(metadata_package)
    # 将时间戳修改为另一个值
    timestamp_tampered["metadata"]["timestamp"] = "2026-04-21T00:00:00+00:00"
    # 复制一份正常包，用于构造“修改算法标识”场景
    algorithm_tampered = copy_package(metadata_package)
    # 修改算法套件字段
    algorithm_tampered["metadata"]["algorithm_suite"] = "RSA-PKCS1v15+SHA256"
    # 复制一份正常包，用于构造“修改接收方 ID”场景
    receiver_tampered = copy_package(metadata_package)
    # 将 receiver_id 篡改为 Mallory
    receiver_tampered["metadata"]["receiver_id"] = "Mallory"
    # 保存实验四的结果
    results["experiment_4"] = {
        # D1：正常签名包验签
        "D1_normal": verify_metadata_signature(alice_public, metadata_package),
        # D2：修改时间戳后验签
        "D2_modify_timestamp": verify_metadata_signature(alice_public, timestamp_tampered),
        # D3：修改算法标识后验签
        "D3_modify_algorithm_suite": verify_metadata_signature(alice_public, algorithm_tampered),
        # D4：修改接收方 ID 后验签
        "D4_modify_receiver_id": verify_metadata_signature(alice_public, receiver_tampered),
        # 保存原始元数据，便于报告展示
        "metadata": metadata,
    }

    # -------------------- 实验五：先签名后加密 --------------------

    # 构造实验五用的元数据
    ste_metadata = _make_metadata()
    # 先签名再加密，生成安全消息包
    ste_package = sign_then_encrypt(alice_private, bob_public, MESSAGE_M1, ste_metadata)
    # E1：正常流程，Bob 解密后再验签
    ste_normal = decrypt_then_verify(bob_private, alice_public, ste_package)
    # E2：篡改密文后，Bob 再解密验签
    ste_cipher_tampered = decrypt_then_verify(
        bob_private,
        alice_public,
        tamper_package_b64_field(ste_package, "ciphertext_b64"),
    )
    # E2：篡改 GCM Tag 后，Bob 再解密验签
    ste_tag_tampered = decrypt_then_verify(
        bob_private,
        alice_public,
        tamper_package_b64_field(ste_package, "tag_b64"),
    )
    # 构造“内部签名被篡改，但外层重新加密”的测试包
    ste_signature_tampered_package = tamper_sign_then_encrypt_inner_signature(
        bob_private,
        bob_public,
        ste_package,
    )
    # E3：解密成功，但内部签名应当验证失败
    ste_signature_tampered = decrypt_then_verify(
        bob_private,
        alice_public,
        ste_signature_tampered_package,
    )
    # E4：使用错误私钥解密
    ste_wrong_private = decrypt_then_verify(wrong_private, alice_public, ste_package)
    # 保存实验五结果
    results["experiment_5"] = {
        # E1：正常流程结果
        "E1_normal": ste_normal,
        # E2：篡改密文结果
        "E2_tamper_ciphertext": ste_cipher_tampered,
        # E2：篡改 Tag 结果
        "E2_tamper_tag": ste_tag_tampered,
        # E3：篡改内部签名结果
        "E3_tamper_inner_signature": ste_signature_tampered,
        # E4：错误私钥解密结果
        "E4_wrong_private_key": ste_wrong_private,
        # 展示密文片段
        "ciphertext_preview": preview_bytes(b64decode(ste_package["ciphertext_b64"])),
        # 展示 Tag 片段
        "tag_preview": preview_bytes(b64decode(ste_package["tag_b64"])),
    }

    # -------------------- 实验六：先加密后签名 --------------------

    # 构造实验六用的元数据
    ets_metadata = _make_metadata()
    # 先加密再签名，生成外层带签名的密文包
    ets_package = encrypt_then_sign(alice_private, bob_public, MESSAGE_M1, ets_metadata)
    # F1：正常流程，先验签再解密
    ets_normal = verify_then_decrypt(bob_private, alice_public, ets_package)
    # F2：篡改密文后再执行先验签后解密
    ets_cipher_tampered = verify_then_decrypt(
        bob_private,
        alice_public,
        tamper_package_b64_field(ets_package, "ciphertext_b64"),
    )
    # F3：使用错误发送方公钥验签
    ets_wrong_public = verify_then_decrypt(bob_private, wrong_public, ets_package)
    # F4：使用错误接收方私钥解密
    ets_wrong_private = verify_then_decrypt(wrong_private, alice_public, ets_package)
    # 保存实验六结果
    results["experiment_6"] = {
        # F1：正常流程结果
        "F1_normal": ets_normal,
        # F2：篡改密文结果
        "F2_tamper_ciphertext": ets_cipher_tampered,
        # F3：错误发送方公钥结果
        "F3_wrong_sender_public_key": ets_wrong_public,
        # F4：错误接收方私钥结果
        "F4_wrong_receiver_private_key": ets_wrong_private,
        # 展示密文片段
        "ciphertext_preview": preview_bytes(b64decode(ets_package["ciphertext_b64"])),
        # 展示 Tag 片段
        "tag_preview": preview_bytes(b64decode(ets_package["tag_b64"])),
    }

    # -------------------- 实验七：数字信封 + 数字签名综合实验 --------------------

    # 构造数字信封安全包
    envelope = build_secure_envelope(
        alice_private,
        bob_public,
        MESSAGE_M1,
        "Alice",
        "Bob",
    )
    # 保存实验七结果
    results["experiment_7"] = {
        # G1：正常数字信封打开结果
        "G1_normal": open_secure_envelope(bob_private, alice_public, envelope),
        # G2：篡改密文后打开数字信封
        "G2_tamper_ciphertext": open_secure_envelope(
            bob_private,
            alice_public,
            tamper_secure_envelope(envelope, "ciphertext_b64"),
        ),
        # G3：篡改 Tag 后打开数字信封
        "G3_tamper_tag": open_secure_envelope(
            bob_private,
            alice_public,
            tamper_secure_envelope(envelope, "tag_b64"),
        ),
        # G4：修改算法标识后打开数字信封
        "G4_modify_algorithm_suite": open_secure_envelope(
            bob_private,
            alice_public,
            tamper_secure_envelope(envelope, "algorithm_suite"),
        ),
        # G5：修改接收方 ID 后打开数字信封
        "G5_modify_receiver_id": open_secure_envelope(
            bob_private,
            alice_public,
            tamper_secure_envelope(envelope, "receiver_id"),
        ),
        # G6：使用错误公钥验证数字信封
        "G6_wrong_public_key": open_secure_envelope(bob_private, wrong_public, envelope),
        # 保存部分展示信息，便于写实验报告
        "envelope_preview": {
            # 加密会话密钥片段
            "encrypted_key": preview_bytes(b64decode(envelope["encrypted_key_b64"])),
            # 密文片段
            "ciphertext": preview_bytes(b64decode(envelope["ciphertext_b64"])),
            # Tag 片段
            "tag": preview_bytes(b64decode(envelope["tag_b64"])),
            # 原始消息摘要
            "message_digest": hash_bytes(MESSAGE_M1).hex(),
            # 安全包创建时间
            "created_at": envelope["created_at"],
        },
    }

    # 记录全部实验完成时间
    results["generated_at"] = utc_timestamp()
    # 返回所有实验的结果字典
    return results


def print_result_summary(results: dict):
    """
    功能：按实验编号输出结果摘要。
    注意：只展示必要片段，不泄露私钥。
    """
    print("数字签名综合实验结果摘要")
    print("=" * 56)
    print("参与方：发送方 Alice（SK_A/PK_A），接收方 Bob（SK_B/PK_B）")
    print(f"PK_A 指纹：{results['participants']['alice_public_key_fingerprint']}")
    print(f"PK_B 指纹：{results['participants']['bob_public_key_fingerprint']}")
    print(f"M1：{results['messages']['M1']}")
    print(f"M1'：{results['messages']['M1_tampered']}")
    print(f"Mbin：长度={results['messages']['Mbin_length']}，末尾hex={results['messages']['Mbin_tail_hex']}")

    exp1 = results["experiment_1"]
    print("\n实验一：基础数字签名")
    print(f"Verify(PK_A, M1, Sig)  = {_yes_no(exp1['A1_correct_signature'])}")
    print(f"Verify(PK_A, M1', Sig) = {_yes_no(exp1['A2_tampered_message'])}")
    print(f"Verify(PK_B, M1, Sig)  = {_yes_no(exp1['A3_wrong_public_key'])}")
    print(f"Mbin bytes验签          = {_yes_no(exp1['Mbin_signature_valid'])}")
    print(f"签名片段：{exp1['signature_preview']}...，长度={exp1['signature_length']} bytes")

    exp2 = results["experiment_2"]
    tampered_hash = exp2["Hash(M1')"]
    print("\n实验二：摘要后签名与完整性检测")
    print(f"Hash(M1)  = {exp2['Hash(M1)']}")
    print(f"Hash(M1') = {tampered_hash}")
    print(f"摘要是否相同：{exp2['digest_same']}")
    print(f"B1 原始消息验签：{_yes_no(exp2['B1_original_message'])}")
    print(f"B2 篡改消息验签：{_yes_no(exp2['B2_tampered_message'])}")
    print(f"B3 摘要对比不同：{_yes_no(exp2['B3_digest_compare'])}")

    exp3 = results["experiment_3"]
    report = exp3["report"]
    print("\n实验三：文件分离式数字签名")
    print(f"文件：{report['file_path']}，大小={report['file_size']} bytes")
    print(f"签名文件：{report['sign_path']}，大小={report['sign_file_size']} bytes")
    print(f"文件摘要片段：{report['digest_preview']}...")
    print(f"C1 签名文件生成：{_ok_fail(exp3['C1_signature_file_generated'])}")
    print(f"C2 原文件+签名验证：{_yes_no(exp3['C2_original_file_verify'])}")
    print(f"C3 文件内容篡改：{_yes_no(exp3['C3_tampered_file_verify'])}")
    print(f"C4 签名文件篡改：{_yes_no(exp3['C4_tampered_signature_verify'])}")

    exp4 = results["experiment_4"]
    print("\n实验四：带元数据的数字签名")
    print(f"D1 正常签名：{_yes_no(exp4['D1_normal'])}")
    print(f"D2 修改时间戳：{_yes_no(exp4['D2_modify_timestamp'])}")
    print(f"D3 修改算法标识：{_yes_no(exp4['D3_modify_algorithm_suite'])}")
    print(f"D4 修改接收方ID：{_yes_no(exp4['D4_modify_receiver_id'])}")

    exp5 = results["experiment_5"]
    print("\n实验五：先签名后加密")
    print(f"E1 正常流程：解密={_ok_fail(exp5['E1_normal']['decrypt_success'])}，验签={_yes_no(exp5['E1_normal']['verify_success'])}")
    print(f"E2 篡改密文：解密={_ok_fail(exp5['E2_tamper_ciphertext']['decrypt_success'])}，验签={_yes_no(exp5['E2_tamper_ciphertext']['verify_success'])}")
    print(f"E2 篡改Tag：解密={_ok_fail(exp5['E2_tamper_tag']['decrypt_success'])}，验签={_yes_no(exp5['E2_tamper_tag']['verify_success'])}")
    print(f"E3 篡改内部签名：解密={_ok_fail(exp5['E3_tamper_inner_signature']['decrypt_success'])}，验签={_yes_no(exp5['E3_tamper_inner_signature']['verify_success'])}")
    print(f"E4 错误私钥解密：解密={_ok_fail(exp5['E4_wrong_private_key']['decrypt_success'])}，验签={_yes_no(exp5['E4_wrong_private_key']['verify_success'])}")

    exp6 = results["experiment_6"]
    print("\n实验六：先加密后签名")
    print(f"F1 正常流程：验签={_yes_no(exp6['F1_normal']['verify_success'])}，解密={_ok_fail(exp6['F1_normal']['decrypt_success'])}")
    print(f"F2 篡改密文：验签={_yes_no(exp6['F2_tamper_ciphertext']['verify_success'])}，解密={_ok_fail(exp6['F2_tamper_ciphertext']['decrypt_success'])}")
    print(f"F3 错误公钥：验签={_yes_no(exp6['F3_wrong_sender_public_key']['verify_success'])}，解密={_ok_fail(exp6['F3_wrong_sender_public_key']['decrypt_success'])}")
    print(f"F4 错误私钥解密：验签={_yes_no(exp6['F4_wrong_receiver_private_key']['verify_success'])}，解密={_ok_fail(exp6['F4_wrong_receiver_private_key']['decrypt_success'])}")

    exp7 = results["experiment_7"]
    print("\n实验七：数字信封 + 数字签名综合")
    for label, key in [
        ("G1 正常包", "G1_normal"),
        ("G2 篡改密文", "G2_tamper_ciphertext"),
        ("G3 篡改Tag", "G3_tamper_tag"),
        ("G4 修改算法标识", "G4_modify_algorithm_suite"),
        ("G5 修改接收方ID", "G5_modify_receiver_id"),
        ("G6 错误公钥", "G6_wrong_public_key"),
    ]:
        item = exp7[key]
        print(
            f"{label}：验签={_yes_no(item['signature_valid'])}，"
            f"解密={_ok_fail(item['decrypt_success'])}，完整性={_yes_no(item['integrity_valid'])}"
        )
    print(f"信封密文片段：{exp7['envelope_preview']['ciphertext']}...")
    print("=" * 56)


if __name__ == "__main__":
    print_result_summary(run_all_experiments())
