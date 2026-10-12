"""步骤2: 用抓取的文档构建 RAG 知识库 -> data/kb/index.json。

依赖步骤1 的产物。若 data/raw 为空，会自动用样例语料兜底。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from travelqa.config import Config              # noqa: E402
from travelqa.kb import build_kb                # noqa: E402
from travelqa.scraper import load_raw, scrape   # noqa: E402


def main():
    cfg = Config.load()
    raw_dir = cfg.resolve_path(cfg.get("paths", "raw_dir", default="data/raw"))
    docs = load_raw(raw_dir)
    if not docs:
        print("[build_kb] data/raw 为空，先用样例语料生成。")
        docs = scrape(raw_dir, offline=True)
    build_kb(cfg, docs)


if __name__ == "__main__":
    main()
