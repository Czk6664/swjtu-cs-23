from models import AccessDecision, DENY, PERMIT

from abac_model import check_abac_access
from acl_model import check_acl_access
from mac_model import check_mac_access
from matrix_model import check_matrix_access
from rbac_model import check_rbac_access


def authorize(request, model_name: str, subjects: dict, resources: dict, policies: dict, **kwargs):
    """Unified authorization entrypoint."""

    if model_name == "matrix":
        return check_matrix_access(request, policies["matrix"])
    if model_name == "acl":
        return check_acl_access(request, subjects, resources, policies["acl"])
    if model_name == "rbac":
        return check_rbac_access(
            request,
            subjects,
            resources,
            policies["rbac"],
            active_roles=set(kwargs.get("active_roles", set())),
        )
    if model_name == "mac":
        return check_mac_access(request, subjects, resources, policies["mac"])
    if model_name == "abac":
        return check_abac_access(
            request,
            subjects,
            resources,
            policies["abac"],
            kwargs.get("combining_alg", "deny_overrides"),
        )
    raise ValueError(f"unsupported model_name: {model_name}")


def combine_decisions(decisions: list, algorithm: str):
    """Combine decisions from models or policies."""

    if not decisions:
        return AccessDecision(DENY, "NO_DECISION_DEFAULT_DENY", "combiner")
    if algorithm == "deny_overrides":
        for decision in decisions:
            if decision.effect == DENY:
                return AccessDecision(DENY, "COMBINE_DENY_OVERRIDES", decision.matched_policy)
        return AccessDecision(PERMIT, "COMBINE_ALL_PERMIT", decisions[0].matched_policy)
    if algorithm == "permit_overrides":
        for decision in decisions:
            if decision.effect == PERMIT:
                return AccessDecision(PERMIT, "COMBINE_PERMIT_OVERRIDES", decision.matched_policy)
        return AccessDecision(DENY, "COMBINE_ALL_DENY", decisions[0].matched_policy)
    if algorithm == "first_applicable":
        first = decisions[0]
        return AccessDecision(first.effect, "COMBINE_FIRST_APPLICABLE", first.matched_policy)
    raise ValueError(f"unsupported combination algorithm: {algorithm}")


def explain_decision(request, decision) -> str:
    """Return a short human-readable explanation."""

    return (
        f"{request.subject_id} -> {request.resource_id} {request.action}: "
        f"{decision.effect}, reason={decision.reason}, policy={decision.matched_policy}"
    )

