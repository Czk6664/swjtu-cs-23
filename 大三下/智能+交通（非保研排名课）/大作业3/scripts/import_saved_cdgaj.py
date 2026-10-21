"""Import browser-saved Chengdu Public Security Bureau bulletin pages.

The official site may return an anti-automation page to HTTP clients. This
script intentionally does not bypass that protection. Save list and detail
pages from a normal browser, place the HTML files in one directory, then run:

    python scripts/import_saved_cdgaj.py --html-dir data/manual/cdgaj_html
    python scripts/2_build_kb.py
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from travelqa.config import Config  # noqa: E402
from travelqa.scraper import Document, load_raw, save_raw  # noqa: E402

BASE_URL = "https://cdgaj.chengdu.gov.cn"
LIST_URL = f"{BASE_URL}/cdsgaj/jgxx/news_gkgs1615379688854.shtml"
CONTENT_PATH_RE = re.compile(r"/cdsgaj/(?:jgxx|tzgg|gkgs)/\d{4}-\d{2}/\d{2}/content_[\w-]+\.shtml")
LIST_PATH_RE = re.compile(r"/cdsgaj/jgxx/news_gkgs1615379688854(?:_(\d+))?\.shtml")
DATE_RE = re.compile(r"20\d{2}[-年/.]\d{1,2}[-月/.]\d{1,2}日?")
WAF_MARKERS = ("$_ts.nsd", "PIFb0UYYzxme", "访问验证")
BODY_SELECTORS = (
    ".TRS_Editor",
    ".article-content",
    ".article_content",
    ".news-content",
    ".detail-content",
    ".content",
    "article",
)
TITLE_SELECTORS = ("h1", ".article-title", ".news-title", ".detail-title")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--html-dir",
        type=Path,
        default=ROOT / "data" / "manual" / "cdgaj_html",
        help="directory containing browser-saved list and detail HTML pages",
    )
    parser.add_argument(
        "--merge-existing",
        action="store_true",
        help="retain existing non-placeholder documents before importing",
    )
    parser.add_argument(
        "--dataset-jsonl",
        type=Path,
        default=ROOT / "data" / "manual" / "traffic_bulletins.jsonl",
        help="reviewable JSONL dataset output",
    )
    parser.add_argument(
        "--urls-output",
        type=Path,
        default=ROOT / "data" / "manual" / "cdgaj_urls.txt",
        help="detail URLs discovered from saved list pages",
    )
    parser.add_argument(
        "--list-urls-output",
        type=Path,
        default=ROOT / "data" / "manual" / "cdgaj_list_urls.txt",
        help="list-page URLs inferred from pagination links",
    )
    parser.add_argument(
        "--index-jsonl",
        type=Path,
        default=ROOT / "data" / "manual" / "cdgaj_notice_index.jsonl",
        help="reviewable bulletin metadata extracted from saved list pages",
    )
    return parser.parse_args()


def read_html(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def find_urls(pages: list[tuple[Path, str]]) -> dict[str, str]:
    urls = {}
    for _, source in pages:
        for path in CONTENT_PATH_RE.findall(source):
            url = urljoin(BASE_URL, path)
            urls[Path(urlparse(url).path).name] = url
    return urls


def find_list_urls(pages: list[tuple[Path, str]]) -> list[str]:
    last_page = 1
    for _, source in pages:
        for suffix in LIST_PATH_RE.findall(source):
            last_page = max(last_page, int(suffix or 1))
    return [
        LIST_URL if page == 1 else LIST_URL.replace(".shtml", f"_{page}.shtml")
        for page in range(1, last_page + 1)
    ]


def extract_index(pages: list[tuple[Path, str]]) -> list[dict]:
    from bs4 import BeautifulSoup

    rows = {}
    for _, source in pages:
        if any(marker in source for marker in WAF_MARKERS):
            continue
        soup = BeautifulSoup(source, "lxml")
        for link in soup.select("a[href*='content_']"):
            url = urljoin(BASE_URL, link.get("href", ""))
            if not CONTENT_PATH_RE.search(url):
                continue
            title = clean_text(link.get("title") or link.get_text(" ", strip=True))
            container = link.find_parent("li", class_="item") or link.parent
            match = DATE_RE.search(container.get_text(" ", strip=True))
            if not title or not match:
                continue
            rows[url] = {
                "title": title,
                "url": url,
                "published_at": normalize_date(match.group(0)),
                "category": "交管通知索引",
                "source_kind": "official",
            }
    return sorted(
        rows.values(),
        key=lambda row: (row["published_at"], row["url"]),
        reverse=True,
    )


def canonical_url(soup, path: Path, known_urls: dict[str, str]) -> str:
    for selector, attribute in (
        ("link[rel=canonical]", "href"),
        ("meta[property='og:url']", "content"),
        ("meta[name='url']", "content"),
    ):
        node = soup.select_one(selector)
        if node and node.get(attribute):
            return urljoin(BASE_URL, node[attribute])
    for name, url in known_urls.items():
        if name in path.name:
            return url
    return ""


def best_text(soup) -> str:
    candidates = []
    for selector in BODY_SELECTORS:
        candidates.extend(node.get_text(" ", strip=True) for node in soup.select(selector))
    if not candidates:
        candidates.extend(node.get_text(" ", strip=True) for node in soup.select("main, body"))
    candidates = [clean_text(text) for text in candidates]
    return max(candidates, key=len, default="")


def best_title(soup, path: Path) -> str:
    for selector in TITLE_SELECTORS:
        node = soup.select_one(selector)
        if node and clean_text(node.get_text(" ", strip=True)):
            return clean_text(node.get_text(" ", strip=True))
    if soup.title:
        return clean_text(soup.title.get_text(" ", strip=True)).split("_")[0]
    return path.stem


def best_date(soup, text: str) -> str:
    for selector in ("meta[name='publishdate']", "meta[name='pubdate']", ".publish-date", ".date", "time"):
        node = soup.select_one(selector)
        if not node:
            continue
        value = node.get("content") or node.get("datetime") or node.get_text(" ", strip=True)
        match = DATE_RE.search(value)
        if match:
            return match.group(0)
    match = DATE_RE.search(text)
    return match.group(0) if match else ""


def normalize_date(value: str) -> str:
    parts = re.findall(r"\d+", value)
    if len(parts) < 3:
        return value
    return f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"


def extract_pages(html_dir: Path) -> tuple[list[Document], list[str]]:
    from bs4 import BeautifulSoup

    pages = [(path, read_html(path)) for path in sorted(html_dir.rglob("*.htm*"))]
    known_urls = find_urls(pages)
    docs, warnings = [], []
    seen = set()
    for path, source in pages:
        if any(marker in source for marker in WAF_MARKERS):
            warnings.append(f"{path.name}: 防护验证页，已跳过")
            continue
        soup = BeautifulSoup(source, "lxml")
        url = canonical_url(soup, path, known_urls)
        if not url or not CONTENT_PATH_RE.search(url):
            continue
        text = best_text(soup)
        if len(text) < 80:
            warnings.append(f"{path.name}: 正文过短({len(text)}字)，已跳过")
            continue
        title = best_title(soup, path)
        published_at = normalize_date(best_date(soup, text))
        if not published_at:
            warnings.append(f"{path.name}: 缺少发布日期，已跳过")
            continue
        if url in seen:
            continue
        seen.add(url)
        docs.append(Document(
            title=title,
            url=url,
            fetched_at=time.strftime("%Y-%m-%d"),
            published_at=published_at,
            category="交管通知",
            source_kind="official",
            text=text,
        ))
    return docs, warnings


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            data = row.to_dict() if hasattr(row, "to_dict") else dict(row)
            file.write(json.dumps(data, ensure_ascii=False) + "\n")


def write_urls(path: Path, urls: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(f"{url}\n" for url in sorted(urls.values())),
        encoding="utf-8",
    )


def write_url_list(path: Path, urls: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{url}\n" for url in urls), encoding="utf-8")


def index_documents(rows: list[dict]) -> list[Document]:
    """Keep real bulletin links usable for RAG until detail HTML is archived."""
    fetched_at = time.strftime("%Y-%m-%d")
    return [
        Document(
            title=row["title"],
            url=row["url"],
            fetched_at=fetched_at,
            published_at=row["published_at"],
            category="交管通知索引",
            source_kind="official_index",
            text=(
                f"公告索引记录：{row['title']}。发布日期：{row['published_at']}。"
                "当前仅已归档官方标题、发布日期和链接；公告正文需访问官方链接核验。"
            ),
        )
        for row in rows
    ]


def main() -> None:
    args = parse_args()
    if not args.html_dir.exists():
        args.html_dir.mkdir(parents=True)
        raise SystemExit(
            f"HTML directory created: {args.html_dir}\n"
            f"Save the list page and detail pages from {LIST_URL}, then rerun this command."
        )
    pages = [(path, read_html(path)) for path in sorted(args.html_dir.rglob("*.htm*"))]
    discovered_urls = find_urls(pages)
    list_urls = find_list_urls(pages)
    index_rows = extract_index(pages)
    write_urls(args.urls_output, discovered_urls)
    write_url_list(args.list_urls_output, list_urls)
    write_jsonl(args.index_jsonl, index_rows)
    print(f"[import_saved_cdgaj] 从列表页发现 {len(discovered_urls)} 个详情链接 -> {args.urls_output}")
    print(f"[import_saved_cdgaj] 推断 {len(list_urls)} 个列表页 -> {args.list_urls_output}")
    print(f"[import_saved_cdgaj] 写出 {len(index_rows)} 条通知索引 -> {args.index_jsonl}")
    docs, warnings = extract_pages(args.html_dir)
    if not docs:
        print(
            f"[import_saved_cdgaj] 尚未发现详情正文: {args.html_dir}\n"
            "[import_saved_cdgaj] 请按 URL 清单保存官方详情页 HTML，随后重新运行。\n"
            "[import_saved_cdgaj] 暂时写入真实公告索引；回答时必须提示正文待官方链接核验。"
        )
        docs = index_documents(index_rows)

    cfg = Config.load()
    raw_dir = cfg.resolve_path(cfg.get("paths", "raw_dir", default="data/raw"))
    if args.merge_existing:
        existing = [doc for doc in load_raw(raw_dir) if "/example/" not in doc.url]
        docs = list({doc.url: doc for doc in existing + docs}.values())
    docs.sort(key=lambda doc: (doc.published_at, doc.url), reverse=True)
    write_jsonl(args.dataset_jsonl, docs)
    output = save_raw(raw_dir, docs)
    print(f"[import_saved_cdgaj] 写出 {len(docs)} 篇真实通知 -> {output}")
    print(f"[import_saved_cdgaj] 可审计 JSONL -> {args.dataset_jsonl}")
    for warning in warnings:
        print(f"[import_saved_cdgaj] 警告: {warning}")


if __name__ == "__main__":
    main()
