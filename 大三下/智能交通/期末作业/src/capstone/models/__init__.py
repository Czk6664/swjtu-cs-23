"""小模型适配器层：把三个大作业的产物统一成 Signal，供编排层融合。

设计原则：编排逻辑与具体模型解耦——换 checkpoint / 换实现只动适配器，不动 fusion/decision。
"""
from .base import Signal  # noqa: F401
from .forecast import ForecastAdapter  # noqa: F401
from .detection import DetectionAdapter  # noqa: F401
from .dialog_rag import DialogRagAdapter  # noqa: F401
