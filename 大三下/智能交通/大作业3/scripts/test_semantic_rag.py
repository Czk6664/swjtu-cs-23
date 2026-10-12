"""Smoke-test the configured semantic RAG index."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from travelqa.config import Config  # noqa: E402
from travelqa.rag import Retriever  # noqa: E402

CASES = [
    ("酒驾处罚", "饮酒后驾驶机动车如何处罚", "中华人民共和国道路交通安全法"),
    ("公告索引", "天府三街交通组织通告", "天府三街"),
    ("缺失依据", "成都尾号限行怎么规定的", ""),
]


def main() -> None:
    cfg = Config.load()
    print(f"[semantic_rag] embedding={cfg.get('embedding', 'model')}")
    print(f"[semantic_rag] reranker={cfg.get('retrieval', 'reranker', 'model')}")
    retriever = Retriever(cfg)
    if not retriever.ready():
        raise SystemExit("[semantic_rag] knowledge base is empty")
    for label, query, expected in CASES:
        hits = retriever.retrieve(query)
        title = hits[0].title if hits else ""
        ok = expected in title if expected else not hits
        print(f"[{'OK' if ok else 'WARN'}] {label}: hits={len(hits)}, first={title or '(none)'}")


if __name__ == "__main__":
    main()
