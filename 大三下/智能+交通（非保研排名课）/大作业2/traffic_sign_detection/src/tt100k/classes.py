from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ClassSpec:
    source_name: str
    target_name: str


DEFAULT_CLASS_SPECS: List[ClassSpec] = [
    ClassSpec("pn", "tt100k_pn"),
    ClassSpec("pne", "tt100k_pne"),
    ClassSpec("i5", "tt100k_i5"),
    ClassSpec("p11", "tt100k_p11"),
    ClassSpec("pl40", "tt100k_pl40"),
    ClassSpec("pl50", "tt100k_pl50"),
    ClassSpec("pl80", "tt100k_pl80"),
    ClassSpec("p26", "tt100k_p26"),
    ClassSpec("pl60", "tt100k_pl60"),
    ClassSpec("i4", "tt100k_i4"),
    ClassSpec("pl100", "tt100k_pl100"),
    ClassSpec("pl30", "tt100k_pl30"),
]


def get_class_names() -> List[str]:
    return [spec.target_name for spec in DEFAULT_CLASS_SPECS]


def get_source_to_index() -> Dict[str, int]:
    return {spec.source_name: index for index, spec in enumerate(DEFAULT_CLASS_SPECS)}


def get_source_to_target() -> Dict[str, str]:
    return {spec.source_name: spec.target_name for spec in DEFAULT_CLASS_SPECS}
