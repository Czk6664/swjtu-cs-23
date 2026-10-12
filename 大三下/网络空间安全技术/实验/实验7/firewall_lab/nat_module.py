from __future__ import annotations

from dataclasses import replace

from common import Packet
from rule_engine import match_ip, match_port, normalize_packet


def apply_snat(packet: Packet, snat_rules: list) -> Packet:
    """Apply source NAT rules to a packet."""

    packet = normalize_packet(packet)
    for rule in snat_rules:
        if _nat_rule_matches(packet, rule, "src"):
            return replace(
                packet,
                src_ip=rule.get("to_ip", packet.src_ip),
                src_port=rule.get("to_port", packet.src_port),
            )
    return packet


def apply_dnat(packet: Packet, dnat_rules: list) -> Packet:
    """Apply destination NAT / port-forwarding rules to a packet."""

    packet = normalize_packet(packet)
    for rule in dnat_rules:
        if _nat_rule_matches(packet, rule, "dst"):
            return replace(
                packet,
                dst_ip=rule.get("to_ip", packet.dst_ip),
                dst_port=rule.get("to_port", packet.dst_port),
            )
    return packet


def record_nat_mapping(
    original_packet: Packet,
    translated_packet: Packet,
    nat_table: dict,
) -> None:
    """Record NAT mapping so return traffic and logs can be traced."""

    original = (
        original_packet.src_ip,
        original_packet.src_port,
        original_packet.dst_ip,
        original_packet.dst_port,
        original_packet.protocol.upper(),
    )
    translated = (
        translated_packet.src_ip,
        translated_packet.src_port,
        translated_packet.dst_ip,
        translated_packet.dst_port,
        translated_packet.protocol.upper(),
    )
    nat_table[translated] = {"original": original, "translated": translated}


def _nat_rule_matches(packet: Packet, rule: dict, side: str) -> bool:
    src_pattern = rule.get("src", "*")
    dst_pattern = rule.get("dst", "*")
    direction = str(rule.get("direction", "*")).lower()
    protocol = str(rule.get("protocol", "*")).upper()
    port_pattern = str(rule.get(f"{side}_port", "*"))
    port_value = packet.src_port if side == "src" else packet.dst_port

    return (
        match_ip(src_pattern, packet.src_ip)
        and match_ip(dst_pattern, packet.dst_ip)
        and match_port(port_pattern, port_value)
        and (direction in {"*", "any"} or direction == packet.direction)
        and (protocol in {"*", "ANY"} or protocol == packet.protocol)
    )
