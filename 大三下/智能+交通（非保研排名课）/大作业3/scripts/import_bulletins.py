"""Import manually collected real traffic bulletins into the local RAG corpus.

The Chengdu traffic-management website may return an anti-automation page.
Collect the official text in a browser, save one JSON object per line, then run:

    python scripts/import_bulletins.py --input data/manual/traffic_bulletins.jsonl
    python scripts/2_build_kb.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from travelqa.config import Config  # noqa: E402
from travelqa.scraper import Document, load_raw, save_raw  # noqa: E402

ALLOWED_SOURCE_KINDS = {"official", "official_reprint"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data" / "manual" / "traffic_bulletins.jsonl",
        help="JSONL file containing reviewed bulletin text",
    )
    parser.add_argument(
        "--merge-existing",
        action="store_true",
        help="retain existing non-placeholder documents before importing",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def validate(row: dict, index: int) -> Document:
    required = ("title", "url", "text", "published_at")
    missing = [key for key in required if not str(row.get(key, "")).strip()]
    if missing:
        raise ValueError(f"row {index}: missing required fields: {', '.join(missing)}")
    url = str(row["url"]).strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"row {index}: invalid source URL: {url}")
    if "/example/" in url:
        raise ValueError(f"row {index}: placeholder URL is not allowed: {url}")
    text = str(row["text"]).strip()
    if len(text) < 80:
        raise ValueError(f"row {index}: bulletin body is too short ({len(text)} chars)")
    source_kind = str(row.get("source_kind", "official")).strip()
    if source_kind not in ALLOWED_SOURCE_KINDS:
        raise ValueError(
            f"row {index}: source_kind must be one of {sorted(ALLOWED_SOURCE_KINDS)}"
        )
    return Document(
        title=str(row["title"]).strip(),
        url=url,
        fetched_at=str(row.get("fetched_at") or time.strftime("%Y-%m-%d")).strip(),
        published_at=str(row["published_at"]).strip(),
        category=str(row.get("category", "交管信息")).strip(),
        text=text,
        source_kind=source_kind,
        district=str(row.get("district", "")).strip(),
        road=str(row.get("road", "")).strip(),
        valid_time=str(row.get("valid_time", "")).strip(),
    )


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"input file does not exist: {args.input}")

    cfg = Config.load()
    raw_dir = cfg.resolve_path(cfg.get("paths", "raw_dir", default="data/raw"))
    docs = []
    if args.merge_existing:
        docs = [doc for doc in load_raw(raw_dir) if "/example/" not in doc.url]

    by_url = {doc.url: doc for doc in docs}
    for index, row in enumerate(read_jsonl(args.input), start=1):
        doc = validate(row, index)
        by_url[doc.url] = doc

    imported = sorted(by_url.values(), key=lambda doc: (doc.published_at, doc.url), reverse=True)
    output = save_raw(raw_dir, imported)
    print(f"[import_bulletins] 写出 {len(imported)} 篇已审核公告 -> {output}")
    for doc in imported:
        print(f"  - [{doc.source_kind}] {doc.published_at} {doc.title}")


if __name__ == "__main__":
    main()
