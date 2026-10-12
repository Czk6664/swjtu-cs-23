from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "ppt_generated_images"
OUT.mkdir(exist_ok=True)

W, H = 1920, 1080
BLUE = "#308FF0"
DEEP1 = "#0070C0"
DEEP2 = "#3354B5"
ACCENT = "#0E6BC9"
LINE = "#316AEF"
GREY = "#7E7E7E"
ORANGE = "#ED7D31"
GREEN = "#70AD47"
YELLOW = "#FFC000"
INK = "#172437"

FONT_REG = r"C:\Windows\Fonts\simhei.ttf"
FONT_BOLD = r"C:\Windows\Fonts\simhei.ttf"
FONT_ARIAL = r"C:\Windows\Fonts\arial.ttf"
FONT_ARIAL_BOLD = r"C:\Windows\Fonts\arialbd.ttf"


def font(size, bold=False, arial=False):
    return ImageFont.truetype(FONT_ARIAL_BOLD if arial and bold else FONT_ARIAL if arial else FONT_BOLD if bold else FONT_REG, size)


F = {
    "cover_title": font(86, True),
    "cover_sub": font(38),
    "h1": font(64, True),
    "h2": font(26),
    "body": font(27),
    "body_b": font(29, True),
    "small": font(22),
    "tiny": font(18),
    "num": font(128, True, True),
    "side": font(21, False, True),
    "page": font(24, True, True),
}


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def gradient(size, c1, c2, horizontal=False):
    w, h = size
    img = Image.new("RGB", size)
    p = img.load()
    a = hex_to_rgb(c1)
    b = hex_to_rgb(c2)
    for y in range(h):
        for x in range(w):
            t = (x / (w - 1)) if horizontal else (y / (h - 1))
            p[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return img


def add_shadow(base, box, radius=28, blur=24, color=(0, 100, 216, 85), offset=(0, 10)):
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(shadow)
    x1, y1, x2, y2 = box
    ox, oy = offset
    d.rounded_rectangle((x1 + ox, y1 + oy, x2 + ox, y2 + oy), radius=radius, fill=color)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(shadow)


def draw_wrapped(draw, text, xy, fnt, fill, max_width, line_gap=10, max_lines=None):
    x, y = xy
    lines = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            test = cur + ch
            if draw.textlength(test, font=fnt) <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip("，。；、 ") + "..."
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def campus_bg():
    img = gradient((W, H), "#0B4EA2", "#4DB5FF", horizontal=True).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(2026)
    for i in range(10):
        x = 120 + i * 190
        bh = random.randint(180, 360)
        d.rounded_rectangle((x, H - 220 - bh, x + 115, H - 220), radius=10,
                            fill=(255, 255, 255, 35), outline=(255, 255, 255, 80), width=2)
        for wy in range(H - 200 - bh, H - 250, 52):
            d.rectangle((x + 22, wy, x + 92, wy + 14), fill=(255, 255, 255, 45))
    for r in range(6):
        d.arc((-250 + r * 35, 460 + r * 20, 900 + r * 95, 1240 + r * 30),
              205, 352, fill=(255, 255, 255, 55), width=4)
    for _ in range(90):
        x = random.randint(0, W)
        y = random.randint(0, H)
        d.ellipse((x, y, x + 3, y + 3), fill=(255, 255, 255, 70))
    overlay = gradient((W, H), "#004B9B", "#2E8CFF", horizontal=True).convert("RGBA")
    overlay.putalpha(135)
    img.alpha_composite(overlay)
    return img


def logo(draw, x=W - 160, y=46, text=True):
    draw.rounded_rectangle((x, y, x + 78, y + 78), radius=18, fill=BLUE, outline=(255, 255, 255, 210), width=3)
    draw.text((x + 12, y + 7), "SWJTU", font=font(14, True, True), fill="white")
    draw.line((x + 16, y + 44, x + 62, y + 44), fill="white", width=5)
    draw.arc((x + 18, y + 26, x + 60, y + 68), 0, 180, fill="white", width=4)
    if text:
        draw.text((x + 94, y + 16), "交大论坛", font=font(34, True), fill=INK)


def content_base(page_no, chapter=""):
    random.seed(1000 + page_no)
    img = Image.new("RGBA", (W, H), (245, 250, 255, 255))
    d = ImageDraw.Draw(img, "RGBA")
    left_w = 760
    left = gradient((left_w, H), DEEP1, DEEP2, horizontal=False).convert("RGBA")
    dl = ImageDraw.Draw(left, "RGBA")
    for _ in range(16):
        cx = random.randint(-100, left_w + 100)
        cy = random.randint(40, H - 40)
        r = random.randint(45, 150)
        dl.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, random.randint(14, 35)))
    for _ in range(7):
        dl.line((random.randint(0, left_w), random.randint(0, H), random.randint(0, left_w), random.randint(0, H)),
                fill=(255, 255, 255, 35), width=3)
    img.alpha_composite(left, (0, 0))
    if chapter:
        d.text((56, 50), chapter, font=F["num"], fill=(255, 255, 255, 80))
    card = (700, 88, 1770, 990)
    add_shadow(img, card)
    d.rounded_rectangle(card, radius=44, fill="white", outline=(212, 233, 250, 255), width=3)
    d.line((1832, 125, 1832, 935), fill=LINE, width=3)
    y = 180
    for ch in "SOUTHWEST JIAOTONG UNIVERSITY":
        d.text((1850, y), ch, font=F["side"], fill=ACCENT)
        y += 25
    d.text((1712, 1002), f"{page_no:02d}", font=F["page"], fill=BLUE)
    logo(d, 1580, 42)
    return img, d, card


