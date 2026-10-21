from __future__ import annotations

from time import time
from typing import Any

from common import Decision, Packet, StateEntry
from rule_engine import normalize_packet


def build_flow_key(packet: Packet) -> tuple:
    """Build a bidirectional five-tuple key for state-table lookup."""

    packet = normalize_packet(packet)
    endpoint_a = (packet.src_ip, packet.src_port)
    endpoint_b = (packet.dst_ip, packet.dst_port)
    first, second = sorted([endpoint_a, endpoint_b])
    return (first, second, packet.protocol)


def is_established(packet: Packet, state_table: dict[tuple, Any]) -> bool:
    """Check whether a packet belongs to an established allowed flow."""

    key = build_flow_key(packet)
    entry = state_table.get(key)
    if entry is None:
        return False

    now = time()
    last_seen = getattr(entry, "last_seen", now)
    timeout = getattr(entry, "timeout", 60)
    if now - last_seen > timeout:
        state_table.pop(key, None)
        return False

    entry.last_seen = now
    return True


def update_state_table(
    packet: Packet,
    decision: Decision,
    state_table: dict[tuple, Any],
    timeout: int = 60,
) -> None:
    """Create or refresh state for allowed TCP/UDP flows."""

    packet = normalize_packet(packet)
    if decision.action != "allow" or packet.protocol not in {"TCP", "UDP"}:
        return

    key = build_flow_key(packet)
    now = time()
    if key in state_table:
        state_table[key].last_seen = now
        return

    state_table[key] = StateEntry(
        flow_key=key,
        created_at=now,
        last_seen=now,
        timeout=timeout,
        meta={"direction": packet.direction, "rule": decision.matched_rule},
    )


def expire_state_entries(state_table: dict[tuple, Any], now: float) -> None:
    """Remove expired state-table entries in place."""

    expired = []
    for key, entry in state_table.items():
        last_seen = getattr(entry, "last_seen", now)
        timeout = getattr(entry, "timeout", 60)
        if now - last_seen > timeout:
            expired.append(key)

    for key in expired:
        state_table.pop(key, None)
