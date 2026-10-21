from models import AccessDecision, DENY, PERMIT


def get_user_roles(subject, rbac_policy: dict) -> set:
    """Get roles assignable to a user."""

    assigned = set(rbac_policy.get("user_roles", {}).get(subject.subject_id, []))
    return assigned | set(subject.roles)


def expand_role_hierarchy(roles: set, rbac_policy: dict) -> set:
    """Expand role inheritance transitively."""

    expanded = set(roles)
    hierarchy = rbac_policy.get("role_hierarchy", {})
    changed = True
    while changed:
        changed = False
        for role in list(expanded):
            for inherited in hierarchy.get(role, []):
                if inherited not in expanded:
                    expanded.add(inherited)
                    changed = True
    return expanded


def check_separation_of_duty(active_roles: set, rbac_policy: dict) -> bool:
    """Return True when no mutually exclusive role set is fully active."""

    for rule in rbac_policy.get("mutually_exclusive_roles", []):
        if set(rule).issubset(active_roles):
            return False
    return True


def collect_permissions(active_roles: set, rbac_policy: dict) -> set:
    """Collect (resource_id, action) permissions from roles."""

    permissions = set()
    for role in active_roles:
        for item in rbac_policy.get("role_permissions", {}).get(role, []):
            permissions.add((item["resource_id"], item["action"]))
    return permissions


def check_rbac_access(request, subjects: dict, resources: dict, rbac_policy: dict, active_roles: set):
    """Authorize by active RBAC roles."""

    if request.subject_id not in subjects:
        return AccessDecision(DENY, "UNKNOWN_SUBJECT", "rbac-default-deny")
    if request.resource_id not in resources:
        return AccessDecision(DENY, "UNKNOWN_RESOURCE", "rbac-default-deny")

    allowed_roles = get_user_roles(subjects[request.subject_id], rbac_policy)
    if not active_roles.issubset(allowed_roles):
        return AccessDecision(DENY, "RBAC_ROLE_NOT_ASSIGNED", "rbac-role-check")

    effective_roles = expand_role_hierarchy(active_roles, rbac_policy)
    if not check_separation_of_duty(effective_roles, rbac_policy):
        return AccessDecision(DENY, "RBAC_MUTUALLY_EXCLUSIVE_ROLES", "rbac-sod")

    permissions = collect_permissions(effective_roles, rbac_policy)
    if (request.resource_id, request.action) in permissions:
        return AccessDecision(PERMIT, "RBAC_PERMISSION_ALLOWED", "rbac-role-permission")
    return AccessDecision(DENY, "RBAC_PERMISSION_NOT_GRANTED", "rbac-default-deny")

