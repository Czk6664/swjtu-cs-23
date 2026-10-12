# Firewall Lab Notes

This directory contains a runnable implementation for experiment 7.

Run:

```powershell
python main.py
```

Implemented modules:

- `common.py`: packet, rule, decision and state-table data structures.
- `rule_engine.py`: normalization, IP matching, port matching and first-match rule evaluation.
- `stateful_firewall.py`: bidirectional flow-key building, established-flow lookup and timeout cleanup.
- `nat_module.py`: SNAT, DNAT and NAT mapping recording helpers.
- `policy_audit.py`: decision logging, shadowed-rule detection, conflict detection and log summary.
- `test_cases.py`: eight traffic cases for the experiment verification table.
- `main.py`: experiment entry point and console report.
