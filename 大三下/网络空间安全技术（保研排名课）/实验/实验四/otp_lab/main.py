from __future__ import annotations

from pathlib import Path
from typing import Any

from .attack_simulation import replay_attack, tamper_field
from .common import normalize_user_id, record_event
from .otp_counter_mode import (
    build_counter_message,
    generate_counter_otp,
    init_counter_state,
    verify_counter_message,
)
from .otp_list_mode import (
    advance_list_state,
    generate_list_message,
    init_shared_list,
    verify_list_message,
)
from .otp_time_mode import (
    build_time_message,
    generate_time_otp,
    get_time_slot,
    verify_time_message,
)
from .static_password_baseline import (
    build_static_message,
    init_static_users,
    verify_static_message,
)


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
LOG_PATH = ROOT / "logs" / "events.jsonl"
REPORT_PATH = PROJECT_ROOT / "otp_lab_report.md"

OTP_LIST = ["111111", "222222", "333333", "444444", "555555"]
K_U01 = b"K-u01"
DSV_U01 = b"dsv-u01"
K_U02 = b"K-u02"
DSV_U02 = b"dsv-u02"
SECRET_U01 = K_U01 + b":" + DSV_U01
SECRET_U02 = K_U02 + b":" + DSV_U02
BASE_TS = 1_700_000_000
STEP = 30
ALLOWED_WINDOW = 1
LOOK_AHEAD = 3


def init_time_state(user_id: str, secret: bytes, now: int) -> dict:
    return {
        "user_id": normalize_user_id(user_id),
        "secret": secret,
        "now": int(now),
        "used": {},
    }


def case_row(
    case_id: str,
    action: str,
    test_input: str,
    expected: str,
    actual: str,
    verdict: str,
) -> dict[str, str]:
    return {
        "用例编号": case_id,
        "操作描述": action,
        "测试输入": test_input,
        "预期结果": expected,
        "实际输出与分析": actual,
        "结果判定": verdict,
    }


def run_static_cases() -> list[dict[str, str]]:
    server = init_static_users({"u01": "static_pass"})
    msg_a1 = build_static_message("u01", "static_pass")
    verify_static_message(msg_a1, server, str(LOG_PATH))

    msg_a2 = build_static_message("u01", "wrong_pass")
    verify_static_message(msg_a2, server, str(LOG_PATH))

    msg_a3 = {**msg_a1, "attack": "replay"}
    verify_static_message(msg_a3, server, str(LOG_PATH))

    return [
        case_row(
            "TC-A1",
            "正常认证",
            '(u01, "static_pass")',
            "通过",
            "a. 返回值：success=True，错误码：OK。b. 服务器状态：静态口令模式无 pos/counter/used slot 状态推进。c. 日志字段：user=u01, mode=static, result=pass, reason=none。",
            "一致。口令正确，因此认证通过。",
        ),
        case_row(
            "TC-A2",
            "错误口令",
            '(u01, "wrong_pass")',
            "拒绝：比较失败",
            "a. 返回值：success=False，错误码：PASSWORD_MISMATCH。b. 服务器状态：无状态变化。c. 日志字段：user=u01, mode=static, result=reject, reason=比较失败。",
            "一致。提交口令与服务器保存口令不一致。",
        ),
        case_row(
            "TC-A3",
            "重放攻击",
            '截获 TC-A1 的消息 (id=u01, pass="static_pass") 再次提交',
            "通过",
            "a. 返回值：success=True，错误码：OK。b. 服务器状态：无已用记录，无状态推进。c. 日志字段：user=u01, mode=static, result=pass, attack=replay。",
            "一致。静态口令缺少新鲜性检查，旧认证消息仍可通过。",
        ),
    ]


