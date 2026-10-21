from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any, Optional


@dataclass(frozen=True)
class Packet:
    """A simplified network packet / connection request."""

    src_ip: str
    dst_ip: str
    protocol: str
    src_port: Optional[int]
    dst_port: Optional[int]
    direction: str
    flags: Optional[str] = None


@dataclass(frozen=True)
class Rule:
    """Firewall rule used by the static packet-filtering engine."""

    rule_id: str
    priority: int
    src: str
    dst: str
    protocol: str
    src_port: str
    dst_port: str
    direction: str
    action: str
    log: bool
    description: str = ""


@dataclass(frozen=True)
class Decision:
    """Decision result for one packet."""

    action: str
    matched_rule: Optional[str]
    reason: str
    should_log: bool


@dataclass
class StateEntry:
    """One state-table entry for an allowed flow."""

    flow_key: tuple
    created_at: float = field(default_factory=time)
    last_seen: float = field(default_factory=time)
    timeout: int = 60
    meta: dict[str, Any] = field(default_factory=dict)


def packet_to_dict(packet: Packet) -> dict[str, Any]:
    return {
        "src_ip": packet.src_ip,
        "dst_ip": packet.dst_ip,
        "protocol": packet.protocol,
        "src_port": packet.src_port,
        "dst_port": packet.dst_port,
        "direction": packet.direction,
        "flags": packet.flags,
    }