def draw_title(d, card, title, subtitle=""):
    x1, y1, _, _ = card
    d.text((x1 + 70, y1 + 58), title, font=F["h1"], fill=BLUE)
    if subtitle:
        d.text((x1 + 74, y1 + 136), subtitle, font=F["h2"], fill=GREY)
    d.rounded_rectangle((x1 + 74, y1 + 184, x1 + 360, y1 + 190), radius=4, fill=ACCENT)
    return y1 + 225


def bullet_list(d, items, x, y, width, color=BLUE, fnt=None, gap=18):
    fnt = fnt or F["body"]
    for item in items:
        d.ellipse((x, y + 8, x + 14, y + 22), fill=color)
        y = draw_wrapped(d, item, (x + 28, y), fnt, INK, width - 28, 8)
        y += gap
    return y


def simple_card(d, box, title, lines, accent=BLUE):
    d.rounded_rectangle(box, radius=26, fill=(247, 252, 255, 255), outline=(205, 229, 247, 255), width=2)
    x1, y1, x2, _ = box
    d.ellipse((x1 + 28, y1 + 26, x1 + 74, y1 + 72), fill=accent)
    d.text((x1 + 92, y1 + 28), title, font=F["body_b"], fill=INK)
    bullet_list(d, lines, x1 + 34, y1 + 92, x2 - x1 - 68, accent, F["small"], 10)


def cover():
    img = campus_bg()
    d = ImageDraw.Draw(img, "RGBA")
    logo(d, W - 230, 64)
    title = "交大论坛"
    tw = d.textlength(title, font=F["cover_title"])
    d.text(((W - tw) / 2, 300), title, font=F["cover_title"], fill=(255, 255, 255, 255),
           stroke_width=2, stroke_fill=(0, 60, 130, 120))
    sub = "交大论坛系统设计与实现"
    tw = d.textlength(sub, font=F["cover_sub"])
    d.text(((W - tw) / 2, 420), sub, font=F["cover_sub"], fill="white")
    info = ["软件系统综合课程设计", "西南交通大学 · 计算机与人工智能学院", "团队成员：程泽凯、金井直、赵祺、董然", "2026年6月"]
    y = 525
    for t in info:
        tw = d.textlength(t, font=font(26))
        d.text(((W - tw) / 2, y), t, font=font(26), fill=(255, 255, 255, 235))
        y += 54
    d.rounded_rectangle((0, H - 82, W, H), radius=0, fill=(255, 255, 255, 160))
    foot = "交大蓝主题 · 校园社区 · 前后端分离 · MySQL 部署"
    tw = d.textlength(foot, font=font(24, True))
    d.text(((W - tw) / 2, H - 56), foot, font=font(24, True), fill="#1D54B1")
    return img


