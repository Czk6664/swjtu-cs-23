from __future__ import annotations

from dataclasses import replace
from ipaddress import ip_address, ip_network
from typing import Optional

from common import Decision, Packet, Rule


def normalize_packet(packet: Packet) -> Packet:
    """Normalize protocol, direction and TCP/UDP port types."""

    protocol = packet.protocol.upper()
    direction = packet.direction.lower()
    flags = packet.flags.upper() if packet.flags else None
    return replace(
        packet,
        protocol=protocol,
        direction=direction,
        src_port=_normalize_optional_port(packet.src_port),
        dst_port=_normalize_optional_port(packet.dst_port),
        flags=flags,
    )


def match_ip(pattern: str, ip: str) -> bool:
    """Match exact IP, CIDR network, comma list or wildcard."""

    pattern = (pattern or "*").strip()
    if pattern in {"*", "any", "ANY"}:
        return True

    if "," in pattern:
        return any(match_ip(part.strip(), ip) for part in pattern.split(","))

    try:
        if "/" in pattern:
            return ip_address(ip) in ip_network(pattern, strict=False)
        return ip_address(ip) == ip_address(pattern)
    except ValueError:
        return pattern == ip


def match_port(pattern: str, port: Optional[int]) -> bool:
    """Match a single port, a range such as 1000-2000, list, or wildcard."""

    pattern = str(pattern or "*").strip().lower()
    if pattern in {"*", "any"}:
        return True
    if port is None:
        return pattern in {"none", "null", "-"}
    if "," in pattern:
        return any(match_port(part.strip(), port) for part in pattern.split(","))
    if "-" in pattern:
        start, end = pattern.split("-", 1)
        return int(start) <= port <= int(end)
    return int(pattern) == port


def match_rule(packet: Packet, rule: Rule) -> bool:
    """Return True if the packet matches all five-tuple and direction fields."""

    packet = normalize_packet(packet)
    return (
        match_ip(rule.src, packet.src_ip)
        and match_ip(rule.dst, packet.dst_ip)
        and _match_text(rule.protocol, packet.protocol)
        and match_port(rule.src_port, packet.src_port)
        and match_port(rule.dst_port, packet.dst_port)
        and _match_text(rule.direction, packet.direction)
    )


def evaluate_rules(packet: Packet, rules: list[Rule], default_action: str) -> Decision:
    """Evaluate rules by priority first, then original rule order."""

    ordered = sorted(enumerate(rules), key=lambda item: (item[1].priority, item[0]))
    for _, rule in ordered:
        if match_rule(packet, rule):
            return Decision(
                action=rule.action.lower(),
                matched_rule=rule.rule_id,
                reason=f"matched {rule.rule_id}: {rule.description or 'no description'}",
                should_log=rule.log,
            )

    action = default_action.lower()
    return Decision(
        action=action,
        matched_rule=None,
        reason=f"default policy: {action}",
        should_log=True,
    )


def _match_text(pattern: str, value: str) -> bool:
    pattern = str(pattern or "*").strip().lower()
    return pattern in {"*", "any"} or pattern == value.lower()


def _normalize_optional_port(port: Optional[int]) -> Optional[int]:
    if port is None:
        return None
    port = int(port)
    if not 0 <= port <= 65535:
        raise ValueError(f"invalid port: {port}")
    return port
