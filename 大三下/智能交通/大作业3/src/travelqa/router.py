"""意图路由: 把用户问题分到一种意图，决定调用哪条小模型/工具/知识库。

原型用关键词规则分类(轻量、可解释)。生产可换成大模型 function-calling 或微调分类头,
接口保持 classify(query) -> Intent 不变。
"""
from __future__ import annotations

import re
from enum import Enum


class Intent(str, Enum):
    TRAFFIC_INFO = "traffic-info"      # 交管信息问答 (RAG)
    WEATHER = "weather"                # 天气问答
    TRAVEL_ADVICE = "travel-advice"    # 出行建议 (RAG + 工具)
    ROUTE = "route"                    # 出行路径规划
    FORECAST = "forecast"              # 高阶: 交通流预测问答 (大作业1)
    DETECTION = "detection"            # 高阶: 交通目标识别理解问答 (大作业2)


_RULES: list[tuple[Intent, list[str]]] = [
    (Intent.ROUTE, ["怎么去", "怎么走", "路线", "路径", "导航", "到.*多久", "去.*坐什么", "坐什么"]),
    (Intent.FORECAST, ["流量预测", "交通流", "预测", "未来.*车流", "拥堵预测", "rmse", "mae", "staeformer"]),
    (Intent.DETECTION, ["识别", "检测", "标志", "标牌", "yolo", "tt100k", "限速标志", "类别", "map"]),
    (Intent.WEATHER, ["天气", "气温", "温度", "降水", "穿什么", "会不会下雨", "下不下雨"]),
    # 强领域信号(限行/违章/违法...)优先于泛化的建议类动词(处理/如何)
    (Intent.TRAFFIC_INFO, ["限行", "尾号", "违章", "违法", "电子警察", "管制", "施工", "处罚", "复核"]),
    (Intent.TRAVEL_ADVICE, ["建议", "注意", "怎么办", "怎么处理", "应该", "事故", "快处",
                            "处理", "剐蹭", "刮蹭", "追尾"]),
]


def classify(query: str) -> Intent:
    q = query.lower()
    for intent, patterns in _RULES:
        for pat in patterns:
            if re.search(pat, q):
                return intent
    # 默认走交管信息 RAG —— 它有兜底的『无依据则说明』能力
    return Intent.TRAFFIC_INFO


def extract_route_od(query: str) -> tuple[str, str]:
    """从『从A到B / A去B / A到B』里粗抽起终点。抽不到则给占位。"""
    m = re.search(r"从(.+?)到(.+?)(?:怎么|坐|开车|$)", query)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    m = re.search(r"(.+?)(?:去|到)(.+?)(?:怎么|坐|开车|$)", query)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "当前位置", "目的地"
