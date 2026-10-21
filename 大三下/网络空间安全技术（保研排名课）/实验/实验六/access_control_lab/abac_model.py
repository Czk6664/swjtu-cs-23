from datetime import time

from models import AccessDecision, DENY, PERMIT


def build_attribute_context(request, subject, resource) -> dict:
    """Merge subject, resource, action, and environment attributes."""

    return {
        "subject": {"id": subject.subject_id, **subject.attrs},
        "resource": {
            "id": resource.resource_id,
            "owner": resource.owner,
            "type": resource.resource_type,
            "label": resource.label,
            **resource.attrs,
        },
        "action": request.action,
        "environment": dict(request.context),
    }


def _get_path(data: dict, path: str):
    current = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _to_time(value):
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        hour, minute = value.split(":")[:2]
        return time(int(hour), int(minute))
    return value


def evaluate_condition(condition: dict, attr_context: dict) -> bool:
    """Evaluate one simple ABAC condition."""

    left = _get_path(attr_context, condition["attr"])
    op = condition.get("op", "eq")
    right = condition.get("value")
    if isinstance(right, str) and right.startswith("$"):
        right = _get_path(attr_context, right[1:])

    if op == "eq":
        return left == right
    if op == "ne":
        return left != right
    if op == "in":
        return left in right
    if op == "contains":
        return right in left if left is not None else False
    if op == "lte":
        return left <= right
    if op == "gte":
        return left >= right
    if op == "between":
        low, high = right
        return low <= left <= high
    if op == "time_between":
        current = _to_time(left)
        start = _to_time(right[0])
        end = _to_time(right[1])
        return start <= current <= end
    raise ValueError(f"unsupported condition operator: {op}")


def match_abac_policy(policy: dict, attr_context: dict) -> bool:
    """Return True when all target and condition clauses match."""

    target = policy.get("target", {})
    for key, expected in target.items():
        actual = _get_path(attr_context, key)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return all(evaluate_condition(item, attr_context) for item in policy.get("conditions", []))


def _combine(matches: list, combining_alg: str):
    if not matches:
        return AccessDecision(DENY, "ABAC_NO_POLICY_MATCH_DEFAULT_DENY", "abac-default-deny")
    if combining_alg == "deny_overrides":
        for policy in matches:
            if policy["effect"] == DENY:
                return AccessDecision(DENY, "ABAC_DENY_OVERRIDES", policy["id"])
        return AccessDecision(PERMIT, "ABAC_POLICY_ALLOWED", matches[0]["id"])
    if combining_alg == "permit_overrides":
        for policy in matches:
            if policy["effect"] == PERMIT:
                return AccessDecision(PERMIT, "ABAC_PERMIT_OVERRIDES", policy["id"])
        return AccessDecision(DENY, "ABAC_POLICY_DENIED", matches[0]["id"])
    if combining_alg == "first_applicable":
        first = matches[0]
        reason = "ABAC_FIRST_APPLICABLE_PERMIT" if first["effect"] == PERMIT else "ABAC_FIRST_APPLICABLE_DENY"
        return AccessDecision(first["effect"], reason, first["id"])
    raise ValueError(f"unsupported combining algorithm: {combining_alg}")


def check_abac_access(request, subjects: dict, resources: dict, abac_policies: list, combining_alg: str):
    """Authorize by ABAC policies and a combining algorithm."""

    if request.subject_id not in subjects:
        return AccessDecision(DENY, "UNKNOWN_SUBJECT", "abac-default-deny")
    if request.resource_id not in resources:
        return AccessDecision(DENY, "UNKNOWN_RESOURCE", "abac-default-deny")

    attr_context = build_attribute_context(request, subjects[request.subject_id], resources[request.resource_id])
    matches = [policy for policy in abac_policies if match_abac_policy(policy, attr_context)]
    return _combine(matches, combining_alg)

