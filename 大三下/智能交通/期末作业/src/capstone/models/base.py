"""小模型输出的统一表示。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Signal:
    """一个小模型/知识源对当前场景的结构化贡献。

    name        : forecast / detection / dialog_rag
    risk        : 该信号映射出的风险分 [0,1]（越高越危险/越需关注）
    confidence  : 该信号自身的可信度 [0,1]（用于难例挖掘与加权）
    summary     : 给大模型/人看的简短结构化说明
    raw         : 原始结构化结果（落遥测用）
    """
    name: str
    risk: float
    confidence: float
    summary: str
    raw: dict[str, Any] = field(default_factory=dict)
    available: bool = True
