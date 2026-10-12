"""本地向量库 + BM25 索引，支持 Hybrid Search 混合检索。

向量检索: embedder 侧已归一化，相似度 = 点积。
BM25 检索: 纯 Python TF-IDF + BM25 长度归一化，零外部依赖。
Hybrid Search: Reciprocal Rank Fusion (RRF) 融合两路结果。

语料规模(课程级)下线性扫描足够。
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Hit:
    score: float
    text: str
    title: str
    url: str
    fetched_at: str
    published_at: str
    category: str
    district: str
    road: str
    valid_time: str


# ---------------------------------------------------------------------------
# BM25 实现（纯 Python，零依赖）
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[一-鿿]|[a-zA-Z0-9]+")


def _tokenize(text: str) -> list[str]:
    """中文按字切分 + 英文按词切分，与 embed.py 的 tokenizer 保持一致。"""
    return _TOKEN_RE.findall(text.lower())


class BM25Index:
    """Okapi BM25 索引，适合中文短文本关键词检索。"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._docs: list[list[str]] = []   # 每篇文档的 token 列表
        self._doc_lens: list[int] = []
        self._avg_dl: float = 0.0
        self._df: Counter = Counter()       # document frequency
        self._n_docs: int = 0

    def build(self, texts: list[str]) -> None:
        self._docs = [_tokenize(t) for t in texts]
        self._doc_lens = [len(d) for d in self._docs]
        self._n_docs = len(texts)
        self._avg_dl = sum(self._doc_lens) / max(self._n_docs, 1)
        self._df.clear()
        for doc in self._docs:
            unique = set(doc)
            for tok in unique:
                self._df[tok] += 1

    def score(self, query: str, top_k: int = 10) -> list[tuple[int, float]]:
        """返回 (doc_index, score) 按分数降序。"""
        if not self._n_docs:
            return []
        q_tokens = _tokenize(query)
        scores = [0.0] * self._n_docs
        for tok in q_tokens:
            if tok not in self._df:
                continue
            df = self._df[tok]
            idf = math.log((self._n_docs - df + 0.5) / (df + 0.5) + 1.0)
            for i, doc in enumerate(self._docs):
                tf = doc.count(tok)
                if tf == 0:
                    continue
                dl = self._doc_lens[i]
                norm = 1 - self.b + self.b * dl / max(self._avg_dl, 1)
                scores[i] += idf * tf * (self.k1 + 1) / (tf + self.k1 * norm)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(idx, sc) for idx, sc in ranked[:top_k] if sc > 0]


# ---------------------------------------------------------------------------
# 向量库 + Hybrid Search
# ---------------------------------------------------------------------------

