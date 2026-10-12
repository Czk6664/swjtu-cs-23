"""抓取成都市交管局信息发布栏，产出带溯源(URL+抓取时间)的文档。"""
from .chengdu_traffic import Document, scrape, load_raw, save_raw  # noqa: F401
from .sample_corpus import SAMPLE_DOCS  # noqa: F401
