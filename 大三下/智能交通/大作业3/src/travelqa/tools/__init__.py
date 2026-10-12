"""外部/结构化工具: 天气、路径规划，以及高阶要求的大作业1预测、大作业2检测接入。"""
from .weather import weather_query  # noqa: F401
from .route import route_plan  # noqa: F401
from .forecast import ForecastTool  # noqa: F401
from .detection import DetectionTool  # noqa: F401
