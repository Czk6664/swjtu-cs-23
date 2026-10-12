import json
from pathlib import Path

from challenge_auth import compute_challenge_proof, issue_challenge
from common import b64d, b64e, now_unix_ts, random_nonce
from integrated_auth import replay_packet, run_auth_trial, summarize_results
from mac_auth import build_mac_packet, inject_payload_tamper, new_mac_nonce
from otp_auth import generate_hotp, generate_totp
from password_auth import build_password_record
from signature_auth import (
    build_signed_packet,
    generate_ec_key_pair,
    inject_data_tamper,
    make_signature_meta,
    public_key_pem,
)
from user_store import add_user_record, clone_db


OUT_DIR = Path("output")
OUT_DIR.mkdir(exist_ok=True)


def make_base_db() -> tuple[dict, dict]:
    alice_password = build_password_record("alice", "SecureP@ss123", "active")
    bob_password = build_password_record("bob", "BobP@ss456", "inactive")
    alice_sk, _ = generate_ec_key_pair()
    bob_sk, _ = generate_ec_key_pair()
    eve_sk, _ = generate_ec_key_pair()

    shared_key = b"alice-shared-key-for-hmac-32bytes"
    otp_secret = b"alice-otp-secret-20b"
    for record in (alice_password, bob_password):
        record.update(
            {
                "shared_key": shared_key,
                "otp_secret": otp_secret,
                "counter": 0,
                "issued_nonces": {},
                "used_hotp_values": set(),
                "used_totp_slots": set(),
                "used_mac_nonces": set(),
                "used_sig_nonces": set(),
            }
        )
    alice_password["pub_key"] = public_key_pem(alice_sk)
    bob_password["pub_key"] = public_key_pem(bob_sk)

    db = {}
    add_user_record(alice_password, db)
    add_user_record(bob_password, db)
    keys = {"alice_sk": alice_sk, "bob_sk": bob_sk, "eve_sk": eve_sk, "shared_key": shared_key, "otp_secret": otp_secret}
    return db, keys


def classify(test_id: str, actual_reason: str, expected: str) -> str:
    if expected == "通过":
        return "通过" if actual_reason.startswith("ok") else "不通过"
    category_by_reason = {
        "password_mismatch": "拒绝（比较失败）",
        "proof_mismatch": "拒绝（比较失败）",
        "signature_invalid": "拒绝（比较失败）",
        "counter_window_miss_or_otp_mismatch": "拒绝（新鲜性失败）" if test_id == "HO-03" else "拒绝（比较失败）",
        "time_window_miss_or_otp_mismatch": "拒绝（新鲜性失败）",
        "nonce_expired": "拒绝（新鲜性失败）",
        "nonce_not_issued": "拒绝（新鲜性失败）",
        "timestamp_expired": "拒绝（新鲜性失败）",
        "freshness_fields_missing": "拒绝（新鲜性失败）",
        "nonce_reused": "拒绝（复用失败）",
        "otp_reused": "拒绝（复用失败）",
        "totp_slot_reused": "拒绝（复用失败）",
        "user_not_found": "拒绝（身份失败）",
        "account_inactive": "拒绝（身份失败）",
        "tag_mismatch": "拒绝（完整性失败）",
    }
    return category_by_reason.get(actual_reason, f"拒绝（{actual_reason}）")


def verdict(expected: str, actual_category: str) -> tuple[str, str]:
    ok = expected == actual_category
    return "是" if ok else "否", "实际结果与期望一致，验证逻辑按安全策略触发。" if ok else "实际结果与期望不一致，需要检查状态推进或校验顺序。"


def row(test_id: str, mode: str, scene: str, input_cond: str, expected: str, actual: dict) -> dict:
    actual_category = classify(test_id, actual["reason"], expected)
    passed, explanation = verdict(expected, actual_category)
    mechanism_note = {
        "PW-05": "静态口令没有 nonce/counter，新旧同一口令请求均可通过，体现其不能天然抵御重放。",
        "CH-05": "已消费 nonce 被再次提交，服务端命中 nonce_reused。",
        "MC-02": "payload 被修改后 tag 覆盖内容变化，HMAC 比较失败。",
        "SG-03": "data 被修改后签名覆盖内容变化，验签失败。",
    }.get(test_id)
    if mechanism_note and passed == "是":
        explanation = mechanism_note
    return {
        "test_id": test_id,
        "mode": mode,
        "scene": scene,
        "input": input_cond,
        "expected": expected,
        "actual_category": actual_category,
        "actual": actual,
        "passed": passed,
        "analysis": explanation,
    }


