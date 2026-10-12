import json
from pathlib import Path

from models import Resource, Subject


def _read_json(path: str):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_subjects(path: str) -> dict:
    """Load subjects from a JSON file."""

    data = _read_json(path)
    return {
        item["subject_id"]: Subject(
            subject_id=item["subject_id"],
            groups=set(item.get("groups", [])),
            roles=set(item.get("roles", [])),
            attrs=item.get("attrs", {}),
        )
        for item in data
    }


def load_resources(path: str) -> dict:
    """Load resources from a JSON file."""

    data = _read_json(path)
    return {
        item["resource_id"]: Resource(
            resource_id=item["resource_id"],
            owner=item["owner"],
            resource_type=item["resource_type"],
            label=item.get("label"),
            attrs=item.get("attrs", {}),
        )
        for item in data
    }


def load_acl_policies(path: str) -> dict:
    """Load ACL policies from a JSON file."""

    return _read_json(path)


def load_rbac_policies(path: str) -> dict:
    """Load RBAC policies from a JSON file."""

    return _read_json(path)


def load_mac_policies(path: str) -> dict:
    """Load MAC policies from a JSON file."""

    return _read_json(path)


def load_abac_policies(path: str) -> list:
    """Load ABAC policies from a JSON file."""

    return _read_json(path)