SLIDES = [
    ("目录", "汇报结构", ["项目背景与需求分析", "软件过程与开发计划", "系统建模：用例图、活动图、类图、时序图", "系统架构与数据库设计", "核心功能模块演示", "测试、部署与总结"]),
    ("项目背景", "研究背景与问题", ["校园信息分散在 QQ 群、微信群、贴吧等平台，缺少统一聚合入口", "通用社交平台难以覆盖课程互助、考研保研、失物招领等校园场景", "传统论坛缺少成长激励和运营治理机制，内容生态难以持续"]),
    ("需求工程", "需求分析方法", ["需求导出：用户访谈、问卷调查、竞品分析", "需求分析：识别功能需求、非功能需求和约束条件", "需求描述：输出需求规格说明书", "需求验证：评审一致性、完整性和可实现性", "核心需求：账号、发帖、评论、搜索、推荐、成长、后台治理"]),
    ("软件过程", "增量式开发模型", ["增量 1：注册登录、帖子 CRUD、评论、板块、点赞收藏", "增量 2：推荐算法、签到积分、等级体系、积分商城、关注通知", "增量 3：管理后台、内容审核、举报处理、推荐权重调控、服务器上线"]),
    ("技术选型", "前后端技术栈总览", ["前端：Vite 5 多页面应用，原生 HTML/CSS/JS，Anime.js 动效", "后端：Java 17 + Spring Boot 3.2 + Spring Security + JPA", "数据库：MySQL 8，utf8mb4 字符集，JPA 实体映射", "部署：阿里云服务器、Nginx 反向代理、systemd 后端守护"]),
    ("系统建模①", "用例图：需求视图", ["普通用户：注册登录、浏览帖子、发布帖子、评论、点赞、收藏、签到、兑换、关注、举报", "管理员/版主：审核内容、管理用户、维护板块、处理举报、配置推荐策略", "系统自动：计算热度、更新推荐排序、发送通知、记录积分流水"]),
    ("系统建模②", "活动图：行为视图", ["发帖流程：填写内容、选择板块、上传图片、提交审核、保存帖子、更新经验", "推荐加载流程：获取标签偏好、浏览历史、关注关系，合并后加权排序", "异常流程：内容不合规返回原因，用户修改后重新提交"]),
    ("系统建模③", "类图：结构视图", ["核心实体：User、Post、Comment、Section、Circle、RewardItem、Report、Notification", "关系：用户发布帖子，帖子拥有评论，板块包含帖子，用户加入圈子", "互动实体：PostLike、PostFavorite、UserFollow、DailyCheckIn、PointsHistory"]),
    ("系统建模④", "时序图：交互视图", ["登录：前端提交账号密码，后端校验并签发 JWT，后续请求携带 Token", "发帖：前端提交表单和图片，后端校验权限、保存帖子、写入积分流水", "互动：点赞/收藏接口返回当前状态，前端局部更新按钮与数量"]),
    ("系统架构", "B/S 三层与前后端分离", ["浏览器访问 Nginx，Nginx 提供静态资源并反向代理 /api", "Spring Boot 承担业务逻辑、权限控制和 REST 接口", "MySQL 保存用户、帖子、评论、积分、举报、通知等业务数据", "上传图片通过 /uploads 路径由后端管理并经 Nginx 代理展示"]),
    ("数据库设计", "概念模型与逻辑表", ["用户与帖子：users、posts、sections、comments", "互动与社交：post_likes、post_favorites、user_follows、notifications", "成长与商城：daily_check_ins、points_history、reward_items、redemption_requests", "治理与运营：reports、operation_logs、recommendation_configs"]),
    ("功能演示①", "首页推荐流", ["首页支持最新/最热排序和刷新按钮，帖子列表局部更新", "SWJTU 热词云呈现校园热点话题", "移动端顶部栏自动收起/出现，减少屏幕占用", "帖子卡片展示作者、板块、时间、摘要、图片和互动数"]),
    ("功能演示②", "帖子与互动", ["发帖支持 PNG/JPG 图片，最多 9 张", "详情页支持评论、点赞、收藏、举报", "点赞和收藏状态会回显，取消操作不刷新页面", "点击头像进入对方公开主页，查看其发布的帖子"]),
    ("功能演示③", "成长体系", ["每日签到获得积分，当天按钮置灰，次日恢复", "等级由经验值驱动，发帖、评论、获赞均可增长", "积分商城支持商品兑换，管理员维护商品上下架", "徽章系统展示用户成就，增强持续参与动机"]),
    ("功能演示④", "社交与通知", ["关注/取消关注用户，个人中心展示关注列表", "通知中心聚合评论、互动、关注和系统通知", "公开主页展示头像、昵称、等级、徽章和发帖历史", "社交关系会影响推荐流权重"]),
    ("功能演示⑤", "管理后台", ["数据总览：用户、帖子、评论、举报、积分商品等指标", "内容治理：举报处理、帖子隐藏与恢复", "用户管理：禁用、恢复、角色管理", "积分商品管理：上架、下架、库存和积分维护"]),
    ("详细设计", "安全架构与 AOP", ["JWT 无状态认证：登录签发 Token，请求携带 Token，服务端校验后放行", "RBAC 权限模型：USER、MODERATOR、ADMIN 分层授权", "Spring Security 与方法级权限保护管理员接口", "统一异常处理返回友好错误，避免暴露敏感堆栈"]),
    ("软件测试", "质量保证策略", ["后端：JUnit 5 + Spring Boot Test，覆盖 Service 核心业务", "前端：运行时安全测试和构建测试，检查 XSS 风险", "系统测试：注册、登录、发帖、图片、评论、点赞、收藏、后台治理全链路", "部署测试：阿里云 Nginx + systemd + MySQL 公网验证"]),
    ("系统部署", "部署架构总览", ["公网入口：Nginx 监听 8082，提供前端静态资源", "后端服务：Spring Boot 监听 127.0.0.1:8081，由 systemd 守护", "数据库：MySQL 8 本机部署，不对公网开放", "更新流程：git pull、后端打包重启、前端构建、Nginx reload"]),
    ("知识应用", "课程知识全景映射", ["软件过程：采用增量模型，分阶段交付核心、增强和运营功能", "需求工程：从校园痛点推导功能需求和非功能需求", "系统建模：用例图、活动图、类图、时序图表达系统视图", "详细设计：接口、数据库、安全、错误处理和部署均形成文档"]),
    ("创新亮点", "项目特色总结", ["真实校园论坛氛围：交大蓝主题、校园热词、圈子和板块结构", "动效体验：卡片上浮、提示淡入淡出、移动端导航滚动收起", "完整成长闭环：签到、积分、等级、徽章、商城兑换", "运营治理闭环：举报、审核、用户管理、推荐策略和数据看板"]),
]