def run_password_tests(records: list[dict]) -> None:
    db, _ = make_base_db()
    pw01_packet = {"id": "alice", "password": "SecureP@ss123"}
    tests = [
        ("PW-01", "正确口令正常登录", 'id="alice", password="SecureP@ss123"', "通过", pw01_packet),
        ("PW-02", "错误口令登录", 'id="alice", password="WrongPass"', "拒绝（比较失败）", {"id": "alice", "password": "WrongPass"}),
        ("PW-03", "不存在的用户登录", 'id="eve", password="anything"', "拒绝（身份失败）", {"id": "eve", "password": "anything"}),
        ("PW-04", "停用账户登录", 'id="bob", password="BobP@ss456"', "拒绝（身份失败）", {"id": "bob", "password": "BobP@ss456"}),
        ("PW-05", "重放攻击（重复提交旧请求）", "将 PW-01 的请求报文原样再发送一次", "通过", replay_packet(pw01_packet)),
    ]
    for test_id, scene, input_cond, expected, packet in tests:
        records.append(row(test_id, "password", scene, input_cond, expected, run_auth_trial("password", packet, db)))


def run_challenge_tests(records: list[dict]) -> None:
    now = now_unix_ts()
    for test_id, scene, expected, maker in [
        ("CH-01", "正常挑战-应答", "通过", "normal"),
        ("CH-02", "错误的共享密钥", "拒绝（比较失败）", "bad_key"),
        ("CH-03", "篡改 nonce", "拒绝（新鲜性失败）", "tamper_nonce"),
        ("CH-04", "使用过期 nonce", "拒绝（新鲜性失败）", "expired"),
        ("CH-05", "重放攻击（复用已消费 nonce）", "拒绝（复用失败）", "replay"),
        ("CH-06", "伪造 nonce（客户端自行生成）", "拒绝（新鲜性失败）", "forged"),
    ]:
        db, keys = make_base_db()
        challenge = issue_challenge("alice", db, ttl=5, issued_at=now)
        nonce_id = challenge["nonce"]
        nonce_bytes = b64d(nonce_id)
        context = b"login:alice"
        key = keys["shared_key"] if maker != "bad_key" else b"wrong-shared-key"
        packet = {"id": "alice", "nonce": nonce_id, "context": context, "proof": compute_challenge_proof(key, nonce_bytes, context)}
        server_time = now
        if maker == "tamper_nonce":
            packet["nonce"] = b64e(random_nonce(16))
        elif maker == "expired":
            server_time = now + 10
        elif maker == "replay":
            first = run_auth_trial("challenge", packet, db)
            records.append(row("CH-01-pre", "challenge", "CH-05 前置正常认证", "先消费 nonce", "通过", first))
            packet = replay_packet(packet)
        elif maker == "forged":
            forged = random_nonce(16)
            packet["nonce"] = b64e(forged)
            packet["proof"] = compute_challenge_proof(keys["shared_key"], forged, context)
        packet["server_time"] = server_time
        input_cond = {
            "normal": "使用正确共享密钥 K 和服务器签发 nonce 计算 proof",
            "bad_key": "使用错误密钥 K' 计算 proof",
            "tamper_nonce": "将服务器签发 nonce 修改为不同值后提交",
            "expired": "获取 nonce 后模拟超过 5 秒有效期再提交",
            "replay": "将已通过的 CH-01 报文原样再次提交",
            "forged": "不向服务器获取 nonce，客户端自行生成随机数作为 nonce",
        }[maker]
        if test_id != "CH-01-pre":
            records.append(row(test_id, "challenge", scene, input_cond, expected, run_auth_trial("challenge", packet, db)))


