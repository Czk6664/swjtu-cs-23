import json
from dataclasses import asdict
from pathlib import Path

from abac_model import check_abac_access
from acl_model import check_acl_access, grant_acl_permission
from audit_logger import create_audit_record, summarize_audit_log, write_audit_log
from decision_engine import explain_decision
from mac_model import check_mac_access
from matrix_model import build_access_matrix, check_matrix_access, update_matrix_permission
from rbac_model import check_rbac_access
from test_cases import (
    base_data,
    build_matrix_permissions,
    clone_policies,
    experiment_rows,
)


BASE_DIR = Path(__file__).resolve().parent
AUDIT_LOG = BASE_DIR / "audit_log.jsonl"
RESULTS_JSON = BASE_DIR / "experiment_results.json"
SECTION6_TXT = BASE_DIR / "section6_program_design.txt"


def _reset_audit_log():
    AUDIT_LOG.write_text("", encoding="utf-8")


def _record(records: list, test_id: str, scene: str, request, expected: str, actual, model_name: str, extra=None):
    consistent = "是" if expected == actual.effect else "否"
    row = {
        "测试编号": test_id,
        "测试场景": scene,
        "输入条件": f"subject={request.subject_id}, resource={request.resource_id}, action={request.action}, context={request.context}",
        "期望结果": expected,
        "实际结果": f"{actual.effect} ({actual.reason})",
        "是否一致": consistent,
        "结果分析": _analysis_for(actual.reason),
    }
    records.append(row)
    audit_record = create_audit_record(request, actual, model_name, extra=extra)
    audit_record["test_id"] = test_id
    write_audit_log(audit_record, str(AUDIT_LOG))
    return row


def _analysis_for(reason: str) -> str:
    mapping = {
        "MATRIX_ACTION_ALLOWED": "访问矩阵单元格包含该操作，授权通过。",
        "MATRIX_ACTION_NOT_GRANTED": "矩阵中没有对应操作权限，按默认拒绝处理。",
        "UNKNOWN_SUBJECT": "主体表中不存在该 subject_id，授权失败。",
        "UNKNOWN_RESOURCE": "资源表中不存在该 resource_id，授权失败。",
        "ACL_ENTRY_ALLOWED": "资源 ACL 中存在匹配的用户或组允许条目。",
        "ACL_NO_MATCH_DEFAULT_DENY": "未命中任何 ACL 允许条目，默认拒绝。",
        "RBAC_PERMISSION_ALLOWED": "激活角色汇总后的权限集合包含目标资源和操作。",
        "RBAC_PERMISSION_NOT_GRANTED": "低权限角色没有目标资源操作权限。",
        "RBAC_MUTUALLY_EXCLUSIVE_ROLES": "会话同时激活互斥角色，违反职责分离约束。",
        "MAC_LABEL_RULE_ALLOWED": "主体等级与客体标签满足 MAC 读写规则。",
        "MAC_NO_READ_UP": "低级别主体读取高级别客体，违反 no read up。",
        "MAC_NO_WRITE_DOWN": "高级别主体写入低级别客体，违反 no write down。",
        "ABAC_POLICY_ALLOWED": "请求属性满足允许策略，授权通过。",
        "ABAC_DENY_OVERRIDES": "同时命中允许和拒绝策略，deny-overrides 返回拒绝。",
        "ABAC_PERMIT_OVERRIDES": "同时命中允许和拒绝策略，permit-overrides 返回允许。",
        "ABAC_FIRST_APPLICABLE_PERMIT": "按策略顺序采用第一条适用的 Permit 策略。",
        "ABAC_NO_POLICY_MATCH_DEFAULT_DENY": "属性条件不满足任何允许策略，默认拒绝。",
    }
    return mapping.get(reason, f"授权结果由原因码 {reason} 决定。")


def run_matrix_experiment():
    subjects, resources, _ = base_data()
    matrix = build_access_matrix(subjects, resources, build_matrix_permissions())
    records = []
    for test_id, scene, request, expected in experiment_rows()["matrix"]:
        if test_id == "MX-05":
            update_matrix_permission(matrix, request.subject_id, request.resource_id, request.action, "grant")
        decision = check_matrix_access(request, matrix)
        _record(records, test_id, scene, request, expected, decision, "matrix")
    return records


