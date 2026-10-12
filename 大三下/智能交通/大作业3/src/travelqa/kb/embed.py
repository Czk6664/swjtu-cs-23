"""可插拔 embedding 与 reranker。

Embedding:
- offline_hash         : 纯 Python 哈希词袋向量。零依赖、零下载，满足"模型先不下载"，
                         可让 RAG 端到端跑通；语义精度有限，仅用于原型/CI。
- sentence_transformers: 真实语义向量，需安装 sentence-transformers 并下载模型。
                         推荐 BAAI/bge-m3（多功能多语言多粒度，支持 8192 tokens）。

Reranker:
- offline              : 基于关键词重叠的简单打分，零依赖，用于原型。
- sentence_transformers: 真实重排序模型，推荐 BAAI/bge-reranker-v2-m3。

两者都实现统一接口，config 切换即可，不动编排逻辑。
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

_TOKEN = re.compile(r"[一-鿿]|[a-zA-Z0-9]+")


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

class Embedder(Protocol):
    dim: int
    def embed(self, texts: list[str]) -> list[list[float]]: ...


def _tokenize(text: str) -> list[str]:
    """中文按字、英文数字按词。再加 2-gram(中文) 提升区分度。"""
    toks = _TOKEN.findall(text.lower())
    bigrams = [toks[i] + toks[i + 1] for i in range(len(toks) - 1)]
    return toks + bigrams


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm > 0 else vec


class HashEmbedder:
    """特征哈希(feature hashing)词袋向量。确定性、无外部依赖。"""

    def __init__(self, dim: int = 512):
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for text in texts:
            vec = [0.0] * self.dim
            for tok in _tokenize(text):
                h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
                idx = h % self.dim
                sign = 1.0 if (h >> 1) & 1 else -1.0
                vec[idx] += sign
            out.append(_normalize(vec))
        return out


class SentenceTransformerEmbedder:
    """真实语义向量。仅在配置切换且依赖就绪时使用。
    推荐模型: BAAI/bge-m3（中文 + 长文本 + 混合检索）。"""

    def __init__(self, model: str):
        from sentence_transformers import SentenceTransformer  # 延迟导入
        self._model = SentenceTransformer(model)
        self.dim = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        embs = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, e)) for e in embs]


def get_embedder(cfg) -> Embedder:
    provider = cfg.get("embedding", "provider", default="offline_hash")
    if provider == "sentence_transformers":
        return SentenceTransformerEmbedder(_resolve_model_path(cfg, cfg.get("embedding", "model")))
    return HashEmbedder(int(cfg.get("embedding", "dim", default=512)))


# ---------------------------------------------------------------------------
# Reranker
# ---------------------------------------------------------------------------

class Reranker(Protocol):
    def rerank(self, query: str, docs: list[str], top_k: int = 4) -> list[tuple[int, float]]:
        """返回 (原始索引, 分数) 按相关性降序。"""
        ...


class OfflineReranker:
    """基于关键词重叠的简单 reranker，零依赖。用于离线原型。
    比纯向量检索多一层关键词过滤，聊胜于无。"""

    def rerank(self, query: str, docs: list[str], top_k: int = 4) -> list[tuple[int, float]]:
        q_tokens = set(_tokenize(query))
        if not q_tokens:
            return [(i, 0.0) for i in range(min(top_k, len(docs)))]
        scored = []
        for i, doc in enumerate(docs):
            d_tokens = set(_tokenize(doc))
            overlap = len(q_tokens & d_tokens)
            # Jaccard-like 打分，偏向重叠比例高的
            score = overlap / max(len(q_tokens | d_tokens), 1)
            scored.append((i, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


class CrossEncoderReranker:
    """真实交叉编码器 reranker。推荐 BAAI/bge-reranker-v2-m3。
    需安装 sentence-transformers 并下载模型。"""

    def __init__(self, model: str):
        from sentence_transformers import CrossEncoder  # 延迟导入
        self._model = CrossEncoder(model)

    def rerank(self, query: str, docs: list[str], top_k: int = 4) -> list[tuple[int, float]]:
        if not docs:
            return []
        pairs = [(query, doc) for doc in docs]
        scores = self._model.predict(pairs)
        scored = list(enumerate(map(float, scores)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


def get_reranker(cfg) -> Reranker:
    provider = cfg.get("retrieval", "reranker", "provider", default="offline")
    if provider == "sentence_transformers":
        model = _resolve_model_path(
            cfg,
            cfg.get("retrieval", "reranker", "model", default="BAAI/bge-reranker-v2-m3"),
        )
        return CrossEncoderReranker(model)
    return OfflineReranker()


def _resolve_model_path(cfg, model: str) -> str:
    """Use project-relative model directories when present, otherwise hub IDs."""
    path = cfg.resolve_path(model)
    return str(path) if path.exists() else model
