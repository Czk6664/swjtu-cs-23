"""知识库构建管道: 原始文档 -> 分块 -> 向量化 -> BM25 索引 -> 落盘。"""
from __future__ import annotations

from pathlib import Path

from .chunk import chunk_documents
from .embed import get_embedder
from .store import VectorStore


def build_kb(cfg, docs) -> VectorStore:
    chunks = chunk_documents(docs)
    embedder = get_embedder(cfg)
    vectors = embedder.embed([c.text for c in chunks])

    store = VectorStore()
    store.add(vectors, chunks)
    store.build_bm25()  # 构建 BM25 关键词索引

    kb_dir = cfg.resolve_path(cfg.get("paths", "kb_dir", default="data/kb"))
    store.save(kb_dir, embedding_provider=cfg.get("embedding", "provider", default="offline_hash"),
               embedding_model=cfg.get("embedding", "model", default=""))
    print(f"[kb] 已构建 {len(chunks)} 个知识片段(向量 + BM25) -> {Path(kb_dir) / 'index.json'}")
    return store
