from __future__ import annotations

from common import Packet, Rule
from policy_audit import log_decision, summarize_logs
from rule_engine import evaluate_rules, normalize_packet
from stateful_firewall import is_established, update_state_table


DEFAULT_ACTION = "deny"


def build_packet_case(case_id: str, description: str = "") -> Packet:
    """Build traffic for the lab verification table."""

    cases = {
        "TC-01": Packet("10.0.1.10", "198.51.100.20", "tcp", 53000, 80, "outbound", "SYN"),
        "TC-02": Packet("198.51.100.20", "10.0.1.10", "tcp", 80, 53000, "inbound", "ACK"),
        "TC-03": Packet("203.0.113.8", "10.0.1.10", "tcp", 44000, 22, "inbound", "SYN"),
        "TC-04": Packet("203.0.113.8", "203.0.113.10", "tcp", 44000, 443, "inbound", "SYN"),
        "TC-05": Packet("10.0.1.10", "203.0.113.10", "tcp", 53001, 443, "outbound", "SYN"),
        "TC-06": Packet("10.0.1.10", "198.51.100.53", "udp", 53002, 53, "outbound"),
        "TC-07": Packet("10.0.1.10", "198.51.100.20", "icmp", None, None, "outbound"),
        "TC-08": Packet("203.0.113.8", "10.0.2.30", "tcp", 44000, 3306, "inbound", "SYN"),
    }
    try:
        return normalize_packet(cases[case_id])
    except KeyError as exc:
        raise ValueError(f"unknown case id: {case_id} {description}".strip()) from exc


def run_test_case(packet: Packet, rules: list[Rule], state_table: dict) -> dict:
    """Run a single packet through stateful lookup and static rule matching."""

    logs = []
    if is_established(packet, state_table):
        from common import Decision

        decision = Decision("allow", "STATE", "matched established state", True)
    else:
        decision = evaluate_rules(packet, rules, DEFAULT_ACTION)
        update_state_table(packet, decision, state_table)

    log_decision(packet, decision, logs)
    return {
        "packet": packet,
        "action": decision.action,
        "matched_rule": decision.matched_rule or "DEFAULT",
        "reason": decision.reason,
        "logged": bool(logs),
        "logs": logs,
    }


def run_test_suite(cases: list, rules: list[Rule]) -> list:
    """Run a batch of test cases and preserve state across the suite."""

    state_table = {}
    results = []
    for case in cases:
        packet = case if isinstance(case, Packet) else build_packet_case(str(case))
        result = run_test_case(packet, rules, state_table)
        result["state_size"] = len(state_table)
        results.append(result)
    return results


def collect_logs(results: list[dict]) -> list[dict]:
    logs = []
    for result in results:
        logs.extend(result.get("logs", []))
    return logs


def summarize_results(results: list[dict]) -> dict:
    return summarize_logs(collect_logs(results))
