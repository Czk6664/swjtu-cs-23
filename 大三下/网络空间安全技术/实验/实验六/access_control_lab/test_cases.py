from copy import deepcopy

from models import AccessRequest, Resource, Subject


def build_subjects() -> dict:
    return {
        "alice": Subject(
            "alice",
            groups={"dev", "employees"},
            roles={"developer"},
            attrs={"department": "engineering", "clearance": "internal", "mfa": True},
        ),
        "bob": Subject(
            "bob",
            groups={"finance", "employees"},
            roles={"finance_user"},
            attrs={"department": "finance", "clearance": "confidential", "mfa": True},
        ),
        "carol": Subject(
            "carol",
            groups={"audit", "employees"},
            roles={"auditor"},
            attrs={"department": "audit", "clearance": "confidential", "mfa": True},
        ),
        "dave": Subject(
            "dave",
            groups={"guests"},
            roles={"guest"},
            attrs={"department": "external", "clearance": "public", "mfa": False},
        ),
        "erin": Subject(
            "erin",
            groups={"management", "employees"},
            roles={"manager"},
            attrs={"department": "management", "clearance": "secret", "mfa": True},
        ),
        "frank": Subject(
            "frank",
            groups={"dev", "audit"},
            roles={"developer", "auditor"},
            attrs={"department": "engineering", "clearance": "confidential", "mfa": True},
        ),
    }


def build_resources() -> dict:
    return {
        "repo": Resource(
            "repo",
            owner="alice",
            resource_type="code",
            label="internal",
            attrs={"department": "engineering", "sensitivity": "normal", "mfa_required": False},
        ),
        "payroll": Resource(
            "payroll",
            owner="bob",
            resource_type="finance",
            label="confidential",
            attrs={"department": "finance", "sensitivity": "high", "mfa_required": True},
        ),
        "audit_log": Resource(
            "audit_log",
            owner="carol",
            resource_type="log",
            label="confidential",
            attrs={"department": "audit", "sensitivity": "high", "mfa_required": True},
        ),
        "strategy_doc": Resource(
            "strategy_doc",
            owner="erin",
            resource_type="document",
            label="secret",
            attrs={"department": "management", "sensitivity": "high", "mfa_required": True},
        ),
        "public_news": Resource(
            "public_news",
            owner="alice",
            resource_type="notice",
            label="public",
            attrs={"department": "public", "sensitivity": "low", "mfa_required": False},
        ),
    }


def build_matrix_permissions() -> list:
    return [
        {"subject_id": "alice", "resource_id": "repo", "actions": ["read", "write"]},
        {"subject_id": "bob", "resource_id": "payroll", "actions": ["read"]},
        {"subject_id": "carol", "resource_id": "audit_log", "actions": ["read"]},
        {"subject_id": "dave", "resource_id": "public_news", "actions": ["read"]},
    ]


def build_acl_policies() -> dict:
    return {
        "repo": [
            {"id": "acl-repo-alice", "type": "user", "grantee": "alice", "actions": ["read", "write"]},
            {"id": "acl-repo-dev", "type": "group", "grantee": "dev", "actions": ["read"]},
        ],
        "payroll": [
            {"id": "acl-payroll-finance", "type": "group", "grantee": "finance", "actions": ["read"]},
        ],
        "audit_log": [
            {"id": "acl-audit-auditors", "type": "group", "grantee": "audit", "actions": ["read"]},
        ],
        "public_news": [
            {"id": "acl-public-guests", "type": "group", "grantee": "guests", "actions": ["read"]},
        ],
    }


def build_rbac_policy() -> dict:
    return {
        "user_roles": {
            "alice": ["developer"],
            "bob": ["finance_user"],
            "carol": ["auditor"],
            "dave": ["guest"],
            "erin": ["manager"],
            "frank": ["developer", "auditor"],
        },
        "role_hierarchy": {
            "manager": ["reviewer"],
        },
        "role_permissions": {
            "developer": [
                {"resource_id": "repo", "action": "read"},
                {"resource_id": "repo", "action": "write"},
            ],
            "finance_user": [
                {"resource_id": "payroll", "action": "read"},
            ],
            "auditor": [
                {"resource_id": "audit_log", "action": "read"},
            ],
            "guest": [
                {"resource_id": "public_news", "action": "read"},
            ],
            "reviewer": [
                {"resource_id": "strategy_doc", "action": "read"},
            ],
            "manager": [
                {"resource_id": "strategy_doc", "action": "approve"},
            ],
        },
        "mutually_exclusive_roles": [["developer", "auditor"]],
    }


def build_mac_policy() -> dict:
    return {
        "label_order": ["public", "internal", "confidential", "secret"],
        "enforce_integrity": False,
    }


