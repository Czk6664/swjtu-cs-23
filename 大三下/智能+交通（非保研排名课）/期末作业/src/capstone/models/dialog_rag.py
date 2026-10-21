"""大作业3 对话/RAG 适配器（复用 travelqa.TravelQAApp）。

在决策系统里它有两个角色：
1. 知识源：对场景相关问题做 RAG 检索，给融合层提供"是否有相关管控规定/出行建议"的知识信号。
2. 对话出口：把最终决策用自然语言解释给用户（在 decision 层调用其 LLM provider）。
"""
from __future__ import annotations

from .base import Signal


class DialogRagAdapter:
    name = "dialog_rag"

    def __init__(self, cfg):
        from travelqa.app import TravelQAApp
        from travelqa.config import Config as TqaConfig
        self.app = TravelQAApp(TqaConfig.load())

    def infer(self, scene: dict) -> Signal:
        query = scene.get("query") or scene.get("context") or "该路段有何交通管制或出行注意事项？"
        if not self.app.retriever.ready():
            return Signal(self.name, risk=0.0, confidence=0.0,
                          summary="知识库未构建(先跑大作业3 build_kb)", raw={}, available=False)
        hits = self.app.retriever.retrieve(query)
        top = hits[0].score if hits else 0.0
        # 知识"风险"：检索到管控/限行类知识 → 提示有管制，轻微抬高关注度
        risky_kw = any(k in h.text for h in hits for k in ("限行", "管制", "施工", "事故"))
        risk = 0.4 if risky_kw else 0.1
        return Signal(
            self.name, risk=risk, confidence=round(float(top), 3),
            summary=(f"RAG 命中 {len(hits)} 条(top={top:.2f}); "
                     + ("含管控/限行相关知识" if risky_kw else "无强管控提示")),
            raw={"query": query, "hits": [{"title": h.title, "score": h.score,
                                           "url": h.url} for h in hits]},
            available=bool(hits))

    def explain(self, query: str, evidence: str) -> str:
        """用大作业3 的 LLM provider 生成自然语言解释（offline 时为模板）。"""
        return self.app.llm.generate(
            "你是成都智能交通决策助手，基于以下依据用简洁中文解释决策理由。\n" + evidence, query)