class VectorStore:
    def __init__(self):
        self._vectors: list[list[float]] = []
        self._meta: list[dict] = []
        self._bm25 = BM25Index()
        self.embedding_provider: str = ""
        self.embedding_model: str = ""

    def add(self, vectors: list[list[float]], chunks) -> None:
        for vec, ch in zip(vectors, chunks):
            self._vectors.append(vec)
            m = ch.to_dict() if hasattr(ch, "to_dict") else dict(ch)
            self._meta.append(m)

    def build_bm25(self) -> None:
        """从已添加的 meta 中构建 BM25 索引。"""
        texts = [m.get("text", "") for m in self._meta]
        self._bm25.build(texts)

    def _to_hit(self, score: float, m: dict) -> Hit:
        return Hit(
            score=round(score, 4),
            text=m.get("text", ""),
            title=m.get("title", ""),
            url=m.get("url", ""),
            fetched_at=m.get("fetched_at", ""),
            published_at=m.get("published_at", ""),
            category=m.get("category", ""),
            district=m.get("district", ""),
            road=m.get("road", ""),
            valid_time=m.get("valid_time", ""),
        )

    # --- 向量检索 ---
    def vector_search(self, query_vec: list[float], top_k: int = 10,
                      min_score: float = 0.0) -> list[tuple[int, float]]:
        """返回 (meta_index, score)。"""
        scored = []
        for i, vec in enumerate(self._vectors):
            score = sum(a * b for a, b in zip(query_vec, vec))
            if score >= min_score:
                scored.append((i, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    # --- BM25 检索 ---
    def bm25_search(self, query: str, top_k: int = 10) -> list[tuple[int, float]]:
        """返回 (meta_index, score)。"""
        return self._bm25.score(query, top_k=top_k)

    # --- Hybrid Search (RRF 融合) ---
    def hybrid_search(self, query: str, query_vec: list[float],
                      top_k: int = 4, min_score: float = 0.0,
                      vector_top_k: int = 20, bm25_top_k: int = 20,
                      rrf_k: int = 60) -> list[Hit]:
        """Hybrid Search: 向量检索 + BM25 关键词检索，RRF 融合排序。

        Args:
            query: 用户查询文本
            query_vec: 查询的向量表示
            top_k: 最终返回数量
            min_score: 向量检索最低相似度阈值
            vector_top_k: 向量检索召回数
            bm25_top_k: BM25 召回数
            rrf_k: RRF 常数（控制排名靠后的权重衰减）
        """
        vec_hits = self.vector_search(query_vec, top_k=vector_top_k, min_score=min_score)
        bm25_hits = self.bm25_search(query, top_k=bm25_top_k)

        # RRF 融合: score = Σ 1 / (k + rank)
        fused: dict[int, float] = {}
        for rank, (idx, _) in enumerate(vec_hits):
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (rrf_k + rank + 1)
        for rank, (idx, _) in enumerate(bm25_hits):
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (rrf_k + rank + 1)

        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)
        return [self._to_hit(sc, self._meta[idx]) for idx, sc in ranked[:top_k]]

    # --- 旧接口兼容 ---
    def search(self, query_vec: list[float], top_k: int = 4,
               min_score: float = 0.0) -> list[Hit]:
        """纯向量检索（保持向后兼容）。"""
        hits = self.vector_search(query_vec, top_k=top_k, min_score=min_score)
        return [self._to_hit(sc, self._meta[idx]) for idx, sc in hits]

    # --- Metadata 过滤 ---
    def filter_search(self, query_vec: list[float], filters: dict,
                      top_k: int = 4, min_score: float = 0.0) -> list[Hit]:
        """带 metadata 过滤的向量检索。filters 如 {"district": "武侯区"}。"""
        scored = []
        for i, vec in enumerate(self._vectors):
            # 先检查 metadata 是否匹配
            match = True
            for key, val in filters.items():
                meta_val = self._meta[i].get(key, "")
                if val and val not in meta_val:
                    match = False
                    break
            if not match:
                continue
            score = sum(a * b for a, b in zip(query_vec, vec))
            if score >= min_score:
                scored.append((i, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [self._to_hit(sc, self._meta[idx]) for idx, sc in scored[:top_k]]

    # --- 持久化 ---
    def save(self, kb_dir: str | Path, embedding_provider: str = "",
             embedding_model: str = "") -> Path:
        d = Path(kb_dir)
        d.mkdir(parents=True, exist_ok=True)
        path = d / "index.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump({"embedding_provider": embedding_provider,
                       "embedding_model": embedding_model,
                       "vectors": self._vectors, "meta": self._meta},
                      f, ensure_ascii=False)
        return path

    @classmethod
    def load(cls, kb_dir: str | Path) -> "VectorStore":
        store = cls()
        path = Path(kb_dir) / "index.json"
        if not path.exists():
            return store
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        store._vectors = data.get("vectors", [])
        store._meta = data.get("meta", [])
        store.embedding_provider = data.get("embedding_provider", "")
        store.embedding_model = data.get("embedding_model", "")
        store.build_bm25()  # 加载后自动构建 BM25 索引
        return store

    def __len__(self) -> int:
        return len(self._vectors)
