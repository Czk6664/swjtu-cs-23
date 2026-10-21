from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set


PERMIT = "Permit"
DENY = "Deny"


@dataclass
class Subject:
    """Access subject."""

    subject_id: str
    groups: Set[str] = field(default_factory=set)
    roles: Set[str] = field(default_factory=set)
    attrs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Resource:
    """Protected resource."""

    resource_id: str
    owner: str
    resource_type: str
    label: Optional[str] = None
    attrs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessRequest:
    """One authorization request."""

    subject_id: str
    resource_id: str
    action: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessDecision:
    """Authorization result."""

    effect: str
    reason: str
    matched_policy: Optional[str] = None

