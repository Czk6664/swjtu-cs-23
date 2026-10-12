"""Import reviewed traffic-related regulations from data/raw/open_data into RAG.

Supported formats: Markdown, DOCX, PDF. The importer keeps provenance and
merges with existing non-placeholder documents. Duplicate markdown summaries
are skipped when a DOCX copy of the same traffic law is present.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from travelqa.config import Config  # noqa: E402
from travelqa.scraper import Document, load_raw, save_raw  # noqa: E402

DEFAULT_SOURCE_URLS = {
    "中华人民共和国道路交通安全法_20210429.docx":
        "https://flk.npc.gov.cn/detail?fileId=&id=ff8081817ab231eb017abd617ef70519&title=中华人民共和国道路交通安全法&type=",
    "道路交通安全法.md":
        "https://flk.npc.gov.cn/detail?fileId=&id=ff8081817ab231eb017abd617ef70519&title=中华人民共和国道路交通安全法&type=",
    "中华人民共和国道路交通安全法实施条例__增刊2019·1国务院公报_中国政府网.pdf":
        "https://www.gov.cn/banshi/2005-08/23/content_25579.htm",
    "中华人民共和国民法典 - 中华人民共和国最高人民法院.pdf":
        "https://peixun.court.gov.cn/uploadfile/2020/0803/20200803092325165.pdf",
}
TITLE_REPLACEMENTS = {
    "中华人民共和国道路交通安全法_20210429": "中华人民共和国道路交通安全法",
    "中华人民共和国道路交通安全法实施条例__增刊2019·1国务院公报_中国政府网":
        "中华人民共和国道路交通安全法实施条例",
    "中华人民共和国民法典 - 中华人民共和国最高人民法院": "中华人民共和国民法典",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=ROOT / "data" / "raw" / "open_data")
    return parser.parse_args()


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\ufeff", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def read_markdown(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = text.replace("**", "")
    return clean_text(text)


def read_docx(path: Path) -> str:
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    paragraphs = []
    for paragraph in root.findall(".//w:p", namespace):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace))
        if text.strip():
            paragraphs.append(text)
    return clean_text("\n".join(paragraphs))


def read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        raise RuntimeError("PDF import requires pypdf: python -m pip install pypdf") from exc
    reader = PdfReader(str(path))
    return clean_text("\n".join(page.extract_text() or "" for page in reader.pages))


def source_url(path: Path) -> str:
    return DEFAULT_SOURCE_URLS.get(path.name, path.resolve().as_uri())


def title(path: Path) -> str:
    return TITLE_REPLACEMENTS.get(path.stem, path.stem)


def should_skip(path: Path, paths: list[Path]) -> bool:
    if path.name.lower() == "readme.md":
        return True
    return path.name == "道路交通安全法.md" and any(
        candidate.name == "中华人民共和国道路交通安全法_20210429.docx"
        for candidate in paths
    )


def import_documents(input_dir: Path) -> list[Document]:
    paths = sorted(
        path for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".md", ".docx", ".pdf"}
    )
    docs = []
    fetched_at = time.strftime("%Y-%m-%d")
    for path in paths:
        if should_skip(path, paths):
            print(f"[import_regulations] 跳过重复摘要: {path.name}")
            continue
        reader = {".md": read_markdown, ".docx": read_docx, ".pdf": read_pdf}[path.suffix.lower()]
        text = reader(path)
        if len(text) < 500:
            print(f"[import_regulations] 跳过正文过短文件({len(text)}字): {path.name}")
            continue
        docs.append(Document(
            title=title(path),
            url=source_url(path),
            fetched_at=fetched_at,
            published_at="",
            category="交通法规",
            source_kind="official_regulation",
            text=text,
        ))
        print(f"[import_regulations] 已解析: {path.name} ({len(text)}字)")
    return docs


def main() -> None:
    args = parse_args()
    if not args.input_dir.exists():
        raise SystemExit(f"input directory does not exist: {args.input_dir}")
    cfg = Config.load()
    raw_dir = cfg.resolve_path(cfg.get("paths", "raw_dir", default="data/raw"))
    existing = [
        doc for doc in load_raw(raw_dir)
        if "/example/" not in doc.url and doc.source_kind != "official_regulation"
    ]
    regulations = import_documents(args.input_dir)
    by_url = {doc.url: doc for doc in existing}
    for doc in regulations:
        by_url[doc.url] = doc
    docs = list(by_url.values())
    output = save_raw(raw_dir, docs)
    print(f"[import_regulations] 合并写出 {len(docs)} 篇文档 -> {output}")


if __name__ == "__main__":
    main()
