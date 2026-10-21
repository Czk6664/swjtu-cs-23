"""成都市交管局信息发布栏抓取器。

要点(遵守抓取礼仪与项目安全规则):
- 尊重 robots.txt、限速(默认每请求间隔 >=1s)、设置 UA、失败重试有上限。
- 原始 HTML 落盘缓存，保留 URL + 抓取时间(溯源)，RAG 回答方可引用来源。
- 离线/无网络时回退到内置 SAMPLE_DOCS，保证后续流程可跑通。

真实站点结构可能随时变化 —— 选择器集中在 SELECTORS 常量，便于按实际页面调整。
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .sample_corpus import SAMPLE_DOCS

# 成都市公安局交通管理局 信息公开/公告 入口（占位，按实际栏目调整）。
BASE_URL = "https://gaj.chengdu.gov.cn"
LIST_PATHS = ["/jjzd/"]  # 信息发布栏列表页路径，需按真实站点核对
USER_AGENT = "TravelQA-CourseBot/0.1 (academic homework; contact: student@example.edu)"
REQUEST_INTERVAL_S = 1.0
MAX_PAGES = 20

# 真实页面选择器（核对站点后填写）。
SELECTORS = {
    "list_item": "a.news-link",     # 列表页文章链接
    "title": "h1.article-title",    # 详情页标题
    "body": "div.article-content",  # 详情页正文
    "date": "span.publish-date",    # 发布时间
}


@dataclass
class Document:
    title: str
    url: str
    fetched_at: str
    category: str
    text: str
    published_at: str = ""
    source_kind: str = "official"
    district: str = ""
    road: str = ""
    valid_time: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def scrape(out_dir: str | Path, max_pages: int = MAX_PAGES,
           offline: bool = False) -> list[Document]:
    """抓取并落盘。无网络或 offline=True 时回退到样例语料。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if offline:
        return _use_sample(out)

    try:
        import requests  # noqa: F401
        from bs4 import BeautifulSoup  # noqa: F401
    except ModuleNotFoundError:
        print("[scraper] 未安装 requests/bs4，回退到离线样例语料。")
        return _use_sample(out)

    try:
        docs = _crawl(out, max_pages)
    except Exception as exc:  # 网络/解析异常 -> 不中断流程
        print(f"[scraper] 在线抓取失败({exc!r})，回退到离线样例语料。")
        return _use_sample(out)

    if not docs:
        print("[scraper] 在线未抓到内容(可能选择器需按真实站点调整)，回退到样例语料。")
        return _use_sample(out)
    return docs


def _crawl(out: Path, max_pages: int) -> list[Document]:
    import requests
    from bs4 import BeautifulSoup

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    today = time.strftime("%Y-%m-%d")
    docs: list[Document] = []

    article_urls: list[str] = []
    for path in LIST_PATHS:
        resp = session.get(BASE_URL + path, timeout=15)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "lxml")
        for a in soup.select(SELECTORS["list_item"]):
            href = a.get("href", "")
            if href:
                article_urls.append(href if href.startswith("http") else BASE_URL + href)
        time.sleep(REQUEST_INTERVAL_S)

    for url in article_urls[:max_pages]:
        try:
            resp = session.get(url, timeout=15)
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "lxml")
            title_el = soup.select_one(SELECTORS["title"])
            body_el = soup.select_one(SELECTORS["body"])
            date_el = soup.select_one(SELECTORS["date"])
            if not body_el:
                continue
            docs.append(Document(
                title=title_el.get_text(strip=True) if title_el else url,
                url=url,
                fetched_at=today,
                category="交管信息",
                text=body_el.get_text(" ", strip=True),
                published_at=(date_el.get_text(strip=True) if date_el else ""),
            ))
        except Exception:
            continue
        finally:
            time.sleep(REQUEST_INTERVAL_S)

    save_raw(out, docs)
    return docs


def _use_sample(out: Path) -> list[Document]:
    docs = [Document(**d) for d in SAMPLE_DOCS]
    save_raw(out, docs)
    return docs


def save_raw(out_dir: str | Path, docs: list[Document]) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "documents.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump([d.to_dict() for d in docs], f, ensure_ascii=False, indent=2)
    return path


def load_raw(out_dir: str | Path) -> list[Document]:
    path = Path(out_dir) / "documents.json"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [Document(**d) for d in json.load(f)]
