from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from common import Decision, Packet, Rule
from rule_engine import match_ip, match_port


def log_decision(packet: Packet, decision: Decision, log_store: list) -> None:
    """Append one firewall decision log record."""

    if not decision.should_log:
        return

    log_store.append(
        {
            "time": datetime.now().isoformat(timespec="seconds"),
            "src": packet.src_ip,
            "dst": packet.dst_ip,
            "protocol": packet.protocol.upper(),
            "src_port": packet.src_port,
            "dst_port": packet.dst_port,
            "direction": packet.direction.lower(),
            "action": decision.action,
            "rule": decision.matched_rule or "DEFAULT",
            "reason": decision.reason,
        }
    )


def detect_shadowed_rules(rules: list[Rule]) -> list:
    """Detect rules that may never be reached because an earlier rule covers them."""

    shadowed = []
    ordered = sorted(enumerate(rules), key=lambda item: (item[1].priority, item[0]))
    for index, (_, rule) in enumerate(ordered):
        previous_rules = [item[1] for item in ordered[:index]]
        if any(_covers(prev, rule) for prev in previous_rules):
            shadowed.append(rule.rule_id)
    return shadowed


def detect_conflicting_rules(rules: list[Rule]) -> list:
    """Detect overlapping rules with different actions."""

    conflicts = []
    for i, left in enumerate(rules):
        for right in rules[i + 1 :]:
            if left.action.lower() == right.action.lower():
                continue
            if _overlaps(left, right):
                conflicts.append((left.rule_id, right.rule_id))
    return conflicts


def summarize_logs(log_store: list) -> dict:
    """Summarize allow/deny/default decisions and rule hit counts."""

    action_counts = Counter(item["action"] for item in log_store)
    rule_counts = Counter(item["rule"] for item in log_store)
    return {
        "total": len(log_store),
        "allow": action_counts.get("allow", 0),
        "deny": action_counts.get("deny", 0),
        "default": rule_counts.get("DEFAULT", 0),
        "rule_hits": dict(rule_counts),
    }


def _covers(left: Rule, right: Rule) -> bool:
    return (
        _field_covers(left.src, right.src, "ip")
        and _field_covers(left.dst, right.dst, "ip")
        and _field_covers(left.protocol, right.protocol, "text")
        and _field_covers(left.src_port, right.src_port, "port")
        and _field_covers(left.dst_port, right.dst_port, "port")
        and _field_covers(left.direction, right.direction, "text")
    )


def _overlaps(left: Rule, right: Rule) -> bool:
    return (
        _field_overlaps(left.src, right.src, "ip")
        and _field_overlaps(left.dst, right.dst, "ip")
        and _field_overlaps(left.protocol, right.protocol, "text")
        and _field_overlaps(left.src_port, right.src_port, "port")
        and _field_overlaps(left.dst_port, right.dst_port, "port")
        and _field_overlaps(left.direction, right.direction, "text")
    )


def _field_covers(left: str, right: str, kind: str) -> bool:
    left = str(left).lower()
    right = str(right).lower()
    if left in {"*", "any"}:
        return True
    if kind == "text":
        return left == right
    if kind == "port":
        sample = _port_sample(right)
        return sample is not None and match_port(left, sample)
    if kind == "ip":
        sample = _ip_sample(right)
        return sample is not None and match_ip(left, sample)
    return False


def _field_overlaps(left: str, right: str, kind: str) -> bool:
    return _field_covers(left, right, kind) or _field_covers(right, left, kind)


def _port_sample(pattern: str) -> int | None:
    pattern = str(pattern).lower()
    if pattern in {"*", "any"}:
        return 0
    if "," in pattern:
        return _port_sample(pattern.split(",", 1)[0])
    if "-" in pattern:
        return int(pattern.split("-", 1)[0])
    try:
        return int(pattern)
    except ValueError:
        return None


def _ip_sample(pattern: str) -> str | None:
    pattern = str(pattern).lower()
    if pattern in {"*", "any"}:
        return "0.0.0.0"
    if "," in pattern:
        return _ip_sample(pattern.split(",", 1)[0])
    if "/" in pattern:
        return pattern.split("/", 1)[0]
    return pattern
