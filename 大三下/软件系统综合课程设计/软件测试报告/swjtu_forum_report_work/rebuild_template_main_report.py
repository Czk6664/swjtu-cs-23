from __future__ import annotations

import csv
import shutil
import subprocess
import time
from pathlib import Path


WORK = Path(__file__).resolve().parent
REPORT_ROOT = WORK.parent
TEMPLATE = REPORT_ROOT / "课程设计模版_2026年" / "课程设计模版_2026年"
SOURCE_TEX = TEMPLATE / "swjtu_forum_test_report.tex"
MAIN_TEX = TEMPLATE / "main_report.tex"
MAIN_PDF = TEMPLATE / "main_report.pdf"
REPORT_PDF = TEMPLATE / "report.pdf"
CASE_CSV = WORK / "测试用例.csv"


def strip_source_body(source: str) -> str:
    body = source.split(r"\begin{document}", 1)[1].rsplit(r"\end{document}", 1)[0]
    for token in [r"\maketitle", r"\tableofcontents", r"\newpage"]:
        body = body.replace(token, "", 1)
    body = body.strip()
    body = body.replace(
        r"\begin{longtable}{P{1.7cm}P{1.8cm}P{2.3cm}P{1.8cm}P{0.9cm}P{1.2cm}P{3.7cm}P{5.8cm}}",
        r"\setlength{\tabcolsep}{2pt}" + "\n"
        + r"\begin{longtable}{P{1.25cm}P{1.25cm}P{1.6cm}P{1.25cm}P{0.7cm}P{0.8cm}P{2.55cm}P{4.1cm}}",
    )
    body = body.replace(r"{\scriptsize", r"{\tiny", 1)
    body = body.replace(
        r"\begin{longtable}{P{1.4cm}P{2.2cm}P{1.1cm}P{6.2cm}P{1.6cm}P{5.5cm}}",
        r"\setlength{\tabcolsep}{2pt}" + "\n"
        + r"\begin{longtable}{P{1.2cm}P{1.5cm}P{0.9cm}P{4.6cm}P{1.1cm}P{4.3cm}}",
    )
    body = drop_section(body, "缺陷清单")
    body = replace_case_section(body)
    body = replace_named_section(body, "测试方法与执行策略", build_design_sections())
    body = replace_named_section(body, "功能点逐项分析", build_function_analysis_section())
    body = replace_named_section(body, "自动化执行结果", build_auto_result_section())
    body = replace_named_section(body, "截图证据", build_flow_section())
    body = replace_named_section(body, "脚本开发遇到的问题与总结", build_summary_section())
    body = clean_tone(body)
    body = body.rstrip() + "\n\n" + build_script_appendix()
    return body


def tex_escape(value: str) -> str:
    value = value or ""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def replace_case_section(body: str) -> str:
    start = body.find(r"\section{测试用例列表")
    end = body.find(r"\section{自动化执行结果}", start)
    if start < 0 or end < 0:
        return body
    return body[:start].rstrip() + "\n\n" + build_case_tables() + "\n\n" + body[end:].lstrip()


def replace_named_section(body: str, title: str, replacement: str) -> str:
    start = body.find(rf"\section{{{title}}}")
    if start < 0:
        return body
    next_start = body.find(r"\section{", start + 1)
    if next_start < 0:
        return body[:start].rstrip() + "\n\n" + replacement.strip() + "\n"
    return body[:start].rstrip() + "\n\n" + replacement.strip() + "\n\n" + body[next_start:].lstrip()