def run_acl_experiment():
    subjects, resources, policies = base_data()
    acl_policies = clone_policies(policies)["acl"]
    records = []
    for test_id, scene, request, expected in experiment_rows()["acl"]:
        if test_id == "AC-04":
            grant_acl_permission(acl_policies, request.resource_id, request.subject_id, {request.action})
        decision = check_acl_access(request, subjects, resources, acl_policies)
        _record(records, test_id, scene, request, expected, decision, "acl")
    return records


def run_rbac_experiment():
    subjects, resources, policies = base_data()
    records = []
    for test_id, scene, request, expected, active_roles in experiment_rows()["rbac"]:
        decision = check_rbac_access(request, subjects, resources, policies["rbac"], active_roles)
        _record(records, test_id, scene, request, expected, decision, "rbac", {"active_roles": sorted(active_roles)})
    return records


def run_mac_experiment():
    subjects, resources, policies = base_data()
    records = []
    for test_id, scene, request, expected in experiment_rows()["mac"]:
        decision = check_mac_access(request, subjects, resources, policies["mac"])
        _record(records, test_id, scene, request, expected, decision, "mac")
    return records


def run_abac_experiment():
    subjects, resources, policies = base_data()
    records = []
    for test_id, scene, request, expected in experiment_rows()["abac"]:
        decision = check_abac_access(request, subjects, resources, policies["abac"], "deny_overrides")
        _record(records, test_id, scene, request, expected, decision, "abac", {"combining_alg": "deny_overrides"})
    return records


def run_conflict_experiment():
    subjects, resources, policies = base_data()
    records = []
    for test_id, scene, request, expected, algorithm in experiment_rows()["conflict"]:
        decision = check_abac_access(request, subjects, resources, policies["abac"], algorithm)
        _record(records, test_id, scene, request, expected, decision, "abac-conflict", {"combining_alg": algorithm})
    return records


def run_audit_analysis():
    return summarize_audit_log(str(AUDIT_LOG))


def _write_section6_txt(results: dict, summary: dict):
    modules = [
        "models.py",
        "policy_store.py",
        "matrix_model.py",
        "acl_model.py",
        "rbac_model.py",
        "mac_model.py",
        "abac_model.py",
        "decision_engine.py",
        "audit_logger.py",
        "test_cases.py",
        "main.py",
    ]
    lines = [
        "第六部分 程序设计与代码清单",
        "=" * 36,
        "",
        "一、运行方式",
        "在实验六目录下执行：python access_control_lab/main.py",
        "",
        "二、模块说明",
        "本工程按照任务书推荐结构实现访问矩阵、ACL/DAC、RBAC、MAC、ABAC、策略冲突组合和审计日志分析。",
        "策略与测试数据为教学用途，不操作真实系统权限。",
        "",
        "三、运行结果摘要",
    ]
    for group, rows in results.items():
        if group == "audit":
            continue
        lines.append(f"{group}: {len(rows)} 条测试")
        for row in rows:
            lines.append(
                f"  {row['测试编号']} {row['测试场景']} -> {row['实际结果']}，是否一致：{row['是否一致']}"
            )
    lines.extend(
        [
            "",
            "四、审计统计",
            json.dumps(summary, ensure_ascii=False, indent=2),
            "",
            "五、代码清单",
        ]
    )
    for module in modules:
        path = BASE_DIR / module
        lines.extend(["", "-" * 36, module, "-" * 36, path.read_text(encoding="utf-8")])
    SECTION6_TXT.write_text("\n".join(lines), encoding="utf-8")


def _save_results_json(results: dict, summary: dict):
    payload = {"results": results, "audit": summary}
    RESULTS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    _reset_audit_log()
    results = {
        "访问矩阵实验": run_matrix_experiment(),
        "ACL / DAC 实验": run_acl_experiment(),
        "RBAC 实验": run_rbac_experiment(),
        "MAC 标签控制实验": run_mac_experiment(),
        "ABAC 条件策略实验": run_abac_experiment(),
        "策略冲突与组合实验": run_conflict_experiment(),
    }
    summary = run_audit_analysis()
    _save_results_json(results, summary)
    _write_section6_txt(results, summary)

    print("Access control experiments completed.")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Audit log: {AUDIT_LOG}")
    print(f"Section 6 txt: {SECTION6_TXT}")
    print(f"Results JSON: {RESULTS_JSON}")


if __name__ == "__main__":
    main()

