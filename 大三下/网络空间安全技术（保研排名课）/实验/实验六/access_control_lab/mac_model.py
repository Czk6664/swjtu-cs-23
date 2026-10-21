from models import AccessDecision, DENY, PERMIT


def compare_security_label(subject_label: str, object_label: str, label_order: list) -> int:
    """Compare labels. Positive means subject is higher than object."""

    if subject_label not in label_order or object_label not in label_order:
        raise ValueError("unknown security label")
    return label_order.index(subject_label) - label_order.index(object_label)


def check_confidentiality_rule(action: str, subject_label: str, object_label: str, mac_policy: dict) -> bool:
    """Bell-LaPadula style: no read up, no write down."""

    diff = compare_security_label(subject_label, object_label, mac_policy["label_order"])
    if action == "read":
        return diff >= 0
    if action == "write":
        return diff <= 0
    return True


def check_integrity_rule(action: str, subject_label: str, object_label: str, mac_policy: dict) -> bool:
    """Optional simplified integrity hook for the experiment."""

    if not mac_policy.get("enforce_integrity", False):
        return True
    diff = compare_security_label(subject_label, object_label, mac_policy["label_order"])
    if action == "read":
        return diff <= 0
    if action == "write":
        return diff >= 0
    return True


def check_mac_access(request, subjects: dict, resources: dict, mac_policy: dict):
    """Authorize by subject clearance and object label."""

    if request.subject_id not in subjects:
        return AccessDecision(DENY, "UNKNOWN_SUBJECT", "mac-default-deny")
    if request.resource_id not in resources:
        return AccessDecision(DENY, "UNKNOWN_RESOURCE", "mac-default-deny")

    subject_label = subjects[request.subject_id].attrs.get("clearance", "public")
    object_label = resources[request.resource_id].label or "public"
    try:
        confidentiality_ok = check_confidentiality_rule(
            request.action, subject_label, object_label, mac_policy
        )
        integrity_ok = check_integrity_rule(request.action, subject_label, object_label, mac_policy)
    except ValueError:
        return AccessDecision(DENY, "MAC_UNKNOWN_LABEL", "mac-label-order")

    if not confidentiality_ok:
        if request.action == "read":
            return AccessDecision(DENY, "MAC_NO_READ_UP", "mac-confidentiality")
        if request.action == "write":
            return AccessDecision(DENY, "MAC_NO_WRITE_DOWN", "mac-confidentiality")
        return AccessDecision(DENY, "MAC_CONFIDENTIALITY_DENY", "mac-confidentiality")
    if not integrity_ok:
        return AccessDecision(DENY, "MAC_INTEGRITY_DENY", "mac-integrity")
    return AccessDecision(PERMIT, "MAC_LABEL_RULE_ALLOWED", "mac-label-rule")

