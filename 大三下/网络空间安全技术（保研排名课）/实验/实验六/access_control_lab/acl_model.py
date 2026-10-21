from models import AccessDecision, DENY, PERMIT


def match_acl_entry(request, subject, acl_entry: dict) -> bool:
    """Check whether one ACL entry matches user/group, action, and resource."""

    if request.action not in set(acl_entry.get("actions", [])):
        return False
    principal_type = acl_entry.get("type", "user")
    grantee = acl_entry.get("grantee")
    if principal_type == "user":
        return request.subject_id == grantee
    if principal_type == "group":
        return grantee in subject.groups
    return False


def check_acl_access(request, subjects: dict, resources: dict, acl_policies: dict):
    """Authorize by resource-side ACL. Missing allow entries deny by default."""

    if request.subject_id not in subjects:
        return AccessDecision(DENY, "UNKNOWN_SUBJECT", "acl-default-deny")
    if request.resource_id not in resources:
        return AccessDecision(DENY, "UNKNOWN_RESOURCE", "acl-default-deny")

    subject = subjects[request.subject_id]
    entries = acl_policies.get(request.resource_id, [])
    for entry in entries:
        if match_acl_entry(request, subject, entry):
            effect = entry.get("effect", PERMIT)
            policy_id = entry.get("id", f"acl:{request.resource_id}:{entry.get('grantee')}")
            if effect == DENY:
                return AccessDecision(DENY, "ACL_EXPLICIT_DENY", policy_id)
            return AccessDecision(PERMIT, "ACL_ENTRY_ALLOWED", policy_id)
    return AccessDecision(DENY, "ACL_NO_MATCH_DEFAULT_DENY", "acl-default-deny")


def grant_acl_permission(acl_policies: dict, resource_id: str, grantee: str, actions: set):
    """Grant simulated DAC permissions."""

    entries = acl_policies.setdefault(resource_id, [])
    entry = {
        "id": f"dac-grant-{resource_id}-{grantee}",
        "type": "user",
        "grantee": grantee,
        "actions": sorted(actions),
        "effect": PERMIT,
    }
    entries.append(entry)
    return entry


def revoke_acl_permission(acl_policies: dict, resource_id: str, grantee: str, actions: set):
    """Revoke simulated DAC permissions."""

    target = set(actions)
    for entry in acl_policies.get(resource_id, []):
        if entry.get("grantee") == grantee:
            remaining = set(entry.get("actions", [])) - target
            entry["actions"] = sorted(remaining)
    return acl_policies

