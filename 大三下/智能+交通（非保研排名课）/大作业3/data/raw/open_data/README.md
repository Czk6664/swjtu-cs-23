# open_data

<!-- directory-guide:start -->
## 本层内容介绍

这里是“智能+交通”课程下的“open_data”目录，主要用于整理项目使用的数据或样例输入。

**阅读建议：**先查上级说明中的数据来源、字段和处理方式，再查看具体文件；此处不一定包含完整数据集。

**项目背景与使用步骤：**请继续阅读本页下方的“原有项目说明”，其中保留了项目自己的功能介绍、环境要求或运行方法。

### 本层有哪些内容

本目录及子目录共收录 **11 份文件**（不含各层 README）；下面先介绍本层直接可见的内容。

- **配置及其他配套文件（3 份）**：[chengdu_bus_lines_stops.jsonl](chengdu_bus_lines_stops.jsonl)、[manifest.json](manifest.json)等；完整列表见本页导航。
- **表格与数据（7 份）**：[chengdu_highway_toll_stations.csv](chengdu_highway_toll_stations.csv)、[chengdu_metro_tram_station_names.xls](chengdu_metro_tram_station_names.xls)等；完整列表见本页导航。
- **文档与说明（1 份）**：[道路交通安全法.md](%E9%81%93%E8%B7%AF%E4%BA%A4%E9%80%9A%E5%AE%89%E5%85%A8%E6%B3%95.md)。

<!-- directory-guide:end -->