def build_abac_policies() -> list:
    return [
        {
            "id": "abac-managed-low-risk-same-dept",
            "effect": "Permit",
            "target": {"action": "read", "resource.sensitivity": "normal"},
            "conditions": [
                {"attr": "subject.department", "op": "eq", "value": "$resource.department"},
                {"attr": "environment.device_state", "op": "eq", "value": "managed"},
                {"attr": "environment.risk", "op": "lte", "value": 3},
            ],
        },
        {
            "id": "abac-finance-office-hours",
            "effect": "Permit",
            "target": {"action": "read", "resource.department": "finance"},
            "conditions": [
                {"attr": "subject.department", "op": "eq", "value": "finance"},
                {"attr": "environment.location", "op": "in", "value": ["office", "vpn"]},
                {"attr": "environment.time", "op": "time_between", "value": ["09:00", "18:00"]},
                {"attr": "environment.device_state", "op": "eq", "value": "managed"},
            ],
        },
        {
            "id": "abac-sensitive-requires-mfa-deny",
            "effect": "Deny",
            "target": {"resource.sensitivity": "high"},
            "conditions": [
                {"attr": "subject.mfa", "op": "eq", "value": False},
            ],
        },
        {
            "id": "abac-unmanaged-device-deny",
            "effect": "Deny",
            "target": {},
            "conditions": [
                {"attr": "environment.device_state", "op": "eq", "value": "unmanaged"},
            ],
        },
        {
            "id": "abac-conflict-permit",
            "effect": "Permit",
            "target": {"subject.id": "bob", "resource.id": "payroll", "action": "read"},
            "conditions": [
                {"attr": "environment.device_state", "op": "eq", "value": "managed"},
                {"attr": "environment.conflict_case", "op": "eq", "value": True},
            ],
        },
        {
            "id": "abac-conflict-deny",
            "effect": "Deny",
            "target": {"subject.id": "bob", "resource.id": "payroll", "action": "read"},
            "conditions": [
                {"attr": "environment.risk", "op": "gte", "value": 5},
                {"attr": "environment.conflict_case", "op": "eq", "value": True},
            ],
        },
    ]


def build_all_policies() -> dict:
    return {
        "acl": build_acl_policies(),
        "rbac": build_rbac_policy(),
        "mac": build_mac_policy(),
        "abac": build_abac_policies(),
    }


def base_data():
    return build_subjects(), build_resources(), build_all_policies()


def clone_policies(policies: dict) -> dict:
    return deepcopy(policies)


def experiment_rows() -> dict:
    common_managed = {"device_state": "managed", "risk": 2, "time": "10:00", "location": "office"}
    return {
        "matrix": [
            ("MX-01", "已授权主体访问已授权客体", AccessRequest("alice", "repo", "read"), "Permit"),
            ("MX-02", "主体存在但矩阵未授权", AccessRequest("alice", "payroll", "write"), "Deny"),
            ("MX-03", "未知主体访问", AccessRequest("unknown_user", "repo", "read"), "Deny"),
            ("MX-04", "未知客体访问", AccessRequest("alice", "unknown_resource", "read"), "Deny"),
            ("MX-05", "修改矩阵后重新验证", AccessRequest("bob", "repo", "read"), "Permit"),
        ],
        "acl": [
            ("AC-01", "用户 ACL 直接授权", AccessRequest("alice", "repo", "write"), "Permit"),
            ("AC-02", "组 ACL 授权", AccessRequest("frank", "repo", "read"), "Permit"),
            ("AC-03", "未命中 ACL 默认拒绝", AccessRequest("dave", "repo", "write"), "Deny"),
            ("AC-04", "资源侧 ACL 授权写操作", AccessRequest("dave", "repo", "write"), "Permit"),
            ("AC-05", "非授权组访问敏感资源", AccessRequest("alice", "payroll", "read"), "Deny"),
        ],
        "rbac": [
            ("RB-01", "角色具备资源写权限", AccessRequest("alice", "repo", "write"), "Permit", {"developer"}),
            ("RB-02", "角色具备审计读取权限", AccessRequest("carol", "audit_log", "read"), "Permit", {"auditor"}),
            ("RB-03", "低权限角色访问未授权资源", AccessRequest("dave", "strategy_doc", "read"), "Deny", {"guest"}),
            ("RB-04", "互斥角色同时激活", AccessRequest("frank", "repo", "read"), "Deny", {"developer", "auditor"}),
            ("RB-05", "管理角色执行审批操作", AccessRequest("erin", "strategy_doc", "approve"), "Permit", {"manager"}),
        ],
        "mac": [
            ("MA-01", "同级标签读取", AccessRequest("bob", "payroll", "read"), "Permit"),
            ("MA-02", "低级别主体向上读取", AccessRequest("dave", "strategy_doc", "read"), "Deny"),
            ("MA-03", "高级别主体读取低级别客体", AccessRequest("erin", "public_news", "read"), "Permit"),
            ("MA-04", "高级别主体向下写", AccessRequest("erin", "public_news", "write"), "Deny"),
            ("MA-05", "public 主体读取 public 客体", AccessRequest("dave", "public_news", "read"), "Permit"),
        ],
        "abac": [
            ("AB-01", "部门、设备、风险均满足", AccessRequest("alice", "repo", "read", common_managed), "Permit"),
            ("AB-02", "设备状态不满足", AccessRequest("alice", "repo", "read", {**common_managed, "device_state": "unmanaged"}), "Deny"),
            ("AB-03", "财务部门办公时间访问", AccessRequest("bob", "payroll", "read", common_managed), "Permit"),
            ("AB-04", "超出办公时间访问", AccessRequest("bob", "payroll", "read", {**common_managed, "time": "21:00"}), "Deny"),
            ("AB-05", "敏感资源缺少二次验证", AccessRequest("dave", "strategy_doc", "read", common_managed), "Deny"),
        ],
        "conflict": [
            ("CF-01", "deny-overrides 冲突处理", AccessRequest("bob", "payroll", "read", {**common_managed, "risk": 5, "conflict_case": True}), "Deny", "deny_overrides"),
            ("CF-02", "permit-overrides 冲突处理", AccessRequest("bob", "payroll", "read", {**common_managed, "risk": 5, "conflict_case": True}), "Permit", "permit_overrides"),
            ("CF-03", "first-applicable 冲突处理", AccessRequest("bob", "payroll", "read", {**common_managed, "risk": 5, "conflict_case": True}), "Permit", "first_applicable"),
        ],
    }