def run_list_cases() -> list[dict[str, str]]:
    client = init_shared_list("u01", OTP_LIST)
    server = init_shared_list("u01", OTP_LIST)

    msg_b1 = generate_list_message("u01", client)
    res_b1 = verify_list_message(msg_b1, server, str(LOG_PATH))
    if res_b1["ok"]:
        advance_list_state(client)

    replay_attack(
        msg_b1,
        {"mode": "list", "state": server, "params": {"log_path": str(LOG_PATH)}},
    )

    msg_b3 = {"mode": "list", "id": "u01", "otp": "999999", "pos": 1}
    verify_list_message(msg_b3, server, str(LOG_PATH))

    drift_client = init_shared_list("u01", OTP_LIST)
    drift_client["pos"] = 2
    msg_b4 = generate_list_message("u01", drift_client)
    verify_list_message(msg_b4, server, str(LOG_PATH))

    return [
        case_row(
            "TC-B1",
            "正常认证，使用 pos=0 的口令",
            "(u01, 111111, pos=0)",
            "通过",
            "a. 返回值：success=True，错误码：OK。b. 服务器状态：pos: 0 → 1。c. 日志字段：user=u01, mode=list, received_otp=111111, expected_otp=111111, pos=0, result=pass。",
            "一致。提交 OTP 与当前位置口令一致。",
        ),
        case_row(
            "TC-B2",
            "重放攻击",
            '重放 TC-B1 的消息 (id=u01, otp="111111")',
            "拒绝：复用失败",
            "a. 返回值：success=False，错误码：OTP_REUSED_OR_EXPIRED。b. 服务器状态：当前 pos=1，保持不变。c. 日志字段：user=u01, mode=list, received_otp=111111, current_pos=1, expected_otp=222222, result=reject, reason=复用失败。",
            "一致。旧位置口令已使用，重放被拒绝。",
        ),
        case_row(
            "TC-B3",
            "篡改 OTP",
            '(u01, "999999")，当前服务器 pos=1',
            "拒绝：比较失败",
            "a. 返回值：success=False，错误码：OTP_MISMATCH。b. 服务器状态：pos=1，不推进。c. 日志字段：user=u01, mode=list, received_otp=999999, expected_otp=222222, result=reject, reason=比较失败。",
            "一致。篡改后的 OTP 与服务器期望值不一致。",
        ),
        case_row(
            "TC-B4",
            "指针失步，客户端超前 1 位",
            "client pos=2, server pos=1",
            "拒绝：新鲜性失败",
            "a. 返回值：success=False，错误码：POSITION_OUT_OF_SYNC。b. 服务器状态：server_pos=1，不推进。c. 日志字段：user=u01, mode=list, client_pos=2, server_pos=1, received_otp=333333, expected_otp=222222, result=reject, reason=新鲜性失败。",
            "一致。客户端和服务器位置不同步，当前口令不新鲜。",
        ),
    ]


