"""capstone —— 大小模型协同的智能交通管理决策系统 (期末作业).

整合三个大作业，聚焦两个核心新增：
    orchestration/  决策融合：把小模型(预测/检测)结构化输出 + RAG 知识融合成
                    带风险等级与可解释理由的决策。
    flywheel/       数据飞轮：采集→难例挖掘→标注→重训→门控晋升→监控的闭环，
                    让小模型与知识库"越用越准"，且可观测、可回滚。

复用：
    大作业1 STAEformer 预测结果、大作业2 YOLO 检测结果、
    大作业3 travelqa(意图路由 / RAG / LLM provider / 工具)。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 复用大作业3 的 travelqa 包（按路径引用，不拷贝代码）。
_DZ3_SRC = Path(__file__).resolve().parents[2].parent / "大作业3" / "src"
if _DZ3_SRC.exists() and str(_DZ3_SRC) not in sys.path:
    sys.path.insert(0, str(_DZ3_SRC))

__version__ = "0.1.0"
