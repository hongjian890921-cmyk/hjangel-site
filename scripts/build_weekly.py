#!/usr/bin/env python3
"""
build_weekly.py — 把 Obsidian 公众号版周记 HTML 套上 hjangel.com 网站壳，
生成 weekly/NN.html 详情页。每周新增周记后重跑即可。
"""
import re
from pathlib import Path

SRC = Path("/Users/apple/Library/Mobile Documents/iCloud~md~obsidian/Documents/投研工作台/微信公众号")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "weekly"

# 每期元数据：文件名、期数、周次、日期、标题、摘要
ISSUES = [
    {
        "file": "投研周记01_W34_公众号版.html",
        "num": 1, "week": "W34", "range": "2026.08.17 – 08.23",
        "title": "中报密集披露周，12 只标的全景跟踪",
        "excerpt": "泡泡玛特、阿里等中报放榜；美伊谈判期满未果，布伦特油价 +5.9%，COMEX 黄金收 4571 美元。紫金 +8.12% 领涨，茅台失守 1300 元。",
    },
    {
        "file": "投研周记02_W35_公众号版.html",
        "num": 2, "week": "W35", "range": "2026.08.24 – 08.30",
        "title": "中报收官周：广发净利 +80%，海油派息创新高",
        "excerpt": "紫金、海油、广发、美的、拼多多五份中报落地；英伟达财报超预期并给出 FY28 +70% 展望；美伊新停火协议令油价回吐地缘溢价。",
    },
    {
        "file": "投研周记03_W36_公众号版.html",
        "num": 3, "week": "W36", "range": "2026.08.31 – 09.06",
        "title": "非农爆表，茅台批价 5 连涨，两大广告印钞机收缩回购",
        "excerpt": "美国 8 月非农 16.2 万人远超预期，9 月加息概率升至 60%+；腾讯回购降档、谷歌被指削减回购；茅台飞天批价 5 连涨至 1755 元。",
    },
]

NAV = """<nav class="nav">
    <div class="nav-container">
        <a href="../index.html" class="nav-logo">hjangel<span class="accent">·</span>投研手记</a>
        <ul class="nav-links">
            <li><a href="../index.html">首页</a></li>
            <li><a href="../research.html">研究</a></li>
            <li><a href="../weekly.html" class="active">周记</a></li>
            <li><a href="../portfolio.html">组合追踪</a></li>
            <li><a href="../about.html">关于</a></li>
        </ul>
    </div>
</nav>"""

FOOTER = """<footer class="footer">
    <div>hjangel.com · 投研手记 · <a href="../about.html">关于与免责声明</a></div>
    <div class="disclaimer">本站所有内容仅作个人研究记录，不构成任何投资建议。市场有风险，决策需谨慎。</div>
</footer>"""


def extract_body(src_path: Path) -> str:
    html = src_path.read_text(encoding="utf-8")
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    return m.group(1).strip() if m else ""


def build(issue: dict):
    body = extract_body(SRC / issue["file"])
    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="投研周记 {issue['num']:02d}/150 · {issue['week']} · {issue['title']}">
    <title>投研周记 {issue['num']:02d}/150 ｜ {issue['title']} · hjangel.com</title>
    <link rel="stylesheet" href="../assets/style.css">
</head>
<body>

{NAV}

<main class="container">
    <p style="margin:0 0 4px 0;"><a href="../weekly.html" style="color:#1F3A5F;text-decoration:none;font-size:14px;">← 全部周记</a></p>
    <div style="max-width:680px;margin:0 auto;padding:12px 0 32px 0;font-family:-apple-system,PingFang SC,Microsoft YaHei,sans-serif;">
{body}
    </div>
</main>

{FOOTER}

</body>
</html>
"""
    out = OUT / f"{issue['num']:02d}.html"
    out.write_text(page, encoding="utf-8")
    print(f"✅ {out.relative_to(ROOT)}")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for issue in ISSUES:
        build(issue)
    print(f"\n共生成 {len(ISSUES)} 期周记详情页。")
