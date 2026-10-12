"""步骤1: 抓取成都市交管局信息发布栏 -> data/raw/documents.json。

用法:
    python scripts/1_scrape.py            # 尝试在线抓取，失败回退样例语料
    python scripts/1_scrape.py --offline  # 直接用内置样例语料(无网络/可复现)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from travelqa.config import Config       # noqa: E402
from travelqa.scraper import scrape      # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="跳过联网，使用内置样例语料")
    args = ap.parse_args()

    cfg = Config.load()
    raw_dir = cfg.resolve_path(cfg.get("paths", "raw_dir", default="data/raw"))
    docs = scrape(raw_dir, offline=args.offline)
    print(f"[scrape] 共 {len(docs)} 篇文档 -> {raw_dir / 'documents.json'}")
    for d in docs:
        print(f"  - {d.title} ({d.fetched_at})")


if __name__ == "__main__":
    main()