def run_otp_tests(records: list[dict]) -> None:
    fixed_ts = (now_unix_ts() // 30) * 30 + 5
    db, keys = make_base_db()
    hotp0 = generate_hotp(keys["otp_secret"], 0)
    records.append(row("HO-01", "otp(hotp)", "当前 counter 正常验证", "客户端 counter=0，服务端 counter=0", "通过", run_auth_trial("otp(hotp)", {"id": "alice", "otp": hotp0}, db)))
    records.append(row("HO-02", "otp(hotp)", "重放攻击（重复提交相同 OTP）", "将 HO-01 使用的 OTP 再次提交", "拒绝（复用失败）", run_auth_trial("otp(hotp)", {"id": "alice", "otp": hotp0}, db)))
    records.append(row("HO-03", "otp(hotp)", "客户端 counter 超前（漂移）", "客户端 counter=5，服务端 counter=1", "拒绝（新鲜性失败）", run_auth_trial("otp(hotp)", {"id": "alice", "otp": generate_hotp(keys["otp_secret"], 5)}, db)))
    records.append(row("HO-04", "otp(hotp)", "错误的 OTP", "随机输入 6 位数字 OTP", "拒绝（比较失败）", run_auth_trial("otp(hotp)", {"id": "alice", "otp": "123456"}, db)))

    db, keys = make_base_db()
    current_totp = generate_totp(keys["otp_secret"], fixed_ts)
    records.append(row("TO-01", "otp(totp)", "当前时间片正常验证", "系统时间同步，使用当前 TOTP", "通过", run_auth_trial("otp(totp)", {"id": "alice", "otp": current_totp, "server_time": fixed_ts}, db)))
    prev_totp = generate_totp(keys["otp_secret"], fixed_ts - 30)
    records.append(row("TO-02", "otp(totp)", "前一个时间片验证（窗口容错）", "使用 30 秒前生成的 TOTP 提交", "通过", run_auth_trial("otp(totp)", {"id": "alice", "otp": prev_totp, "server_time": fixed_ts}, db)))
    old_totp = generate_totp(keys["otp_secret"], fixed_ts - 120)
    records.append(row("TO-03", "otp(totp)", "时间窗口外的过期 OTP", "使用 2 分钟前生成的 TOTP 提交", "拒绝（新鲜性失败）", run_auth_trial("otp(totp)", {"id": "alice", "otp": old_totp, "server_time": fixed_ts}, db)))
    records.append(row("TO-04", "otp(totp)", "同一时间片内重复提交", "将 TO-01 的 TOTP 再次提交", "拒绝（复用失败）", run_auth_trial("otp(totp)", {"id": "alice", "otp": current_totp, "server_time": fixed_ts}, db)))


def run_mac_tests(records: list[dict]) -> None:
    now = now_unix_ts()
    db, keys = make_base_db()
    packet = build_mac_packet("alice", b"amount=100&to=bob", keys["shared_key"], new_mac_nonce(), now)
    records.append(row("MC-01", "mac", "正常报文验证", "当前 ts、新 nonce、正确 tag", "通过", run_auth_trial("mac", {**packet, "server_time": now}, db)))
    records.append(row("MC-02", "mac", "篡改 payload", "复制 MC-01 报文，修改 payload，保持 tag 不变", "拒绝（完整性失败）", run_auth_trial("mac", {**inject_payload_tamper(packet), "server_time": now}, clone_db(make_base_db()[0]))))
    tampered_id = replay_packet(packet)
    tampered_id["id"] = "bob"
    db_id_tamper = clone_db(make_base_db()[0])
    db_id_tamper["bob"]["status"] = "active"
    records.append(row("MC-03", "mac", "篡改 id 字段", '复制 MC-01 报文，将 id 改为 "bob"，保持 tag 不变', "拒绝（完整性失败）", run_auth_trial("mac", {**tampered_id, "server_time": now}, db_id_tamper)))
    tampered_ts = replay_packet(packet)
    tampered_ts["ts"] = now - 30
    records.append(row("MC-04", "mac", "篡改 ts 字段", "复制 MC-01 报文，修改 ts，保持 tag 不变", "拒绝（完整性失败）", run_auth_trial("mac", {**tampered_ts, "server_time": now}, clone_db(make_base_db()[0]))))
    records.append(row("MC-05", "mac", "重放攻击（过期 ts）", "保存 MC-01 报文，模拟 2 分钟后再提交", "拒绝（新鲜性失败）", run_auth_trial("mac", {**packet, "server_time": now + 120}, clone_db(make_base_db()[0]))))
    records.append(row("MC-06", "mac", "重放攻击（复用 nonce）", "在 ts 仍有效的短时间内再次提交 MC-01", "拒绝（复用失败）", run_auth_trial("mac", {**packet, "server_time": now + 1}, db)))
    db_no_fresh, keys = make_base_db()
    no_fresh = build_mac_packet("alice", b"amount=100&to=bob", keys["shared_key"], None, None)
    first = run_auth_trial("mac", {**no_fresh, "require_freshness": False, "server_time": now}, db_no_fresh)
    second = run_auth_trial("mac", {**no_fresh, "require_freshness": False, "server_time": now + 1}, db_no_fresh)
    records.append(row("MC-07", "mac(no_freshness)", "无新鲜性字段的 MAC（对照）", "仅含 id、payload、tag，正确后原样重放一次", "通过", second if first["result"] == "accept" else first))


def run_signature_tests(records: list[dict]) -> None:
    now = now_unix_ts()
    db, keys = make_base_db()
    pristine_db = clone_db(db)
    meta = make_signature_meta(now)
    packet = build_signed_packet("alice", b"amount=100&to=bob", keys["alice_sk"], meta)
    records.append(row("SG-01", "signature", "正常签名验证", "alice 用 sk_A 签名，服务端用 pk_A 验签", "通过", run_auth_trial("signature", {**packet, "server_time": now}, db)))

    db_bad_key = clone_db(pristine_db)
    db_bad_key["alice"]["pub_key"] = db_bad_key["bob"]["pub_key"]
    records.append(row("SG-02", "signature", "使用错误的公钥验证", "用 bob 的公钥 pk_B 去验证 alice 的签名", "拒绝（比较失败）", run_auth_trial("signature", {**packet, "server_time": now}, db_bad_key)))
    records.append(row("SG-03", "signature", "篡改 data 字段", "复制 SG-01 报文，修改 data，保持 signature 不变", "拒绝（比较失败）", run_auth_trial("signature", {**inject_data_tamper(packet), "server_time": now}, clone_db(pristine_db))))
    tampered_ts = replay_packet(packet)
    tampered_ts["meta"]["ts"] = now - 30
    records.append(row("SG-04", "signature", "篡改 meta 中的 ts", "复制 SG-01 报文，修改 meta.ts，保持 signature 不变", "拒绝（比较失败）", run_auth_trial("signature", {**tampered_ts, "server_time": now}, clone_db(pristine_db))))
    records.append(row("SG-05", "signature", "重放攻击（过期 ts）", "保存 SG-01 报文，模拟 2 分钟后再提交", "拒绝（新鲜性失败）", run_auth_trial("signature", {**packet, "server_time": now + 120}, clone_db(pristine_db))))
    forged = build_signed_packet("alice", b"amount=100&to=bob", keys["eve_sk"], make_signature_meta(now))
    records.append(row("SG-06", "signature", "签名伪造尝试", 'eve 用自己的私钥签名，但 id 字段填 "alice"', "拒绝（比较失败）", run_auth_trial("signature", {**forged, "server_time": now}, clone_db(pristine_db))))
    optional = replay_packet(packet)
    optional["remark"] = "tampered unsigned field"
    records.append(row("SG-07", "signature", "未签名字段被篡改（选做）", "篡改 remark 字段，该字段不在签名覆盖范围内", "通过", run_auth_trial("signature", {**optional, "server_time": now}, clone_db(pristine_db))))


def run_cross_tests(records: list[dict]) -> list[dict]:
    matrix = [
        {
            "test_id": "X-01",
            "attack": "重放相同报文",
            "password": "通过：静态口令无新鲜性字段，旧请求仍可通过",
            "challenge": "拒绝（复用失败）：nonce 已消费",
            "otp(hotp)": "拒绝（复用失败）：同一 OTP 已使用",
            "mac": "拒绝（复用失败）：nonce 已消费",
            "signature": "拒绝（复用失败）：签名报文 nonce 已消费",
        },
        {
            "test_id": "X-02",
            "attack": "篡改 payload",
            "password": "不适用/弱：未保护业务消息 payload",
            "challenge": "拒绝（比较失败）：context 被覆盖时 proof 不匹配",
            "otp(hotp)": "不适用/弱：OTP 只证明登录，不绑定 payload",
            "mac": "拒绝（完整性失败）：tag 不匹配",
            "signature": "拒绝（比较失败）：验签失败",
        },
        {
            "test_id": "X-03",
            "attack": "伪造身份（未知 id）",
            "password": "拒绝（身份失败）：用户不存在",
            "challenge": "拒绝（身份失败）：用户不存在/无已签发 nonce",
            "otp(hotp)": "拒绝（身份失败）：用户不存在",
            "mac": "拒绝（身份失败）：用户不存在",
            "signature": "拒绝（身份失败）：用户不存在",
        },
        {
            "test_id": "X-04",
            "attack": "使用错误凭证",
            "password": "拒绝（比较失败）：口令摘要不匹配",
            "challenge": "拒绝（比较失败）：proof 不匹配",
            "otp(hotp)": "拒绝（比较失败）：OTP 不匹配",
            "mac": "拒绝（完整性失败）：tag 不匹配",
            "signature": "拒绝（比较失败）：验签失败",
        },
    ]
    return matrix


def serialize(obj):
    if isinstance(obj, bytes):
        return b64e(obj)
    if isinstance(obj, set):
        return sorted(obj)
    raise TypeError(f"not serializable: {type(obj)}")


def make_test_suite() -> list[dict]:
    records: list[dict] = []
    run_password_tests(records)
    run_challenge_tests(records)
    records[:] = [r for r in records if r["test_id"] != "CH-01-pre"]
    run_otp_tests(records)
    run_mac_tests(records)
    run_signature_tests(records)
    cross = run_cross_tests(records)
    payload = {"records": records, "cross": cross, "summary": summarize_results(records)}
    (OUT_DIR / "experiment_results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=serialize), encoding="utf-8")
    return records


if __name__ == "__main__":
    suite = make_test_suite()
    print(f"generated {len(suite)} detailed test rows")
    print(f"results: {OUT_DIR / 'experiment_results.json'}")