def make_content(idx, title, subtitle, bullets):
    chapter = str(((idx - 1) // 4) + 1 if idx not in (2, 22) else "")
    img, d, card = content_base(idx, chapter)
    y = draw_title(d, card, title, subtitle)
    x1, y1, x2, y2 = card
    if idx == 2:
        y += 15
        for n, b in enumerate(bullets, 1):
            cy = y + n * 90
            d.ellipse((x1 + 84, cy - 18, x1 + 134, cy + 32), fill=BLUE if n == 1 else (48, 143, 240, 90))
            d.text((x1 + 101, cy - 13), str(n), font=font(24, True, True), fill="white")
            d.text((x1 + 160, cy - 14), b, font=F["body_b"], fill=INK if n == 1 else (80, 95, 110, 210))
    elif idx in (5, 6, 12, 21, 22):
        cols = 2 if idx in (5, 21, 22) else 4
        gap = 24
        top = y + 15
        left = x1 + 65
        avail = x2 - x1 - 130
        cw = (avail - gap * (cols - 1)) / cols
        ch = 260 if cols == 2 else 500
        colors = [BLUE, ORANGE, GREEN, YELLOW]
        for i, b in enumerate(bullets):
            col = i % cols
            row = i // cols
            bx = left + col * (cw + gap)
            by = top + row * (ch + gap)
            simple_card(d, (int(bx), int(by), int(bx + cw), int(by + ch)),
                        b.split("：")[0] if "：" in b else f"模块 {i + 1}",
                        [b.split("：", 1)[1] if "：" in b else b], colors[i % 4])
    elif idx in (7, 8, 9, 10, 11, 12, 18, 20):
        top = y + 20
        left = x1 + 90
        for i, b in enumerate(bullets[:6]):
            bx = left + (i % 2) * 470
            by = top + (i // 2) * 160
            d.rounded_rectangle((bx, by, bx + 410, by + 110), radius=24,
                                fill=(238, 247, 255, 255), outline=(48, 143, 240, 170), width=3)
            draw_wrapped(d, b, (bx + 24, by + 18), F["small"], INK, 360, 8, max_lines=2)
            if i % 2 == 0 and i + 1 < len(bullets):
                d.line((bx + 415, by + 55, bx + 455, by + 55), fill=ACCENT, width=4)
                d.polygon([(bx + 455, by + 55), (bx + 440, by + 45), (bx + 440, by + 65)], fill=ACCENT)
    else:
        y = bullet_list(d, bullets, x1 + 88, y + 28, x2 - x1 - 170, BLUE, F["body"], 22)
        if idx in (13, 14, 15, 16, 17):
            d.rounded_rectangle((x1 + 78, y + 20, x2 - 80, min(y + 220, y2 - 65)), radius=28,
                                fill=(238, 247, 255, 255), outline=(205, 229, 247, 255), width=2)
            d.text((x1 + 110, y + 48), "功能效果示意区", font=F["body_b"], fill=BLUE)
            for k in range(5):
                d.rounded_rectangle((x1 + 110 + k * 160, y + 105, x1 + 230 + k * 160, y + 160),
                                    radius=18, fill=(48, 143, 240, 50), outline=(48, 143, 240, 120), width=2)
    return img


def thanks():
    img = campus_bg()
    d = ImageDraw.Draw(img, "RGBA")
    logo(d, (W - 78) // 2, 110, text=False)
    title = "感谢聆听"
    tw = d.textlength(title, font=F["cover_title"])
    d.text(((W - tw) / 2, 360), title, font=F["cover_title"], fill="white",
           stroke_width=2, stroke_fill=(0, 60, 130, 150))
    sub = "欢迎提问与交流"
    tw = d.textlength(sub, font=F["cover_sub"])
    d.text(((W - tw) / 2, 485), sub, font=F["cover_sub"], fill="white")
    lines = ["在线体验：http://47.108.218.39:8082/", "演示账号：admin / admin123456", "西南交通大学 · 计算机与人工智能学院"]
    y = 590
    for t in lines:
        tw = d.textlength(t, font=font(28))
        d.text(((W - tw) / 2, y), t, font=font(28), fill=(255, 255, 255, 235))
        y += 56
    d.rounded_rectangle((560, 850, 1360, 858), radius=4, fill=BLUE)
    return img


def make_contact_sheet():
    imgs = sorted(OUT.glob("slide_*.png"))
    thumbs = []
    for p in imgs:
        im = Image.open(p).convert("RGB")
        im.thumbnail((320, 180))
        thumbs.append((p, im.copy()))
    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 360, rows * 230), (245, 248, 252))
    d = ImageDraw.Draw(sheet)
    label_font = font(20, True, True)
    for i, (p, im) in enumerate(thumbs):
        x = (i % cols) * 360 + 20
        y = (i // cols) * 230 + 35
        sheet.paste(im, (x, y))
        d.text((x, y - 25), p.stem, font=label_font, fill=(20, 35, 50))
    sheet.save(OUT / "preview_contact_sheet.png")


def main():
    cover().save(OUT / "slide_01.png")
    for idx, (title, subtitle, bullets) in enumerate(SLIDES, start=2):
        make_content(idx, title, subtitle, bullets).save(OUT / f"slide_{idx:02d}.png")
    thanks().save(OUT / "slide_23.png")
    make_contact_sheet()
    print(f"generated {len(list(OUT.glob('slide_*.png')))} png files")
    print(OUT)


if __name__ == "__main__":
    main()
