# 成都交管公告采集说明

成都交管官网可能对脚本请求返回防自动化页面。课程作业默认采用“浏览器人工审核原文，
本地脚本统一导入”的方式，避免绕过站点防护，也避免把转载摘要或占位 URL 当成事实。

## 来源优先级

1. 成都市公安局交通管理局官网或“成都交警”官方发布渠道：标记
   `source_kind=official`。
2. 成都发布、红星新闻网等成都官方媒体完整转载页：标记
   `source_kind=official_reprint`。仅收录正文中明确写出发布机关和通告全文的页面。
3. 普通媒体摘要、自媒体转述和只有标题没有正文的页面：不进入 RAG。

## 建议采集范围

- 交通组织调整：单行道、潮汐车道、禁左、封闭施工。
- 临时交通管理：大型活动、节假日、高速施工、恶劣天气。
- 绕行提示：管制路段、起止时间、替代路线。
- 限行政策：仅收录可核验的正式公告，并保留发布日期和有效期。

先采集最近 6 至 12 个月的 50 至 100 篇。知识库重在可追溯，不要为了数量复制同一公告。

## 人工采集格式

新建 `data/manual/traffic_bulletins.jsonl`，每行一篇公告：

```json
{"title":"关于调整青羊区东坡北一路道路交通组织的通告","url":"https://真实原文或官方转载链接","published_at":"2026-05-27","source_kind":"official_reprint","category":"交通组织调整","district":"青羊区","road":"东坡北一路","valid_time":"自2026年6月1日起","text":"粘贴完整通告正文，不要只粘贴媒体导语。"}
```

最低必填字段：`title`、`url`、`published_at`、`text`。脚本会拒绝 `/example/` 占位 URL、
无效链接和过短正文。

## 导入与构建

```powershell
python scripts/import_bulletins.py --input data/manual/traffic_bulletins.jsonl
python scripts/2_build_kb.py
python finetune/build_dataset.py
```

`documents.json` 用于 RAG。公告正文不需要大量重复写入微调权重；微调集只保留少量回答格式样本。

## cdgaj 官网批量保存页

成都市公安局公示公告列表页：

```text
https://cdgaj.chengdu.gov.cn/cdsgaj/jgxx/news_gkgs1615379688854.shtml
```

该站可能对脚本请求返回 `412` 防护页。不要尝试绕过防护。可在普通浏览器中打开列表页，
按需进入通知详情页，使用浏览器“网页，仅 HTML”保存到：

```text
data/manual/cdgaj_html/
```

列表页也应保存，以便脚本从列表链接还原详情页原始 URL。可以先只保存列表页并运行
一次脚本，脚本会生成通知索引、完整列表页清单和已发现的详情页清单；再按链接保存其他
列表页与详情页并重新运行：

```powershell
python scripts/import_saved_cdgaj.py --html-dir data/manual/cdgaj_html
python scripts/2_build_kb.py
python finetune/build_dataset.py
```

导入器会跳过防护验证页、非官方详情页、缺少发布日期的页面和过短正文，并生成：

```text
data/manual/traffic_bulletins.jsonl
data/manual/cdgaj_notice_index.jsonl
data/manual/cdgaj_list_urls.txt
data/manual/cdgaj_urls.txt
data/raw/documents.json
```

## 浏览器采集建议

1. 在官网、“成都交警”或成都官方媒体页面搜索：`成都交警 通告 交通组织 调整`。
2. 打开文章后确认发布机关、发布日期、适用路段、起止时间和正文完整性。
3. 优先复制通告正文，排除网页导航、广告、二维码说明和无关转载内容。
4. 每篇公告保留原始 URL。转载页必须标记 `official_reprint`，不能伪装成官网原文。
