"""
plot.py
=======

读取 ../data/portfolio.json，画和洪老板原图风格一致的 matplotlib 净值曲线。

风格参考：
- 深蓝色主线（#1F497D）
- 多条曲线对比：组合 + 基准
- X 轴：周内日度日期（如 8.14、8.17）
- Y 轴：净值（0.98 - 1.05）
- 标题居中："投研周记跟踪标的 · 等权拟合净值曲线 (起始日 = 1 · 本地币种 · 日度再平衡)"
- 灰色虚线：本周（W36）标记
- 图例放左上角
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # 无 GUI 环境
import matplotlib.pyplot as plt
from matplotlib import rcParams

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CHARTS_DIR = ROOT / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# 字体配置（中文显示）
rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "DejaVu Sans"]
rcParams["axes.unicode_minus"] = False

# 颜色方案（参考原图）
COLORS = {
    "价值红利10只等权": "#1F3A5F",    # 深蓝（主组合）
    "全枢约12只等权":   "#B8860B",    # 金棕（次组合）
    "沪深300":         "#888888",    # 灰（沪深 300）
    "中证红利":         "#C0392B",    # 砖红（中证红利）
}

LINE_STYLES = {
    "价值红利10只等权": "-",
    "全枢约12只等权":   "-",
    "沪深300":         "--",
    "中证红利":         "--",
}

LABEL_MAP = {
    "value_yield_10": "价值红利10只等权",
    "all_core_12":    "全枢约12只等权",
    "沪深300":        "沪深300",
    "中证红利":        "中证红利",
}


def format_date_label(date_str: str) -> str:
    """把 '2026-08-14' 格式化成 '8.14'。"""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{d.month}.{d.day}"


def iso_week_label(date_str: str) -> str:
    """ISO 周标记。"""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    year, week, _ = d.isocalendar()
    return f"W{week}"


def load_data() -> dict:
    """读取 portfolio.json。"""
    portfolio_path = DATA_DIR / "portfolio.json"
    if not portfolio_path.exists():
        raise FileNotFoundError(
            f"找不到 {portfolio_path}\n请先运行: python scripts/fetch_data.py"
        )
    with open(portfolio_path, "r", encoding="utf-8") as f:
        return json.load(f)


def plot_portfolio_chart(data: dict) -> Path:
    """画主图：所有组合 + 基准叠加。"""
    dates_raw = data.get("dates", [])
    series = data.get("series", {})
    start_date = data.get("start_date", "")
    rebalance = data.get("rebalance", "月度再平衡")
    is_demo = data.get("demo", False)

    if not dates_raw or not series:
        raise ValueError("数据为空，请检查 portfolio.json")

    # 格式化日期显示
    dates_display = [format_date_label(d) for d in dates_raw]
    dates_iso_week = [iso_week_label(d) for d in dates_raw]

    # 创建画布
    fig, ax = plt.subplots(figsize=(13, 6.5), dpi=120)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FAFBFC")

    # 画每条曲线
    legend_entries = []
    for name, values in series.items():
        if not values:
            continue
        color = COLORS.get(name, "#444444")
        linestyle = LINE_STYLES.get(name, "-")
        lw = 2.0 if "等权" in name else 1.6

        line, = ax.plot(
            dates_display,
            values,
            color=color,
            linestyle=linestyle,
            linewidth=lw,
            marker="o" if "等权" in name else "",
            markersize=4 if "等权" in name else 0,
            label=name,
        )
        legend_entries.append((line, name, values))

    # 计算最新值做图例标注
    legend_labels = []
    for line, name, values in legend_entries:
        if values:
            latest = values[-1]
            change = (latest - 1) * 100
            sign = "+" if change > 0 else ""
            label = f"{name} {latest:.4f}  (期间{sign}{change:.1f}%)"
            legend_labels.append(label)
        else:
            legend_labels.append(name)

    # 替换图例 labels
    handles = [entry[0] for entry in legend_entries]
    ax.legend(
        handles,
        legend_labels,
        loc="upper left",
        fontsize=9.5,
        frameon=True,
        facecolor="#F0F0F0",
        edgecolor="#CCCCCC",
        framealpha=0.95,
    )

    # Y 轴范围（自动 + 边距）
    all_values = []
    for vals in series.values():
        all_values.extend(vals)
    if all_values:
        y_min = min(all_values) - 0.005
        y_max = max(all_values) + 0.005
        ax.set_ylim(y_min, y_max)

    # 网格
    ax.grid(True, linestyle="-", linewidth=0.5, alpha=0.3, color="#CCCCCC")
    ax.set_axisbelow(True)

    # X 轴
    ax.tick_params(axis="x", labelsize=9, rotation=0)
    ax.tick_params(axis="y", labelsize=10)

    # 标题
    title = f"投研周记跟踪标的 · 等权拟合净值曲线 ({start_date} = 1 · 本地币种 · {rebalance})"
    if is_demo:
        title += "  [DEMO]"
    ax.set_title(title, fontsize=13, color="#1F3A5F", pad=15, weight="bold")

    # 本周标记（每周五画灰色虚线 + W{n} 标签）
    for i, (d_raw, d_iso) in enumerate(zip(dates_raw, dates_iso_week)):
        d = datetime.strptime(d_raw, "%Y-%m-%d")
        if d.weekday() == 4:  # 周五
            ax.axvline(
                x=i, color="#888888", linestyle=":", linewidth=0.8, alpha=0.6
            )
            ax.text(
                i, y_min + 0.002, f"本周({d_iso})",
                fontsize=8, color="#B8860B", ha="center", weight="bold"
            )

    # 美化边框
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")

    plt.tight_layout()

    output_path = CHARTS_DIR / "portfolio.png"
    plt.savefig(output_path, dpi=120, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close()

    return output_path


def main():
    print("📊 加载数据...")
    data = load_data()

    print("🎨 画图...")
    out = plot_portfolio_chart(data)
    print(f"✅ {out}")

    if data.get("demo"):
        print("\n⚠️  当前为 demo 数据，跑真实数据请运行：")
        print("    python scripts/fetch_data.py")


if __name__ == "__main__":
    main()