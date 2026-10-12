from models import AccessDecision, DENY, PERMIT


def build_access_matrix(subjects: dict, resources: dict, permissions: list) -> dict:
    """Build matrix[subject_id][resource_id] = set(actions)."""

    matrix = {
        subject_id: {resource_id: set() for resource_id in resources}
        for subject_id in subjects
    }
    for item in permissions:
        subject_id = item["subject_id"]
        resource_id = item["resource_id"]
        actions = set(item.get("actions", []))
        matrix.setdefault(subject_id, {}).setdefault(resource_id, set()).update(actions)
    return matrix


def check_matrix_access(request, matrix: dict):
    """Authorize a request by access matrix."""

    if request.subject_id not in matrix:
        return AccessDecision(DENY, "UNKNOWN_SUBJECT", "matrix-default-deny")
    known_resources = {resource_id for row in matrix.values() for resource_id in row}
    if request.resource_id not in known_resources:
        return AccessDecision(DENY, "UNKNOWN_RESOURCE", "matrix-default-deny")
    allowed_actions = matrix.get(request.subject_id, {}).get(request.resource_id, set())
    if request.action in allowed_actions:
        return AccessDecision(PERMIT, "MATRIX_ACTION_ALLOWED", "matrix-cell")
    return AccessDecision(DENY, "MATRIX_ACTION_NOT_GRANTED", "matrix-default-deny")


def update_matrix_permission(matrix: dict, subject_id: str, resource_id: str, action: str, effect: str):
    """Grant or revoke one matrix permission in memory."""

    actions = matrix.setdefault(subject_id, {}).setdefault(resource_id, set())
    if effect.lower() in {"grant", "permit", "allow"}:
        actions.add(action)
    elif effect.lower() in {"revoke", "deny", "remove"}:
        actions.discard(action)
    else:
        raise ValueError(f"unsupported matrix update effect: {effect}")
    return matrix

