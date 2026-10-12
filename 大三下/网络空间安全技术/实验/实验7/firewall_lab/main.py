from __future__ import annotations

import csv
from pathlib import Path

from common import Rule
from policy_audit import detect_conflicting_rules, detect_shadowed_rules, summarize_logs
from test_cases import collect_logs, run_test_suite


def load_policy(policy_path: str) -> list[Rule]:
    """Read a CSV policy file and convert it to Rule objects."""

    path = Path(policy_path)
    if not path.exists():
        return build_default_policy()

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = csv.DictReader(file)
        return [
            Rule(
                rule_id=row["rule_id"],
                priority=int(row.get("priority", "100")),
                src=row.get("src", "*"),
                dst=row.get("dst", "*"),
                protocol=row.get("protocol", "*"),
                src_port=row.get("src_port", "*"),
                dst_port=row.get("dst_port", "*"),
                direction=row.get("direction", "*"),
                action=row.get("action", "deny").lower(),
                log=row.get("log", "true").lower() in {"1", "true", "yes", "y"},
                description=row.get("description", ""),
            )
            for row in rows
        ]


def build_default_policy() -> list[Rule]:
    """Default lab policy used when no CSV file is provided."""

    return [
        Rule("R-01", 10, "10.0.1.0/24", "*", "tcp", "*", "80,443", "outbound", "allow", True, "internal users may browse web services"),
        Rule("R-02", 20, "10.0.1.0/24", "*", "udp", "*", "53", "outbound", "allow", True, "internal DNS queries are allowed"),
        Rule("R-03", 30, "*", "203.0.113.10", "tcp", "*", "443", "inbound", "allow", True, "publish DMZ HTTPS service"),
        Rule("R-04", 40, "*", "10.0.1.0/24", "tcp", "*", "22", "inbound", "deny", True, "block external SSH to internal hosts"),
        Rule("R-05", 50, "*", "10.0.2.0/24", "*", "*", "*", "inbound", "deny", True, "block direct access to database subnet"),
    ]


def run_firewall_experiment() -> list[dict]:
    """Main experiment entry: load rules, generate packets, evaluate and report."""

    rules = load_policy("policy.csv")
    cases = [f"TC-{index:02d}" for index in range(1, 9)]
    results = run_test_suite(cases, rules)
    logs = collect_logs(results)
    audit_summary = summarize_logs(logs)
    audit_summary["shadowed_rules"] = detect_shadowed_rules(rules)
    audit_summary["conflicting_rules"] = detect_conflicting_rules(rules)
    print_experiment_summary(results, audit_summary)
    return results


def print_experiment_summary(results: list, audit_summary: dict) -> None:
    """Print a concise lab report."""

    print("=== Firewall Lab Result ===")
    print("case   src -> dst                 proto sport dport dir       action rule")
    for index, result in enumerate(results, start=1):
        packet = result["packet"]
        print(
            f"TC-{index:02d}  "
            f"{packet.src_ip}:{packet.src_port or '-'} -> {packet.dst_ip}:{packet.dst_port or '-'}  "
            f"{packet.protocol:<5} {packet.direction:<8} "
            f"{result['action']:<5} {result['matched_rule']}"
        )

    print("\n=== Audit Summary ===")
    print(f"total logs: {audit_summary['total']}")
    print(f"allow: {audit_summary['allow']} deny: {audit_summary['deny']} default: {audit_summary['default']}")
    print(f"rule hits: {audit_summary['rule_hits']}")
    print(f"shadowed rules: {audit_summary['shadowed_rules'] or 'none'}")
    print(f"conflicting rules: {audit_summary['conflicting_rules'] or 'none'}")


if __name__ == "__main__":
    run_firewall_experiment()