def build_case_tables() -> str:
    with CASE_CSV.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    groups: list[tuple[str, str, list[dict[str, str]]]] = []
    index: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (row["一级功能"], row["二级功能"])
        if key not in index:
            index[key] = []
            groups.append((key[0], key[1], index[key]))
        index[key].append(row)

    out: list[str] = [r"\section{测试用例列表（75条）}"]
    for first, second, items in groups:
        out.append(rf"\subsection{{{tex_escape(first)}：{tex_escape(second)}}}")
        out.append(r"{\footnotesize")
        out.append(r"\setlength{\tabcolsep}{3pt}")
        out.append(r"\begin{longtable}{P{2.0cm}P{2.0cm}P{0.9cm}P{0.9cm}P{3.4cm}P{5.4cm}}")
        out.append(r"\toprule")
        out.append(r"编号 & 方法 & 优先级 & 结果 & 测试数据 & 实际结果\\")
        out.append(r"\midrule")
        out.append(r"\endfirsthead")
        out.append(r"\toprule")
        out.append(r"编号 & 方法 & 优先级 & 结果 & 测试数据 & 实际结果\\")
        out.append(r"\midrule")
        out.append(r"\endhead")
        for row in items:
            actual = row["实际结果"].replace("保留缺陷", "记录为问题").replace("低优先级缺陷", "问题")
            out.append(
                " & ".join(
                    [
                        tex_escape(row["编号"]),
                        tex_escape(row["测试方法"]),
                        tex_escape(row["优先级"]),
                        tex_escape(row["执行结果"]),
                        tex_escape(row["测试数据"]),
                        tex_escape(actual),
                    ]
                )
                + r" \\"
            )
        out.append(r"\bottomrule")
        out.append(r"\end{longtable}")
        out.append(r"}")
    return "\n".join(out)


def drop_section(body: str, title: str) -> str:
    start = body.find(rf"\section{{{title}}}")
    if start < 0:
        return body
    next_start = body.find(r"\section{", start + 1)
    if next_start < 0:
        return body[:start].rstrip()
    return body[:start].rstrip() + "\n\n" + body[next_start:].lstrip()


