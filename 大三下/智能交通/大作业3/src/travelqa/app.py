"""端到端编排器 —— 大小模型协同的核心。

流程: 问题 -> 路由意图 -> (RAG 检索 / 调用小模型工具) -> 汇总证据 ->
       大模型组织带来源的回答。

小模型(专才)只产出结构化结果(检索片段、预测指标、检测类别/精度)，
大模型(通才)负责融合这些证据并用自然语言解释——这就是大小模型协同。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import Config
from .llm import get_llm
from .rag import Retriever
from .router import Intent, classify, extract_route_od
from .tools import DetectionTool, ForecastTool, route_plan, weather_query

_SYSTEM_BASE = (
    "你是成都『智能交通出行问答』助手。基于下方提供的依据/工具结果作答，"
    "做到准确、简洁、可溯源；信息不足时明确说明并建议查阅官方发布，不要编造。"
)


@dataclass
class Answer:
    intent: str
    text: str
    evidence: str = ""
    sources: list[dict] = field(default_factory=list)
    tool_result: dict | None = None


class TravelQAApp:
    def __init__(self, cfg: Config | None = None):
        self.cfg = cfg or Config.load()
        self.llm = get_llm(self.cfg)
        self.retriever = Retriever(self.cfg)
        self.forecast = ForecastTool(self.cfg)
        self.detection = DetectionTool(self.cfg)

    def ask(self, query: str) -> Answer:
        intent = classify(query)
        handler = {
            Intent.TRAFFIC_INFO: self._rag,
            Intent.TRAVEL_ADVICE: self._rag,
            Intent.WEATHER: self._weather,
            Intent.ROUTE: self._route,
            Intent.FORECAST: self._forecast,
            Intent.DETECTION: self._detection,
        }[intent]
        return handler(query, intent)

    # --- RAG 类意图 (交管信息 / 出行建议) ----------------------------------
    def _rag(self, query: str, intent: Intent) -> Answer:
        hits = self.retriever.retrieve(query)
        evidence = self.retriever.build_evidence(hits)
        if not hits:
            text = (
                "当前知识库未检索到与该问题相关的可核验依据。"
                "请查阅成都市公安局交通管理局最新公告或官方交通服务。"
            )
        else:
            text = self.llm.generate(_SYSTEM_BASE + "\n\n" + evidence, query).strip()
            if not text:
                text = "已检索到相关依据，但回答生成暂时不可用。请查看下方来源链接核验。"
        return Answer(intent=intent.value, text=text, evidence=evidence,
                      sources=[{"title": h.title, "url": h.url, "fetched_at": h.fetched_at,
                                "published_at": h.published_at}
                               for h in hits])

    # --- 天气 -------------------------------------------------------------
    def _weather(self, query: str, intent: Intent) -> Answer:
        date = "后天" if "后天" in query else "明天" if "明天" in query else "今天"
        wx = weather_query(self.cfg, date=date)
        evidence = f"天气工具结果: {wx}"
        text = self.llm.generate(_SYSTEM_BASE + "\n\n" + evidence, query).strip()
        if not text:
            text = _weather_fallback(wx)
        return Answer(intent=intent.value, text=text, evidence=evidence, tool_result=wx)

    # --- 路径规划 ---------------------------------------------------------
    def _route(self, query: str, intent: Intent) -> Answer:
        origin, dest = extract_route_od(query)
        rp = route_plan(self.cfg, origin, dest)
        evidence = f"路径规划工具结果: {rp}"
        text = self.llm.generate(_SYSTEM_BASE + "\n\n" + evidence, query).strip()
        if not text:
            text = _route_fallback(rp)
        return Answer(intent=intent.value, text=text, evidence=evidence, tool_result=rp)

    # --- 高阶: 交通流预测问答 (大作业1) -----------------------------------
    def _forecast(self, query: str, intent: Intent) -> Answer:
        if any(word in query for word in ("未来", "接下来", "下一小时", "后续", "车流量", "流量")):
            fc = self.forecast.predict()
        else:
            fc = self.forecast.summarize()
        evidence = f"交通流预测模型(大作业1 STAEformer)结果: {fc}"
        text = self.llm.generate(_SYSTEM_BASE + "\n\n" + evidence, query)
        return Answer(intent=intent.value, text=text, evidence=evidence, tool_result=fc)

    # --- 高阶: 交通目标识别理解问答 (大作业2) -----------------------------
    def _detection(self, query: str, intent: Intent) -> Answer:
        det = self.detection.summarize()
        evidence = f"交通目标识别模型(大作业2 YOLO/TT100K)结果: {det}"
        text = self.llm.generate(_SYSTEM_BASE + "\n\n" + evidence, query)
        return Answer(intent=intent.value, text=text, evidence=evidence, tool_result=det)


def _weather_fallback(wx: dict) -> str:
    if not wx.get("available"):
        return f"天气工具暂未返回可用结果：{wx.get('error', '原因未知')}。请稍后重试。"
    condition = wx.get("condition") or (
        f"{wx.get('day_condition', '')}转{wx.get('night_condition', '')}".strip("转")
    )
    temperature = wx.get("temperature_c")
    if temperature not in (None, ""):
        temperature_text = f"{temperature}℃"
    else:
        low, high = (wx.get("temperature_range_c") or wx.get("temp_range_c") or ["", ""])[:2]
        temperature_text = f"{low}℃至{high}℃" if low or high else "温度数据暂缺"
    advice = "天气条件总体适合驾车。"
    if any(word in condition for word in ("雨", "雪", "雾", "霾")):
        advice = "驾车时请降低车速、保持车距，并留意路面和能见度变化。"
    return (
        f"{wx.get('city', '成都')}{wx.get('date', '当前')}天气为{condition or '未知'}，"
        f"气温{temperature_text}，{wx.get('wind', '风力数据暂缺')}。{advice}"
        f"数据更新时间：{wx.get('reported_at', '未知')}。"
    )


def _route_fallback(route: dict) -> str:
    if not route.get("available"):
        return f"路径规划工具暂未返回可用结果：{route.get('error', '原因未知')}。请稍后重试。"
    plan = route.get("plan") or {}
    return (
        f"从{route.get('origin', '起点')}到{route.get('destination', '终点')}驾车约"
        f"{route.get('distance_km', plan.get('distance_km', '未知'))}公里，预计"
        f"{route.get('duration_min', plan.get('duration_min', '未知'))}分钟。"
        "实际耗时会随实时路况变化，出发前请再次查看导航。"
    )