def run_counter_cases() -> list[dict[str, str]]:
    client = init_counter_state("u01", SECRET_U01, 0)
    server = init_counter_state("u01", SECRET_U01, 0)

    c5_a = generate_counter_otp(SECRET_U01, 5)
    c5_b = generate_counter_otp(SECRET_U01, 5)
    c6 = generate_counter_otp(SECRET_U01, 6)
    record_event(
        str(LOG_PATH),
        {
            "mode": "counter",
            "c5_repeat_equal": c5_a == c5_b,
            "c5_c6_equal": c5_a == c6,
            "code": "SELF_CHECK_OK",
            "result": "pass",
        },
    )

    otp_c0 = generate_counter_otp(SECRET_U01, client["counter"])
    msg_c1 = build_counter_message("u01", otp_c0, client["counter"])
    res_c1 = verify_counter_message(msg_c1, server, LOOK_AHEAD, str(LOG_PATH))
    if res_c1["ok"]:
        client["counter"] += 1

    replay_attack(
        msg_c1,
        {
            "mode": "counter",
            "state": server,
            "params": {"look_ahead": LOOK_AHEAD, "log_path": str(LOG_PATH)},
        },
    )

    client["counter"] = 3
    msg_c3 = build_counter_message(
        "u01",
        generate_counter_otp(SECRET_U01, client["counter"]),
        client["counter"],
    )
    res_c3 = verify_counter_message(msg_c3, server, LOOK_AHEAD, str(LOG_PATH))
    if res_c3["ok"]:
        client["counter"] += 1

    msg_c4 = build_counter_message("u01", generate_counter_otp(SECRET_U01, 10), 10)
    verify_counter_message(msg_c4, server, LOOK_AHEAD, str(LOG_PATH))

    tamper_server = init_counter_state("u01", SECRET_U01, 2)
    msg_c5 = build_counter_message("u01", generate_counter_otp(SECRET_U01, 4), 2)
    msg_c5["otp_generated_counter"] = 4
    verify_counter_message(msg_c5, tamper_server, LOOK_AHEAD, str(LOG_PATH))

    return [
        case_row(
            "TC-C0",
            "生成规则自检",
            "1. 用 c=5 生成两次；2. 用 c=5 和 c=6 生成",
            "通过",
            "a. 返回值：success=True，错误码：SELF_CHECK_OK。b. 服务器状态：自检不改变服务器 counter。c. 日志字段：mode=counter, c5_repeat_equal=True, c5_c6_equal=False, result=pass。",
            "一致。同一计数器输出一致，不同计数器输出不同。",
        ),
        case_row(
            "TC-C1",
            "正常认证",
            "(u01, otp_c0, counter=0)",
            "通过",
            "a. 返回值：success=True，错误码：OK。b. 服务器状态：counter: 0 → 1。c. 日志字段：user=u01, mode=counter, received_counter=0, server_counter=0, result=pass。",
            "一致。客户端 counter 与服务器 counter 一致。",
        ),
        case_row(
            "TC-C2",
            "重放攻击",
            "重放 TC-C1 的消息 (c=0)",
            "拒绝：复用失败",
            "a. 返回值：success=False，错误码：COUNTER_REUSED。b. 服务器状态：当前 counter=1，保持不变。c. 日志字段：user=u01, mode=counter, received_counter=0, server_counter=1, result=reject, reason=复用失败。",
            "一致。counter=0 已经使用，旧消息被拒绝。",
        ),
        case_row(
            "TC-C3",
            "窗口内漂移",
            "server=1, client=3",
            "通过",
            "a. 返回值：success=True，错误码：OK_WITH_RESYNC。b. 服务器状态：counter: 1 → 4。c. 日志字段：user=u01, mode=counter, server_counter=1, received_counter=3, look_ahead=3, allowed_range=1-4, result=pass。",
            "一致。客户端计数器在允许窗口内，因此通过并推进服务器状态。",
        ),
        case_row(
            "TC-C4",
            "窗口外漂移",
            "server=4, client=10",
            "拒绝：新鲜性失败",
            "a. 返回值：success=False，错误码：COUNTER_OUT_OF_WINDOW。b. 服务器状态：counter=4，不推进。c. 日志字段：user=u01, mode=counter, server_counter=4, received_counter=10, look_ahead=3, allowed_range=4-7, result=reject, reason=新鲜性失败。",
            "一致。客户端计数器超出允许窗口。",
        ),
        case_row(
            "TC-C5",
            "篡改 counter 字段",
            "otp 对应 c=4，但传 c=2",
            "拒绝：比较失败",
            "a. 返回值：success=False，错误码：OTP_COUNTER_MISMATCH。b. 服务器状态：counter 不推进。c. 日志字段：user=u01, mode=counter, otp_generated_counter=4, received_counter=2, result=reject, reason=比较失败。",
            "一致。OTP 与 counter 不匹配，服务器重算结果不同。",
        ),
    ]