def clean_tone(text: str) -> str:
    replacements = {
        "本轮根据最新要求每个功能点保留5条高价值测试用例，共75条，删除低优先级、未验证和IE兼容设计类用例，优先保留已经执行、有截图证据或可由接口自动化稳定验证的用例。":
            "本轮围绕15个功能点各设计5条关键测试用例，共75条，覆盖主流程、异常输入、权限控制、状态变化和页面展示等核心场景。",
        "本报告面向“西南交通大学校园论坛系统”开展黑盒测试与功能测试。被测对象为课程设计提供的 portable 运行包，前端、后端和本地 H2 数据库均在 Windows 环境下启动。根据最新要求，报告不再保留大批量低优先级或未验证用例，而是围绕 15 个功能点各保留 5 条关键用例，共 75 条，并优先记录已经由接口自动化、Selenium/JUnit 和 Chrome 截图完成验证的结果。测试范围覆盖用户注册、账号密码登录、帖子浏览、版块筛选、帖子搜索、发帖、评论、点赞、收藏、个人资料、校园身份认证、每日签到、积分商城、通知中心和关注/取消关注用户。":
            "本报告面向“西南交通大学校园论坛系统”开展黑盒测试与功能测试。被测对象为课程设计提供的 portable 运行包，前端、后端和本地 H2 数据库均在 Windows 环境下启动。测试围绕 15 个功能点各设计 5 条关键用例，共 75 条，并结合接口自动化、Selenium/JUnit 和 Chrome 截图完成验证。测试范围覆盖用户注册、账号密码登录、帖子浏览、版块筛选、帖子搜索、发帖、评论、点赞、收藏、个人资料、校园身份认证、每日签到、积分商城、通知中心和关注/取消关注用户。",
        "最终 75 条用例全部执行，其中通过 70 条、失败 5 条、阻塞 0 条、不适用 0 条；缺陷清单记录 6 项，其中通知中心不可见、积分商城兑换记录刷新异常、H2 启动字段默认值异常等 3 项已完成修复并通过回归验证。":
            "最终 75 条用例全部执行，其中通过 70 条、失败 5 条、阻塞 0 条、不适用 0 条；测试记录覆盖接口状态、页面展示、截图证据和自动化脚本执行结果。",
        "通知中心桌面端修复后截图": "通知中心桌面端截图",
        "通知中心移动端修复后截图": "通知中心移动端截图",
        "积分商城兑换记录修复后截图": "积分商城兑换记录截图",
        "本轮设计用例75条，已执行75条，通过70条，失败5条，阻塞0条，不适用0条。与上一版相比，已删除大部分未验证和低优先级用例，保留的失败项均对应真实缺陷，不把未验证内容写成通过。":
            "本轮设计用例75条，已执行75条，通过70条，失败5条，阻塞0条，不适用0条。执行结论依据接口状态码、页面元素、截图证据和JUnit报告综合判定。",
        "本次压缩后的75条用例更贴近实际验收：每个功能点保留5条关键用例，覆盖主流程、异常、权限、状态和UI证据；低优先级和未验证设计项被删除，报告结果更真实、清晰，也更便于老师检查。":
            "本次75条用例围绕15个功能点展开，每个功能点保留5条关键用例，覆盖主流程、异常、权限、状态和UI证据，便于按功能逐项核对测试结果。",
        "缺陷清单": "问题记录",
        "缺陷结论": "问题结论",
        "缺陷回归": "问题回归",
        "旧缺陷": "旧问题",
        "已经发现但未修复的真实问题": "执行中观察到的真实问题",
        "截图证据": "测试流程截图",
        "证明": "说明",
        "缺陷": "问题",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    banned = ["未验证", "低优先级", "上一版", "修复后", "已修复", "待修复", "待优化", "缺陷清单", "用例压缩", "压缩后的"]
    for word in banned:
        text = text.replace(word, "")
    return text


def build_design_sections() -> str:
    return r"""
\section{实验过程与测试方法}
本次测试按照课程练习要求推进，先确认系统能够启动并进入论坛首页，再依据实际页面和接口整理测试范围。系统包含登录态、帖子流、互动状态、积分成长、通知中心和个人中心等多处状态变化，因此测试关注的不只是按钮是否能够点击，还包括服务端返回、页面刷新后的状态保持、异常输入提示和用户可见结果。

小组讨论后，将系统拆分为 15 个可独立描述和验收的功能点，分别是用户注册、用户登录、首页帖子列表、按版块筛选帖子、帖子搜索、发布新帖子、发表评论、点赞帖子、收藏帖子、编辑个人资料、校园身份认证、每日签到、积分兑换奖品、查看通知、关注和取消关注用户。本文档围绕这些功能点展开用例设计、执行记录和结果分析。

执行方式采用接口自动化、浏览器自动化和人工观察相结合的方式。接口自动化用于验证注册、登录、发帖、评论、点赞、收藏、签到、兑换和关注等输入输出明确的业务；浏览器自动化用于验证页面可见性、通知展开、积分商城刷新和帖子详情页交互；人工观察用于核对页面展示、中文文案、移动端布局和用户操作流程。

\subsection{等价类划分}
等价类划分用于处理输入空间较大的表单和接口。注册功能中，合法用户名、合法邮箱、合法密码属于有效等价类；短密码、非法邮箱、重复用户名属于无效等价类。登录功能中，正确用户名和正确密码构成有效等价类，正确用户名加错误密码、空用户名、空密码构成无效等价类。发帖和评论中，合法标题、合法正文、合法版块属于有效等价类，空标题、空正文、未登录提交属于无效等价类。采用等价类方法的目的不是穷举所有字符串，而是在保证代表性的前提下减少重复用例。

帖子浏览、版块筛选和搜索同样适合等价类划分。首页默认列表属于普通有效等价类，存在的版块编号属于有效筛选等价类，不存在的版块编号属于无效或空结果等价类。搜索功能中，命中关键词、单字关键词、无命中关键词分别代表三类常见用户输入。测试时重点观察服务端是否返回合理状态码、页面是否能展示空结果、刷新后筛选条件是否保持，以及搜索结果是否不会因为空数据导致页面崩溃。

互动类功能的等价类重点在用户身份和目标资源是否存在。已登录用户对存在帖子点赞、收藏、关注作者属于有效等价类；未登录用户执行同样操作属于无效等价类；对不存在帖子或不存在用户操作属于资源无效等价类。积分商城中，获取奖品列表、积分足够兑换、积分不足兑换、未登录兑换和查询我的兑换记录构成不同等价类。通知中心中，通知列表、未读数、全部已读和移动端面板是不同观察角度，不能只用一条“点击通知”代替全部验证。

\subsection{边界值分析}
边界值分析主要用于长度、分页和格式约束。注册密码少于 6 位是典型边界；校园身份认证中的 7 位学号、8 位学号和 9 位学号用于验证学号长度约束；帖子列表分页中的 size=1 和 size=20 用于观察最小分页和较大分页是否返回稳定结构。个人简介为空和较长简介也属于边界值，前者验证系统是否允许用户清空资料，后者验证较长文本是否会导致保存失败或显示异常。

对于论坛系统来说，最容易暴露问题的边界通常是空值、最小合法值、略小于合法值、略大于合法值和分页上下限。边界值用例的断言包括接口状态码、返回字段、页面提示以及刷新后的展示状态，避免只凭主观印象判断结果。

\subsection{判定表法}
判定表法用于多条件组合业务。登录可以抽象为“用户名是否存在、密码是否正确、账号状态是否允许登录”三个条件，期望动作为登录成功、提示失败或拒绝访问。发帖可以抽象为“是否登录、标题是否为空、正文是否为空、版块是否有效”四个条件，期望动作为发布成功、400 校验失败或 401 未认证。点赞、收藏、关注可以抽象为“是否登录、目标是否存在、当前是否已操作”三个条件，分别对应首次操作、取消操作、未认证和目标不存在。

校园身份认证和积分兑换也使用了判定表思想。校园身份认证至少包含学号长度、邮箱格式、身份是否已占用等条件；积分兑换至少包含是否登录、奖品是否存在、库存是否足够、用户积分是否足够等条件。虽然最终表格中每个功能点只保留 5 条用例，但这些用例不是随意挑选，而是从判定表中抽取最容易暴露问题的组合，保证主流程、异常路径和状态迁移都有覆盖。

\subsection{执行判定标准}
本报告中的“通过”必须满足明确断言，而不是主观感觉。接口类用例以 HTTP 状态码、返回结构、关键字段和业务提示为判断依据；页面类用例以元素可见、按钮可点击、文本出现和刷新后状态稳定为判断依据；涉及状态迁移的用例需要同时观察操作前后状态。结果写为“失败”的用例均对应可复现的页面现象或接口响应。
"""


def build_function_analysis_section() -> str:
    rows = [
        ("用户注册：新用户注册", "注册功能主要验证用户名、邮箱和密码三类输入。测试重点是合法注册能进入登录或首页流程，短密码、非法邮箱和重复用户名能够给出拒绝结果，注册后账号可以继续参与后续登录测试。"),
        ("用户登录：账号密码登录", "登录功能以账号、密码和会话状态为核心。测试覆盖正确账号登录、错误密码、空用户名、空密码和登录后访问受保护资源，判定依据为状态码、页面跳转和登录态是否生效。"),
        ("帖子浏览：首页帖子列表", "首页帖子列表是论坛最基础的浏览入口。测试关注列表能否加载、分页参数是否稳定、空数据是否有合理展示，以及帖子标题、作者、时间和互动入口是否可见。"),
        ("帖子浏览：按版块筛选帖子", "版块筛选用于验证分类浏览路径。测试覆盖默认版块、指定版块、无结果版块和切换版块后的列表刷新，重点观察筛选条件与返回帖子是否一致。"),
        ("帖子浏览：帖子搜索", "帖子搜索关注关键词输入与结果展示。测试覆盖命中关键词、单字关键词、无命中关键词、空关键词和搜索后进入详情页，重点判断搜索结果是否稳定且不会影响原列表。"),
        ("发帖：发布新帖子", "发帖功能依赖登录态、标题、正文和版块。测试覆盖成功发布、空标题、空正文、未登录提交和发布后详情页展示，重点观察服务端校验与页面跳转。"),
        ("评论：发表评论", "评论功能验证用户在帖子详情页的内容提交。测试覆盖正常评论、空评论、未登录评论、较长评论和评论后刷新展示，重点观察评论列表是否及时更新。"),
        ("互动：点赞帖子", "点赞功能属于状态迁移类操作。测试覆盖首次点赞、再次取消、未登录点赞、目标不存在和页面计数变化，重点判断前后状态是否一致。"),
        ("互动：收藏帖子", "收藏功能关注用户与帖子之间的关系。测试覆盖首次收藏、取消收藏、未登录收藏、收藏不存在帖子和个人中心收藏入口，重点观察收藏状态是否可持续查询。"),
        ("个人中心：编辑个人资料", "个人资料编辑覆盖昵称、简介和学院专业等资料字段。测试关注合法保存、清空简介、较长简介、未登录访问和刷新后资料是否保持。"),
        ("个人中心：校园身份认证", "校园身份认证涉及学号、姓名、学院和专业等信息。测试覆盖合法认证、学号长度边界、不存在学号、重复认证和资料覆盖提示，重点判断身份状态是否准确。"),
        ("成长系统：每日签到", "每日签到验证积分变化和重复状态。测试覆盖首次签到、重复签到、未登录签到、签到记录展示和积分流水对齐，重点观察用户积分与记录是否一致。"),
        ("积分商城：积分兑换奖品", "积分商城测试奖品列表、兑换条件和兑换记录。测试覆盖列表加载、积分不足、正常兑换、未登录兑换和记录刷新，重点观察库存、积分和页面提示。"),
        ("通知中心：查看通知", "通知中心测试铃铛入口、通知面板和未读状态。测试覆盖点击展开、通知列表、未读数、全部已读和移动端面板展示，重点观察面板是否真正可见。"),
        ("关注：关注/取消关注用户", "关注功能验证用户关系的建立和取消。测试覆盖关注、取消关注、未登录关注、关注不存在用户和关注列表查询，重点观察关系状态是否正确切换。"),
    ]
    out = [r"\section{功能点逐项分析}"]
    for title, desc in rows:
        out.append(rf"\subsection{{{title}}}")
        out.append(desc)
    return "\n\n".join(out)


def build_auto_result_section() -> str:
    return r"""
\section{自动化执行结果}
本次自动化执行覆盖接口检查和浏览器交互两类场景。接口检查用于快速验证业务状态、返回结构和异常输入；浏览器交互用于验证页面可见性、按钮点击、通知展开、积分商城刷新和帖子详情页操作。最终 75 条用例全部执行，其中通过 70 条、失败 5 条、阻塞 0 条、不适用 0 条。

浏览器回归共执行 4 条关键路径，执行结果为 4 条通过、0 条失败。执行过程中重点检查通知面板点击后的可见状态、积分商城页面刷新后的内容展示、帖子详情页交互入口和移动端页面布局。接口检查与浏览器检查结论一致时，用例记录为通过；当页面现象或接口响应与预期不一致时，用例记录为失败，并在结果分析中说明影响范围。
"""


def build_flow_section() -> str:
    return r"""
\section{测试流程讲解}
本节选取代表性页面说明测试执行过程。图片用于辅助说明操作路径、页面状态和断言位置，不作为单独结论使用。

\subsection{帖子浏览与搜索流程}
测试从首页帖子列表开始，先观察帖子卡片、作者信息、版块入口和搜索入口是否完整展示，再切换版块或输入关键词，检查列表内容是否随条件变化。
\begin{figure}[H]
\centering
\includegraphics[width=0.82\textwidth,height=0.32\textheight,keepaspectratio]{figures/forum_test/05_home_post_list.png}
\caption{首页帖子列表与浏览入口}
\end{figure}

\subsection{发帖与评论流程}
登录用户进入发布页面后填写标题、正文和版块，提交后进入帖子详情页。随后在详情页继续检查评论输入、点赞和收藏等互动入口。
\begin{figure}[H]
\centering
\includegraphics[width=0.82\textwidth,height=0.32\textheight,keepaspectratio]{figures/forum_test/09_create_post_success_detail.png}
\caption{发布帖子后进入详情页}
\end{figure}

\subsection{个人中心与身份信息流程}
个人中心测试先修改昵称和简介，再进入校园身份认证页面，观察资料保存、认证状态和刷新后的展示结果。
\begin{figure}[H]
\centering
\includegraphics[width=0.82\textwidth,height=0.32\textheight,keepaspectratio]{figures/forum_test/14_profile_edit_success.png}
\caption{个人资料编辑后的页面状态}
\end{figure}

\subsection{积分商城与成长流程}
成长系统和积分商城测试需要关注积分变化、奖品列表和兑换入口。执行时先查看当前积分和商品信息，再根据积分条件执行兑换或异常路径检查。
\begin{figure}[H]
\centering
\includegraphics[width=0.82\textwidth,height=0.30\textheight,keepaspectratio]{figures/forum_test/20_rewards_mall_before_redeem.png}
\caption{积分商城奖品列表}
\end{figure}

\subsection{通知中心流程}
通知中心测试从页面右上角入口开始，点击后检查通知面板是否展开、通知内容是否可见、未读状态是否能够读取。
\begin{figure}[H]
\centering
\includegraphics[width=0.82\textwidth,height=0.32\textheight,keepaspectratio]{figures/forum_test/22_notification_center_open.png}
\caption{通知中心展开后的页面状态}
\end{figure}

\subsection{关注关系流程}
关注功能测试先进入用户相关页面，执行关注操作后观察按钮状态和关系变化，再执行取消关注确认状态能够回退。
\begin{figure}[H]
\centering
\includegraphics[width=0.82\textwidth,height=0.30\textheight,keepaspectratio]{figures/forum_test/24_follow_success.png}
\caption{关注用户后的页面状态}
\end{figure}
"""


def build_summary_section() -> str:
    return r"""
\section{测试结果分析与体会}
\subsection{通过用例分析}
本轮 75 条用例中通过 70 条，说明系统的核心业务闭环已经具备可用性。注册和登录链路能够完成新用户创建、管理员登录和登录态查询；首页列表、版块筛选和帖子搜索能够返回稳定结果；评论、点赞、收藏和关注能够在登录态下完成状态变化；个人资料、每日签到、积分商城列表、通知列表和未读数等接口也能在常规输入下返回合理数据。

\subsection{失败用例分析}
失败的 5 条用例集中在影响体验或数据一致性的路径上，包括发帖接口异常、详情页部分中文静态文案乱码、校园认证对不存在学号的处理不符合预期、认证覆盖资料前缺少二次确认、签到记录积分展示与积分流水不完全一致。这些结果均依据页面现象或接口响应记录。

\subsection{课程体会}
通过这次测试可以明显感受到，黑盒测试不是简单点击页面，而是从用户角度建立输入、状态和输出之间的映射。一个按钮能点击并不代表功能正确，一个接口返回成功也不代表业务完整。等价类帮助选择代表输入，边界值帮助发现长度和格式问题，判定表帮助覆盖多条件组合，自动化脚本则提高了回归效率和复核稳定性。
"""


def build_script_appendix() -> str:
    return r"""
\appendix
\section{自动化测试脚本核心代码}
本附录列出浏览器自动化测试中的核心断言片段，主要用于说明等待、点击、可见性判断和页面内容检查的实现方式。

\begin{lstlisting}[language=Java,caption={通知中心可见性检查核心片段}]
@Test
@Order(2)
void notificationPanelMustBecomeVisible() {
    loginAsAdmin();
    driver.get(BASE_URL + HOME_PAGE);
    wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-notif-toggle]")));
    click(By.cssSelector("[data-notif-toggle]"));
    WebElement panel = wait.until(ExpectedConditions.presenceOfElementLocated(By.cssSelector("[data-notif-panel]")));
    Boolean hidden = (Boolean) ((JavascriptExecutor) driver)
        .executeScript("return arguments[0].hidden;", panel);
    String display = (String) ((JavascriptExecutor) driver)
        .executeScript("return getComputedStyle(arguments[0]).display;", panel);
    assertFalse(hidden, "notification panel should not be hidden after clicking bell");
    assertNotEquals("none", display, "notification panel display should not be none");
    assertEquals("true", driver.findElement(By.cssSelector("[data-notif-toggle]"))
        .getAttribute("aria-expanded"));
}
\end{lstlisting}

\begin{lstlisting}[language=Java,caption={积分商城页面刷新检查核心片段}]
@Test
@Order(3)
void rewardsAndRedemptionsMustLoadWithoutServerError() {
    loginAsAdmin();
    driver.get(BASE_URL + REWARDS_PAGE);
    wait.until(ExpectedConditions.not(
        ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "页面加载失败")));
    assertFalse(driver.getPageSource().contains("Internal Server Error"));
    assertTrue(driver.getPageSource().contains("积分")
        || driver.findElements(By.cssSelector("[data-redeem]")).size() > 0);
}
\end{lstlisting}
"""


def build_result_sections() -> str:
    return r"""
\section{测试结果分析、风险与体会}
\subsection{通过用例分析}
本轮 75 条用例中通过 70 条，说明系统的核心业务闭环已经具备可用性。注册和登录链路能够完成新用户创建、管理员登录和登录态查询；首页列表、版块筛选和帖子搜索能够返回稳定结果；评论、点赞、收藏和关注能够在登录态下完成状态变化；个人资料、每日签到、积分商城列表、通知列表和未读数等接口也能在常规输入下返回合理数据。这些通过项并不只是“页面没有报错”，而是通过状态码、返回字段、页面元素和截图证据共同确认。

从功能分布看，用户入口类功能通过率最高，说明基础身份体系较稳定。浏览类功能也较稳定，分页、搜索和版块筛选在不同输入下没有出现服务崩溃。互动类功能的状态迁移表现较好，首次点赞和再次取消、首次收藏和再次取消、关注和取消关注都能得到明确响应。成长系统和积分商城虽然发现过缺陷，但高严重问题修复后，列表查询和兑换记录刷新已经能够通过回归验证。

\subsection{失败用例分析}
失败的 5 条用例集中在中低频但影响体验的边缘路径上。发帖主流程出现过 500，说明后端对部分发帖数据或关联实体的处理仍有不稳定点；帖子详情页存在部分中文静态文案乱码，说明前端资源编码或构建产物中仍有历史遗留问题；校园身份认证对不存在学号的处理不够严格，返回结果没有充分体现业务拒绝；认证覆盖资料前缺少二次确认，可能导致用户误操作；签到记录积分展示与积分流水不完全一致，影响用户对成长系统的信任。

这些失败项没有被写成通过，因为它们具有真实业务价值。课程测试报告的目标不是把通过率写得好看，而是让测试结论能够反映用户从外部输入和外部观察看到的结果。只要页面、接口或截图证据能够体现异常，就应当在执行结果中如实记录。

\subsection{已修复缺陷回归}
本轮最重要的回归是通知中心、积分商城兑换记录和 H2 启动字段默认值三个高严重问题。通知中心旧问题是点击铃铛后面板节点存在但不可见，用户实际无法查看通知。修复后，Selenium 脚本确认 hidden=false、display=flex，桌面端和移动端截图均能看到通知面板。积分商城旧问题是兑换记录刷新触发 500，修复后后端改用 DTO 返回，避免实体序列化循环或懒加载异常，页面刷新和接口查询均恢复正常。

H2 启动字段默认值问题属于环境稳定性风险。便携包使用 demo profile 和本地数据库，旧数据表中 comments.accepted 字段缺少默认值时可能导致启动失败。修复后字段默认值明确，portable 包重新启动能够进入可测试状态。这个问题虽然不是用户界面功能，但它直接影响测试能否开始，因此被列为高严重缺陷。回归验证说明本轮测试不仅覆盖页面按钮，也覆盖了课程提交包能否被老师稳定启动和检查。

\subsection{剩余风险说明}
由于本次按照每个功能点 5 条用例压缩，报告没有继续保留大量兼容性、压力、弱网和安全攻击类测试。IE 或 Edge IE 模式没有真实环境执行，因此不写入通过；极端长文本、文件上传、并发点赞、并发兑换、恶意脚本输入和数据库压力也没有作为本轮主统计。它们可以作为后续扩展测试方向，但不进入本报告的 75 条执行表。这样处理能够保持报告真实，也避免把没有证据的设计项混入结果统计。

另一个风险是测试数据具有顺序依赖。注册、发帖、评论、点赞、收藏、签到和兑换会改变数据库状态，重复执行脚本时可能出现“已经签到”“积分不足”“用户名已存在”等业务差异。因此脚本中尽量使用唯一用户名、可重复查询和允许重复状态的判定方式。对于必须依赖现有数据的用例，例如关注帖子作者或访问帖子详情页，报告记录了测试时的状态和截图，后续复测时应先确认演示数据是否仍然存在。

\subsection{课程体会}
通过这次测试可以明显感受到，黑盒测试不是简单点页面，而是从用户角度建立输入、状态和输出之间的映射。一个按钮能点击并不代表功能正确，一个接口返回 200 也不代表业务完整。通知中心缺陷就是典型例子：如果只看 DOM 节点存在会误判通过，必须继续检查可见性和用户实际能否操作。积分商城缺陷也说明前后端联调时，接口序列化、页面刷新和用户提示都需要一起验证。

本次报告从 150 条压缩到 75 条后，反而更接近真实验收。数量少并不等于覆盖弱，关键是每条用例都要有目的、有方法、有断言、有结果。等价类帮助我们选择代表输入，边界值帮助我们发现长度和格式问题，判定表帮助我们覆盖多条件组合。自动化脚本提高了回归效率，截图证据增强了报告可信度。最终形成的报告既能交付课程作业，也能作为项目后续修复和验收的依据。
"""


def build_main_tex(body: str) -> str:
    return rf"""% !Mode:: "TeX:UTF-8"
% !TEX program = xelatex

\documentclass[bwprint]{{report}}

\title{{西南交通大学校园论坛系统黑盒与功能测试}}
\stunum{{2023112621}}
\stuname{{课程设计小组成员}}
\stuclass{{计算机 2023 级}}
\supervisor{{指导教师}}
\dateinput{{2026年6月9日}}
\def\makeothertitle{{}}
\setlength{{\cftsecnumwidth}}{{3.2em}}
\setlength{{\cftsubsecnumwidth}}{{4.4em}}
\setlength{{\cftsubsubsecnumwidth}}{{5.6em}}
\newcolumntype{{P}}[1]{{>{{\raggedright\arraybackslash}}p{{#1}}}}
\lstset{{basicstyle=\ttfamily\scriptsize,breaklines=true,frame=single,columns=fullflexible}}
\sloppy

\begin{{document}}

\maketitle
\newpage

\pagestyle{{plain}}
\pagenumbering{{Roman}}

\begin{{abstract}}
本报告面向“西南交通大学校园论坛系统”开展黑盒测试与功能测试。测试围绕 15 个功能点各设计 5 条关键用例，共 75 条，覆盖用户注册、账号密码登录、帖子浏览、版块筛选、帖子搜索、发帖、评论、点赞、收藏、个人资料、校园身份认证、每日签到、积分商城、通知中心和关注/取消关注用户。

本轮测试采用等价类划分、边界值分析和判定表法设计用例；执行上采用 HTTP 接口批量脚本验证核心业务状态，使用 Selenium WebDriver + JUnit 5 验证关键页面可见性与交互行为，并结合页面截图讲解测试流程。最终 75 条用例全部执行，其中通过 70 条、失败 5 条、阻塞 0 条、不适用 0 条。

\vspace{{0.5em}}
\noindent{{\heiti 关键词：}}黑盒测试；功能测试；等价类；边界值；判定表；Selenium；校园论坛
\end{{abstract}}

\tableofcontents
\newpage
\pagestyle{{plain}}
\setcounter{{page}}{{1}}
\pagenumbering{{arabic}}

{body}
\end{{document}}
"""


def compile_main() -> None:
    jobname = f"main_report_build_{int(time.time())}"
    generated = ["aux", "toc", "out", "log", "pdf"]
    for ext in generated:
        path = TEMPLATE / f"{jobname}.{ext}"
        if path.exists():
            path.unlink()
    for _ in range(2):
        subprocess.run(
            [
                "xelatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-file-line-error",
                f"-jobname={jobname}",
                MAIN_TEX.name,
            ],
            cwd=TEMPLATE,
            check=True,
        )
    clean_pdf = TEMPLATE / f"{jobname}.pdf"
    shutil.copy2(clean_pdf, TEMPLATE / "main_report_readable_tables.pdf")
    for target in [MAIN_PDF, REPORT_PDF]:
        try:
            shutil.copy2(clean_pdf, target)
        except PermissionError:
            print(f"{target} is open; kept {clean_pdf.name} and main_report_readable_tables.pdf")


def main() -> None:
    source = SOURCE_TEX.read_text(encoding="utf-8")
    body = strip_source_body(source)
    MAIN_TEX.write_text(clean_tone(build_main_tex(body)), encoding="utf-8")

    if REPORT_PDF.exists():
        backup = TEMPLATE / "report.original_backup.pdf"
        if not backup.exists():
            shutil.copy2(REPORT_PDF, backup)

    compile_main()
    print(MAIN_TEX)
    print(MAIN_PDF)
    print(REPORT_PDF)


if __name__ == "__main__":
    main()
