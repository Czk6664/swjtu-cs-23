"""RAG 检索 + 证据组织。

检索策略: Hybrid Search（向量 + BM25 关键词）→ 可选 Reranker 重排序。
始终保留来源(标题/URL/抓取时间)，让回答可溯源、可验证。
"""
from __future__ import annotations

import re

from .kb.embed import get_embedder, get_reranker
from .kb.store import VectorStore

_CHINESE_RE = re.compile(r"[\u4e00-\u9fff]+")
_ASCII_RE = re.compile(r"[a-zA-Z0-9]+")
_STOP_TERMS = {
    "成都", "怎么", "如何", "是否", "什么", "规定", "请问", "一下", "最近",
    "今天", "当前", "可以", "需要", "交通", "关于",
}
_IGNORED_TERM_CHARS = set("的了吗呢啊吧怎么如何是否什么规定请问一下最近今天当前可以需要关于成都")


def _query_terms(query: str) -> set[str]:
    terms = {
        text[i:i + 2]
        for text in _CHINESE_RE.findall(query)
        for i in range(len(text) - 1)
        if not any(char in _IGNORED_TERM_CHARS for char in text[i:i + 2])
    }
    terms.update(token.lower() for token in _ASCII_RE.findall(query) if len(token) >= 2)
    return {term for term in terms if term not in _STOP_TERMS}


def _is_relevant(query: str, hit) -> bool:
    terms = _query_terms(query)
    if not terms:
        return True
    haystack = f"{hit.title}\n{hit.text}".lower()
    return any(term in haystack for term in terms)


class Retriever:
    def __init__(self, cfg):
        self.cfg = cfg
        self.embedder = get_embedder(cfg)
        self.reranker = get_reranker(cfg)
        kb_dir = cfg.resolve_path(cfg.get("paths", "kb_dir", default="data/kb"))
        self.store = VectorStore.load(kb_dir)
        expected_provider = cfg.get("embedding", "provider", default="offline_hash")
        if len(self.store) and self.store.embedding_provider != expected_provider:
            raise RuntimeError(
                "知识库向量与当前 embedding provider 不一致。"
                "请先运行 python scripts/2_build_kb.py 重新构建知识库。"
            )

        self.top_k = int(cfg.get("retrieval", "top_k", default=4))
        self.min_score = float(cfg.get("retrieval", "min_score", default=0.05))
        self.mode = cfg.get("retrieval", "mode", default="hybrid")
        self.rerank_top_k = int(cfg.get("retrieval", "rerank_top_k", default=self.top_k))

    def ready(self) -> bool:
        return len(self.store) > 0

    def retrieve(self, query: str):
        """主检索入口: 根据 mode 选择向量检索或混合检索，再可选重排序。"""
        if not self.ready():
            return []

        qvec = self.embedder.embed([query])[0]

        # 第一步: 召回候选
        if self.mode == "hybrid":
            # Hybrid Search: 向量 + BM25，RRF 融合
            candidates = self.store.hybrid_search(
                query, qvec,
                top_k=max(self.top_k * 3, 12),  # 多召回一些给 reranker
                min_score=self.min_score,
            )
        else:
            # 纯向量检索（向后兼容）
            candidates = self.store.search(qvec, top_k=max(self.top_k * 3, 12),
                                           min_score=self.min_score)

        if not candidates:
            return []

        # 第二步: Reranker 重排序（离线 offline 模式也有简单关键词 rerank）
        candidates = [hit for hit in candidates if _is_relevant(query, hit)]
        if not candidates:
            return []

        docs = [f"{h.title}\n{h.text}" for h in candidates]
        reranked = self.reranker.rerank(query, docs, top_k=self.rerank_top_k)
        results = [candidates[idx] for idx, _ in reranked if idx < len(candidates)]

        return results[:self.top_k]

    def build_evidence(self, hits) -> str:
        if not hits:
            return "(知识库中未检索到相关依据，请谨慎回答或建议用户查阅官方发布。)"
        lines = ["检索到的依据:"]
        for i, h in enumerate(hits, 1):
            extra = []
            if h.district:
                extra.append(f"区域:{h.district}")
            if h.road:
                extra.append(f"路段:{h.road}")
            if h.valid_time:
                extra.append(f"时间:{h.valid_time}")
            meta_str = f" [{', '.join(extra)}]" if extra else ""
            lines.append(
                f"[{i}] {h.text}\n"
                f"    来源: {h.title} ({h.url}, 发布于 {h.published_at or '未知'}, "
                f"抓取于 {h.fetched_at}){meta_str}"
            )
        return "\n".join(lines)