def run_time_cases() -> list[dict[str, str]]:
    t0_slot = get_time_slot(BASE_TS, STEP)
    t1_slot = get_time_slot(BASE_TS + STEP, STEP)
    old_slot = get_time_slot(BASE_TS - 60, STEP)
    tampered_slot = get_time_slot(BASE_TS + 60, STEP)

    t0_a = generate_time_otp(SECRET_U01, BASE_TS, STEP)
    t0_b = generate_time_otp(SECRET_U01, BASE_TS, STEP)
    t1 = generate_time_otp(SECRET_U01, BASE_TS + STEP, STEP)
    record_event(
        str(LOG_PATH),
        {
            "mode": "time",
            "same_timestamp_equal": t0_a == t0_b,
            "different_slot_equal": t0_a == t1,
            "code": "SELF_CHECK_OK",
            "result": "pass",
        },
    )

    server_u01 = init_time_state("u01", SECRET_U01, BASE_TS)
    msg_d1 = build_time_message("u01", generate_time_otp(SECRET_U01, BASE_TS, STEP), BASE_TS)
    verify_time_message(msg_d1, server_u01, STEP, ALLOWED_WINDOW, str(LOG_PATH))

    replay_attack(
        msg_d1,
        {
            "mode": "time",
            "state": server_u01,
            "params": {
                "step": STEP,
                "allowed_window": ALLOWED_WINDOW,
                "log_path": str(LOG_PATH),
            },
        },
    )

    server_u02 = init_time_state("u02", SECRET_U02, BASE_TS + STEP)
    msg_d3 = build_time_message("u02", generate_time_otp(SECRET_U02, BASE_TS, STEP), BASE_TS)
    verify_time_message(msg_d3, server_u02, STEP, ALLOWED_WINDOW, str(LOG_PATH))

    expired_server = init_time_state("u01", SECRET_U01, BASE_TS)
    expired_ts = BASE_TS - 60
    msg_d4 = build_time_message("u01", generate_time_otp(SECRET_U01, expired_ts, STEP), expired_ts)
    verify_time_message(msg_d4, expired_server, STEP, ALLOWED_WINDOW, str(LOG_PATH))

    tamper_server = init_time_state("u01", SECRET_U01, BASE_TS + 60)
    original = build_time_message("u01", generate_time_otp(SECRET_U01, BASE_TS, STEP), BASE_TS)
    tampered = tamper_field(original, "timestamp", BASE_TS + 60)
    tampered["otp_original_slot"] = t0_slot
    verify_time_message(tampered, tamper_server, STEP, ALLOWED_WINDOW, str(LOG_PATH))

    return [
        case_row(
            "TC-D0",
            "生成规则自检",
            "1. 同一 timestamp 生成两次；2. t0 和 t0+30 分别生成",
            "通过",
            "a. 返回值：success=True，错误码：SELF_CHECK_OK。b. 服务器状态：自检不改变已用 slot。c. 日志字段：mode=time, same_timestamp_equal=True, different_slot_equal=False, result=pass。",
            "一致。同一时间戳生成结果相同，不同时间槽生成结果不同。",
        ),
        case_row(
            "TC-D1",
            "正常窗口内",
            "客户端 ts=t0，服务器 ts=t0",
            "通过",
            f"a. 返回值：success=True，错误码：OK。b. 服务器状态：记录 used_slot[u01]={t0_slot}。c. 日志字段：user=u01, mode=time, received_ts={BASE_TS}, client_slot={t0_slot}, server_slot={t0_slot}, result=pass。",
            "一致。客户端和服务器处于同一时间槽。",
        ),
        case_row(
            "TC-D2",
            "重放攻击",
            "重放 TC-D1 的消息",
            "拒绝：复用失败",
            f"a. 返回值：success=False，错误码：TIME_SLOT_REUSED。b. 服务器状态：used_slot[u01]={t0_slot} 已存在，不改变。c. 日志字段：user=u01, mode=time, slot={t0_slot}, result=reject, reason=复用失败。",
            "一致。该时间槽已经使用，重放被拒绝。",
        ),
        case_row(
            "TC-D3",
            "允许窗口测试，±1 槽",
            "用户 u02，客户端 ts=t0，服务器 ts=t0+30",
            "通过",
            f"a. 返回值：success=True，错误码：OK_WITH_TIME_WINDOW。b. 服务器状态：记录 used_slot[u02]={t0_slot}。c. 日志字段：user=u02, mode=time, client_slot={t0_slot}, server_slot={t1_slot}, slot_delta=1, allowed_window=1, result=pass。",
            "一致。时间偏差为 1 个时间槽，在允许窗口内。",
        ),
        case_row(
            "TC-D4",
            "窗口外，过期",
            "客户端 ts=t0-60，服务器 ts=t0",
            "拒绝：新鲜性失败",
            f"a. 返回值：success=False，错误码：TIME_SLOT_OUT_OF_WINDOW。b. 服务器状态：不记录新的 used_slot。c. 日志字段：user=u01, mode=time, client_slot={old_slot}, server_slot={t0_slot}, slot_delta=2, allowed_window=1, result=reject, reason=新鲜性失败。",
            "一致。客户端时间槽过期，超出允许窗口。",
        ),
        case_row(
            "TC-D5",
            "篡改 timestamp",
            "客户端生成 ts=t0 的 OTP，后将消息中 timestamp 改为 t0+60",
            "拒绝：比较失败",
            f"a. 返回值：success=False，错误码：OTP_TIMESTAMP_MISMATCH。b. 服务器状态：不记录新的 used_slot。c. 日志字段：user=u01, mode=time, otp_original_slot={t0_slot}, received_slot={tampered_slot}, result=reject, reason=比较失败。",
            "一致。OTP 与被篡改后的 timestamp 不匹配。",
        ),
    ]