所属课程：[智能+交通](../../../../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [chengdu_bus_lines_stops.jsonl](chengdu_bus_lines_stops.jsonl)
- [chengdu_highway_toll_stations.csv](chengdu_highway_toll_stations.csv)
- [chengdu_metro_tram_station_names.xls](chengdu_metro_tram_station_names.xls)
- [chenghua_rail_transit.csv](chenghua_rail_transit.csv)
- [jianyang_parking_fees.csv](jianyang_parking_fees.csv)
- [longquanyi_onstreet_parking.csv](longquanyi_onstreet_parking.csv)
- [manifest.json](manifest.json)
- [shuangliu_bus_lines.jsonl](shuangliu_bus_lines.jsonl)
- [tianfu_parking_locations.csv](tianfu_parking_locations.csv)
- [xindu_bus_lines.csv](xindu_bus_lines.csv)
- [道路交通安全法.md](%E9%81%93%E8%B7%AF%E4%BA%A4%E9%80%9A%E5%AE%89%E5%85%A8%E6%B3%95.md)

[返回上级目录](../README.md)

## 原有项目说明

# 成都公共开放数据下载清单

平台会拦截自动化文件下载。请在 Chrome 中打开对应详情页，点击“数据下载”，
优先选择 CSV 或 JSON 文件，并将文件下载到本目录。

## 已归档

2026-06-01 下载的文件已统一重命名并归档到本目录。机器可读清单见
[`manifest.json`](manifest.json)。

- 已归档 9 个交通数据集和 1 份开放目录压缩包。
- `chengdu_bus_lines_stops.jsonl` 为平台部分导出：现有 5,000 条，目录标称 28,637 条。
- CSV 文件保持平台原始 GB18030 编码，避免修改原始数据。
- 平台 JSON 导出包含两行：第一行为字段定义，第二行为记录数组，因此使用 `.jsonl` 后缀。

## 优先下载

| 本地建议文件名 | 官方目录 | 用途 |
| --- | --- | --- |
| `chengdu_bus_lines_stops.jsonl` | [成都公交线路站点基本信息](https://www.chengdu.gov.cn/data/oportal/catalog/1558519985475203404) | 公交线路、站点和换乘问答 |
| `chengdu_metro_tram_station_names.xls` | [地铁、有轨电车站名称信息](https://www.chengdu.gov.cn/data/oportal/catalog/UaLmwWB1EeeGP8z9ublHbw829) | 地铁站点问答、路线规划地点匹配 |
| `chengdu_highway_toll_stations.csv` | [公路收费站信息](https://www.chengdu.gov.cn/data/oportal/catalog/old_X5XqcWB1Eee6GM_IHOS5CQ1084) | 自驾、高速收费站问答 |
| `tianfu_parking_locations.csv` | [停车场位置信息](https://www.chengdu.gov.cn/data/oportal/catalog/e1591d581f84462c995f730a15c44d90) | 停车场位置和自驾建议 |
| `longquanyi_onstreet_parking.csv` | [路内停车泊位信息](https://www.chengdu.gov.cn/data/oportal/catalog/ae6bca3f0bfa47788cc228dd540702e3) | 路内停车问答 |
| `jianyang_parking_spaces.csv` | [简阳市停车泊位情况](https://www.chengdu.gov.cn/data/oportal/catalog/050414e417df4183a1dde3484cf94d0f) | 停车问答样例 |
| `jianyang_parking_fees.csv` | [简阳市机动车停车收费](https://www.chengdu.gov.cn/data/oportal/catalog/9bee1336d29a4c9fadbf7cf8b90c7bee) | 停车收费问答样例 |

## 可选补充

| 本地建议文件名 | 官方目录 | 用途 |
| --- | --- | --- |
| `pujiang_bus_lines.csv` | [蒲江县公交线路信息](https://www.chengdu.gov.cn/data/oportal/catalog/f98951d6ccdc4c85bf8e318483fac618) | 区县公交补充样例 |
| `xindu_bus_lines.csv` | [新都区公交线路信息](https://www.chengdu.gov.cn/data/oportal/catalog/9a757f26063e4953a30a354900bde7ae) | 区县公交补充样例 |
| `shuangliu_bus_lines.csv` | [双流区公交线路](https://www.chengdu.gov.cn/data/oportal/catalog/ba1124670aab4e079f18b82e5cfe85ca) | 区县公交补充样例 |
| `chenghua_rail_transit.csv` | [轨道交通信息](https://www.chengdu.gov.cn/data/oportal/catalog/e82bac075d6b4ebcafe42ccb9896d8db) | 成华区轨道交通补充样例 |
| `dujiangyan_onstreet_parking.csv` | [都江堰市路内停车泊位统计表台账](https://www.chengdu.gov.cn/data/oportal/catalog/755e85f1d2144184a0b77e81e87895f1) | 区县停车补充样例 |
| `shuangliu_road_construction.xls` | [成都市双流区占用城市道路施工信息表](https://www.chengdu.gov.cn/data/oportal/catalog/987126411c344d31b3e6e4aea9bc35b9) | 施工绕行问答样例 |
| `wuhou_temporary_road_occupation.csv` | [临时占用城市道路（含人行道）许可信息](https://www.chengdu.gov.cn/data/oportal/catalog/017b14b09a924aab9255ec47462f7c74) | 道路占用提醒样例 |
| `chengdu_taxi_companies.csv` | [五城区巡游出租汽车经营企业明细信息](https://www.chengdu.gov.cn/data/oportal/catalog/2a20faf21add4bf9806650e23134b913) | 出租车企业查询 |
| `chengdu_ride_hailing_companies.json` | [业户信息_道路运输_网络预约出租汽车企业](https://www.chengdu.gov.cn/data/oportal/catalog/3c0cd788a6474aaaab923bb1af031955) | 网约车企业查询 |

## 不建议下载

- `市交通运输局_公共数据开放_地面公交`：约 2.8 亿条实时公交 GPS 数据，
  含车牌字段，不适合作为本课程原型的默认本地数据。
- `高新区停车场交易信息`：约 5800 万条交易记录，体积大，且不是路线规划所需的基础信息。
- `高新区共享单车基础信息`、`高新区城市道路基础信息`：有条件开放，需要申请后再评估。

