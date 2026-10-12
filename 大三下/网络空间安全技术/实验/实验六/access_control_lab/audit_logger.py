import json
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def create_audit_record(request, decision, model_name: str, extra: dict = None) -> dict:
    """Create one audit log record."""

    record = {
        "time": datetime.now(timezone.utc).isoformat(),
        "request_id": str(uuid.uuid4()),
        "subject": request.subject_id,
        "resource": request.resource_id,
        "action": request.action,
        "model": model_name,
        "decision": decision.effect,
        "reason": decision.reason,
        "matched_policy": decision.matched_policy,
    }
    if extra:
        record["extra"] = extra
    return record


def write_audit_log(record: dict, path: str):
    """Append one JSONL audit record."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def summarize_audit_log(path: str) -> dict:
    """Summarize decisions, deny reasons, sensitive access, and repeat failures."""

    records = []
    target = Path(path)
    if not target.exists():
        return {}
    with target.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    decisions = Counter(item["decision"] for item in records)
    deny_reasons = Counter(item["reason"] for item in records if item["decision"] == "Deny")
    sensitive_ids = {"payroll", "strategy_doc"}
    sensitive_count = sum(1 for item in records if item["resource"] in sensitive_ids)
    failures = Counter(item["subject"] for item in records if item["decision"] == "Deny")
    repeat_failures = {subject: count for subject, count in failures.items() if count >= 2}

    return {
        "total_requests": len(records),
        "permit_requests": decisions.get("Permit", 0),
        "deny_requests": decisions.get("Deny", 0),
        "most_common_deny_reason": deny_reasons.most_common(1)[0][0] if deny_reasons else "",
        "sensitive_resource_access_count": sensitive_count,
        "repeat_failed_subjects": repeat_failures,
        "deny_reason_counts": dict(deny_reasons),
    }

