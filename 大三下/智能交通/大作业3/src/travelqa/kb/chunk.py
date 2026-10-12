"""把文档切成适合检索的片段，保留溯源元数据。

中文文本按句末标点切句，再贪心合并到 ~max_chars，块间留 overlap 句以保留上下文。
保留公告结构化元数据(路段/区域/生效时间)用于 metadata filtering。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict

_SENT_END = re.compile(r"(?<=[。！？!?；;])")

# 从文本中粗提取成都常见区域
_DISTRICTS = [
    "锦江区", "青羊区", "武侯区", "成华区", "金牛区", "高新区", "天府新区",
    "龙泉驿区", "新都区", "温江区", "双流区", "郫都区", "青白江区",
]
_DISTRICT_RE = re.compile("|".join(re.escape(d) for d in _DISTRICTS))

# 常见道路关键词
_ROADS = [
    "二环路", "三环路", "绕城高速", "天府大道", "剑南大道", "人民南路",
    "春熙路", "红星路", "蜀都大道", "一环路", "成华大道", "建设路",
    "武侯祠大街", "科华北路", "高新大道", "益州大道", "天府广场",
    "二环高架", "三环高架",
]
_ROAD_RE = re.compile("|".join(re.escape(r) for r in _ROADS))


@dataclass
class Chunk:
    id: str
    text: str
    title: str
    url: str
    fetched_at: str
    published_at: str
    category: str
    district: str      # 涉及区域，如"武侯区"
    road: str          # 涉及路段，如"天府大道"
    valid_time: str    # 生效时间/管制时间

    def to_dict(self) -> dict:
        return asdict(self)


def _split_sentences(text: str) -> list[str]:
    parts = [
        piece.strip()
        for block in text.splitlines()
        for piece in _SENT_END.split(block)
        if piece.strip()
    ]
    return parts or ([text.strip()] if text.strip() else [])


def _extract_district(text: str) -> str:
    m = _DISTRICT_RE.search(text)
    return m.group(0) if m else ""


def _extract_road(text: str) -> str:
    m = _ROAD_RE.search(text)
    return m.group(0) if m else ""


def _extract_valid_time(text: str) -> str:
    """粗提取时间表达，如'2026年5月1日起'、'工作日 7:30-20:00'。"""
    patterns = [
        r"\d{4}年\d{1,2}月\d{1,2}日[起至到-]\d{4}年\d{1,2}月\d{1,2}日",
        r"\d{4}年\d{1,2}月\d{1,2}日起?",
        r"工作日\s*\d{1,2}:\d{2}[-–]\d{1,2}:\d{2}",
        r"即日起至\d{4}年\d{1,2}月\d{1,2}日",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(0)
    return ""


def chunk_documents(docs, max_chars: int = 600, overlap_sents: int = 1) -> list[Chunk]:
    chunks: list[Chunk] = []
    for doc in docs:
        d = doc.to_dict() if hasattr(doc, "to_dict") else dict(doc)
        sents = _split_sentences(d.get("text", ""))
        buf: list[str] = []
        cur = 0
        part = 0
        for sent in sents:
            while len(sent) > max_chars:
                if buf:
                    chunks.append(_make(d, part, "".join(buf)))
                    part += 1
                    buf = []
                    cur = 0
                chunks.append(_make(d, part, sent[:max_chars]))
                part += 1
                sent = sent[max_chars:]
            if buf and cur + len(sent) > max_chars:
                chunks.append(_make(d, part, "".join(buf)))
                part += 1
                buf = buf[-overlap_sents:] if overlap_sents else []
                cur = sum(len(s) for s in buf)
            buf.append(sent)
            cur += len(sent)
        if buf:
            chunks.append(_make(d, part, "".join(buf)))
    return chunks


def _make(d: dict, part: int, text: str) -> Chunk:
    base = re.sub(r"\W+", "-", d.get("title", "doc"))[:24].strip("-") or "doc"
    # 优先用文档级元数据，fallback 到从文本提取
    district = d.get("district", "") or _extract_district(text)
    road = d.get("road", "") or _extract_road(text)
    valid_time = d.get("valid_time", "") or _extract_valid_time(text)
    return Chunk(
        id=f"{base}-{part}",
        text=text,
        title=d.get("title", ""),
        url=d.get("url", ""),
        fetched_at=d.get("fetched_at", ""),
        published_at=d.get("published_at", ""),
        category=d.get("category", ""),
        district=district,
        road=road,
        valid_time=valid_time,
    )