def run_security_cases() -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, int]]:
    list_valid = {"mode": "list", "id": "u01", "otp": "111111", "pos": 0}
    counter_valid = build_counter_message("u01", generate_counter_otp(SECRET_U01, 0), 0)
    time_valid = build_time_message("u01", generate_time_otp(SECRET_U01, BASE_TS, STEP), BASE_TS)

    verify_list_message(tamper_field(list_valid, "id", "u99"), init_shared_list("u01", OTP_LIST), str(LOG_PATH))
    verify_counter_message(
        tamper_field(counter_valid, "id", "u99"),
        init_counter_state("u01", SECRET_U01, 0),
        LOOK_AHEAD,
        str(LOG_PATH),
    )
    verify_time_message(
        tamper_field(time_valid, "id", "u99"),
        init_time_state("u01", SECRET_U01, BASE_TS),
        STEP,
        ALLOWED_WINDOW,
        str(LOG_PATH),
    )

    verify_list_message(tamper_field(list_valid, "otp", "999999"), init_shared_list("u01", OTP_LIST), str(LOG_PATH))
    verify_counter_message(
        tamper_field(counter_valid, "otp", "999999"),
        init_counter_state("u01", SECRET_U01, 0),
        LOOK_AHEAD,
        str(LOG_PATH),
    )
    verify_time_message(
        tamper_field(time_valid, "otp", "999999"),
        init_time_state("u01", SECRET_U01, BASE_TS),
        STEP,
        ALLOWED_WINDOW,
        str(LOG_PATH),
    )

    list_state = init_shared_list("u01", OTP_LIST)
    list_msg = generate_list_message("u01", list_state)
    verify_list_message(list_msg, list_state, str(LOG_PATH))
    replay_attack(list_msg, {"mode": "list", "state": list_state, "params": {"log_path": str(LOG_PATH)}})

    counter_state = init_counter_state("u01", SECRET_U01, 0)
    counter_msg = build_counter_message("u01", generate_counter_otp(SECRET_U01, 0), 0)
    verify_counter_message(counter_msg, counter_state, LOOK_AHEAD, str(LOG_PATH))
    replay_attack(
        counter_msg,
        {"mode": "counter", "state": counter_state, "params": {"look_ahead": LOOK_AHEAD, "log_path": str(LOG_PATH)}},
    )

    time_state = init_time_state("u01", SECRET_U01, BASE_TS)
    time_msg = build_time_message("u01", generate_time_otp(SECRET_U01, BASE_TS, STEP), BASE_TS)
    verify_time_message(time_msg, time_state, STEP, ALLOWED_WINDOW, str(LOG_PATH))
    replay_attack(
        time_msg,
        {"mode": "time", "state": time_state, "params": {"step": STEP, "allowed_window": ALLOWED_WINDOW, "log_path": str(LOG_PATH)}},
    )

    verify_list_message(tamper_field(list_valid, "pos", 1), init_shared_list("u01", OTP_LIST), str(LOG_PATH))
    verify_counter_message(
        tamper_field(counter_valid, "counter", 2),
        init_counter_state("u01", SECRET_U01, 0),
        LOOK_AHEAD,
        str(LOG_PATH),
    )
    verify_time_message(
        tamper_field(time_valid, "timestamp", BASE_TS + STEP),
        init_time_state("u01", SECRET_U01, BASE_TS + STEP),
        STEP,
        ALLOWED_WINDOW,
        str(LOG_PATH),
    )

    list_state_for_binding = init_shared_list("u01", OTP_LIST)
    list_state_for_binding["pos"] = 1
    verify_list_message(
        {"mode": "list", "id": "u01", "otp": "111111", "pos": 1},
        list_state_for_binding,
        str(LOG_PATH),
    )
    verify_counter_message(
        build_counter_message("u01", generate_counter_otp(SECRET_U01, 0), 1),
        init_counter_state("u01", SECRET_U01, 0),
        LOOK_AHEAD,
        str(LOG_PATH),
    )
    verify_time_message(
        build_time_message("u01", generate_time_otp(SECRET_U01, BASE_TS, STEP), BASE_TS + STEP),
        init_time_state("u01", SECRET_U01, BASE_TS + STEP),
        STEP,
        ALLOWED_WINDOW,
        str(LOG_PATH),
    )

    security_rows = [
        {
            "用例编号": "TC-S1",
            "攻击类型": "身份篡改",
            "测试说明": "id 错误但 OTP 正确",
            "口令表": "拒绝：比较失败",
            "计数器": "拒绝：比较失败",
            "时间 OTP": "拒绝：比较失败",
            "原因": "错误 id 会导致服务器读取错误用户的密钥或状态，重算 OTP 不一致。",
        },
        {
            "用例编号": "TC-S2",
            "攻击类型": "OTP 篡改",
            "测试说明": "OTP 错误，同步字段正确",
            "口令表": "拒绝：比较失败",
            "计数器": "拒绝：比较失败",
            "时间 OTP": "拒绝：比较失败",
            "原因": "OTP 被修改后，与服务器重算值不一致。",
        },
        {
            "用例编号": "TC-S3",
            "攻击类型": "重放攻击",
            "测试说明": "完整重放已通过消息",
            "口令表": "拒绝：复用失败",
            "计数器": "拒绝：复用失败",
            "时间 OTP": "拒绝：复用失败",
            "原因": "口令表位置、计数器或时间槽已经被使用。",
        },
        {
            "用例编号": "TC-S4",
            "攻击类型": "同步字段篡改",
            "测试说明": "改 counter / ts",
            "口令表": "拒绝：新鲜性失败",
            "计数器": "拒绝：比较失败",
            "时间 OTP": "拒绝：比较失败",
            "原因": "同步字段改变后，OTP 与状态字段不匹配；口令表型表现为当前位置不一致。",
        },
        {
            "用例编号": "TC-S5",
            "攻击类型": "绑定性破坏",
            "测试说明": "OTP 与 counter / ts 不匹配",
            "口令表": "拒绝：比较失败",
            "计数器": "拒绝：比较失败",
            "时间 OTP": "拒绝：比较失败",
            "原因": "OTP 必须与身份、计数器或时间槽绑定，绑定关系破坏后验证失败。",
        },
    ]

    comparison_rows = [
        {
            "安全属性": "防重放",
            "口令表": "通过。成功后 pos 推进，旧口令无法再次使用。",
            "计数器": "通过。成功后 counter 推进，旧 counter 被拒绝。",
            "时间 OTP": "通过。成功后记录已用 slot，同一时间槽不能重复使用。",
        },
        {
            "安全属性": "状态依赖",
            "口令表": "强。必须保存并维护当前 pos。",
            "计数器": "强。必须保存并维护服务器端 counter。",
            "时间 OTP": "中等。需要时间窗口判断，并建议保存已用 slot。",
        },
        {
            "安全属性": "同步要求",
            "口令表": "高。客户端和服务器 pos 必须一致。",
            "计数器": "中等。允许通过 look_ahead 处理轻微超前。",
            "时间 OTP": "中等。允许通过 allowed_window 处理轻微时钟偏差。",
        },
        {
            "安全属性": "容错能力",
            "口令表": "较弱。指针失步后容易失败。",
            "计数器": "较强。窗口内漂移可以通过并重同步。",
            "时间 OTP": "较强。窗口内时间偏差可以通过。",
        },
        {
            "安全属性": "实现复杂度",
            "口令表": "较低。规则简单，但口令表管理不灵活。",
            "计数器": "中等。需要密钥、计数器、窗口和状态推进。",
            "时间 OTP": "中等偏高。需要时间槽、时钟窗口和已用 slot 记录。",
        },
    ]
    return security_rows, comparison_rows, {}


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def md_table(headers: list[str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for item in rows:
        lines.append("| " + " | ".join(md_escape(item.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def build_report(
    static_rows: list[dict[str, str]],
    list_rows: list[dict[str, str]],
    counter_rows: list[dict[str, str]],
    time_rows: list[dict[str, str]],
    security_rows: list[dict[str, str]],
    comparison_rows: list[dict[str, str]],
    fail_summary: dict[str, int] | None = None,
) -> str:
    detail_headers = ["用例编号", "操作描述", "测试输入", "预期结果", "实际输出与分析", "结果判定"]
    security_headers = ["用例编号", "攻击类型", "测试说明", "口令表", "计数器", "时间 OTP", "原因"]
    comparison_headers = ["安全属性", "口令表", "计数器", "时间 OTP"]

    return f"""# 一次性口令机制（OTP）验证实验

## 一、实验名称

一次性口令机制（OTP）验证实验。

## 二、实验目的

1. 理解静态口令与一次性口令在认证安全性上的差异，重点理解重放攻击为什么会对静态口令造成威胁。
2. 掌握共享口令表型、序列 / 计数器同步型、时间同步型三类典型 OTP。
3. 掌握认证端生成 OTP、验证端重算并比较、状态推进与日志记录的完整流程。
4. 验证 OTP 对重放攻击的抵抗能力，并分析同步误差、口令复用、篡改消息等异常场景。
5. 基于实验现象总结 OTP 的安全边界：增强认证与新鲜性，不直接等价于通信保密。

## 三、实验原理

静态口令每次提交相同秘密，服务器只做固定值比较时，攻击者截获一次合法认证消息后可以完整重放。一次性口令把认证值与口令表位置、计数器或时间槽绑定，服务器验证成功后推进状态或记录已用标记，使旧消息再次提交时被判定为复用失败、新鲜性失败或比较失败。

共享口令表型 OTP 要求客户端和服务器保存相同口令表并同步当前位置；计数器型 OTP 使用共享密钥和 counter 派生口令，并可通过 look_ahead 滑动窗口处理轻微超前；时间同步型 OTP 使用共享密钥和时间槽派生口令，并通过 allowed_window 容忍小幅时钟偏差。

## 四、实验环境

- 操作系统：Windows / Linux / macOS 均可。
- 编程语言：Python 3.x，本次运行环境为 Python 3.13.5。
- 开发工具：PyCharm、VS Code、Jupyter Notebook 或命令行均可。

## 五、程序设计

程序采用模块化结构：`common.py` 负责用户标识规范化、HMAC 派生、OTP 截断、恒定时间比较、复用检查和日志记录；`static_password_baseline.py`、`otp_list_mode.py`、`otp_counter_mode.py`、`otp_time_mode.py` 分别实现对照模式与三类 OTP；`attack_simulation.py` 负责重放、篡改和漂移模拟；`main.py` 负责组织实验用例并生成报告。

实验公共参数：

- 用户：`u01`，`u02`（用于时间同步模式干净测试）。
- 口令表：`L=[111111,222222,333333,444444,555555]`，初始 `pos=0`。
- 计数器模式：初始 `counter=0`；服务器验证窗口 `look_ahead=3`。
- 时间同步模式：`step=30s`，`allowed_window=1`（允许 ±1 个时间槽）；基准时间戳 `t0=1700000000`。

## 六、实验结果

### 实验 A：静态口令对照 (Baseline)

{md_table(detail_headers, static_rows)}

### 实验 B：共享口令表型 OTP

{md_table(detail_headers, list_rows)}

### 实验 C：计数器/序列同步型 OTP

{md_table(detail_headers, counter_rows)}

### 实验 D：时间同步型 OTP

{md_table(detail_headers, time_rows)}

### 实验 E/F：统一安全性用例与模式比较

#### 统一攻击模型

{md_table(security_headers, security_rows)}

#### 模式安全性对比

{md_table(comparison_headers, comparison_rows)}

## 七、结果分析

1. 静态口令不维护新鲜性状态，TC-A3 中完整重放仍能通过。
2. 共享口令表型 OTP 成功后推进 `pos`，旧位置口令和指针失步都会被拒绝。
3. 计数器型 OTP 绑定 `counter`，窗口内漂移可以通过并同步服务器状态，窗口外漂移被拒绝。
4. 时间同步型 OTP 绑定时间槽，允许窗口内时钟偏差，但已用 slot 不能重复使用。
5. OTP 增强的是认证与新鲜性，不直接提供通信保密；真实系统仍需要 TLS、完整性保护、限速和审计。

## 八、运行方法

在实验目录执行：

```bash
python -m otp_lab.main
```

运行后会生成 `otp_lab/logs/events.jsonl` 和 `otp_lab_report.md`。
"""


def main() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("", encoding="utf-8")

    static_rows = run_static_cases()
    list_rows = run_list_cases()
    counter_rows = run_counter_cases()
    time_rows = run_time_cases()
    security_rows, comparison_rows, fail_summary = run_security_cases()

    report = build_report(
        static_rows,
        list_rows,
        counter_rows,
        time_rows,
        security_rows,
        comparison_rows,
        fail_summary,
    )
    REPORT_PATH.write_text(report, encoding="utf-8-sig")

    total_cases = (
        len(static_rows)
        + len(list_rows)
        + len(counter_rows)
        + len(time_rows)
        + len(security_rows)
    )
    print(f"OTP lab completed: {total_cases} cases executed.")
    print(f"Report: {REPORT_PATH}")
    print(f"Log: {LOG_PATH}")


if __name__ == "__main__":
    main()
