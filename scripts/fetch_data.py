"""
fetch_data.py
=============

从 AKShare 抓取 A 股 / 港股 / 美股日线收盘价，按周聚合，输出前端可直接消费的 JSON。

支持的市场：
- cn: A 股（ak.stock_zh_a_hist）
- hk: 港股（ak.stock_hk_hist）
- us: 美股（ak.stock_us_hist）

输出：
- ../data/portfolio.json  —— 净值曲线数据（前端 Chart 用）
- ../data/holdings.json   —— 持仓明细
- ../data/daily.json       —— 原始日度数据（备查）

运行：
    python fetch_data.py            # 抓最新数据
    python fetch_data.py --demo     # 用内置 demo 数据跑通（无网络/无 akshare 时使用）
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = SCRIPTS_DIR / "portfolio.yaml"


def load_config() -> dict:
    """加载组合配置。"""
    import yaml
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_stock_akshare(stock: dict, start_date: str) -> list[dict]:
    """
    通用抓取函数：根据 market 路由到不同 AKShare 接口。

    stock: {'market': 'cn'|'hk'|'us', 'code': '600519', 'name': '贵州茅台'}
    start_date: 'YYYY-MM-DD'

    返回: [{'date': '2026-08-14', 'close': 1680.5}, ...]
    """
    try:
        import akshare as ak
    except ImportError:
        raise ImportError("需要安装 akshare：pip install akshare")

    market = stock["market"]
    code = stock["code"]
    name = stock.get("name", code)
    if not isinstance(start_date, str):
        start_date = start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else str(start_date)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_compact = start_date.replace("-", "")
    end_compact = end_date.replace("-", "")

    if market == "cn":
        # A 股
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_compact,
            end_date=end_compact,
            adjust="hfq",  # 后复权
        )
        if df is None or df.empty:
            return []
        return [
            {"date": str(row["日期"])[:10], "close": float(row["收盘"])}
            for _, row in df.iterrows()
        ]

    elif market == "hk":
        # 港股（AKShare: stock_hk_hist）
        df = ak.stock_hk_hist(
            symbol=code,
            period="daily",
            start_date=start_compact,
            end_date=end_compact,
            adjust="hfq",
        )
        if df is None or df.empty:
            return []
        date_col = "日期" if "日期" in df.columns else "date"
        close_col = "收盘" if "收盘" in df.columns else "close"
        return [
            {"date": str(row[date_col])[:10], "close": float(row[close_col])}
            for _, row in df.iterrows()
        ]

    elif market == "us":
        # 美股（AKShare: stock_us_hist）
        # 谷歌 = GOOGL（NASDAQ），拼多多 = PDD
        df = ak.stock_us_hist(
            symbol=code,
            period="daily",
            start_date=start_compact,
            end_date=end_compact,
            adjust="hfq",
        )
        if df is None or df.empty:
            return []
        # 美股字段可能不一样，做兼容处理
        date_col = "日期" if "日期" in df.columns else "date"
        close_col = "收盘" if "收盘" in df.columns else "close"
        return [
            {"date": str(row[date_col])[:10], "close": float(row[close_col])}
            for _, row in df.iterrows()
        ]

    else:
        raise ValueError(f"未知市场: {market}（应为 cn / hk / us）")


def fetch_index_akshare(index_name: str, start_date: str) -> list[dict]:
    """
    用 AKShare 抓取指数日线收盘价。
    """
    try:
        import akshare as ak
    except ImportError:
        raise ImportError("需要安装 akshare：pip install akshare")

    if not isinstance(start_date, str):
        start_date = start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else str(start_date)
    end_date = datetime.now().strftime("%Y-%m-%d")

    index_map = {
        "沪深300": ("sh", "000300"),
        "中证红利": ("sh", "000922"),
        "中证500": ("sh", "000905"),
        "创业板指": ("sz", "399006"),
        "上证50": ("sh", "000016"),
    }

    if index_name not in index_map:
        raise ValueError(f"暂不支持指数: {index_name}")

    market_prefix, symbol = index_map[index_name]

    df = ak.stock_zh_index_daily(symbol=f"{market_prefix}{symbol}")
    if df is None or df.empty:
        return []

    df["date"] = df["date"].astype(str)
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()

    return [
        {"date": row["date"][:10], "close": float(row["close"])}
        for _, row in df.iterrows()
    ]


def aggregate_weekly(daily_data: list[dict]) -> list[dict]:
    """把日线聚合成周线（每周最后交易日）。"""
    if not daily_data:
        return []

    weekly = {}
    for item in daily_data:
        d = datetime.strptime(item["date"], "%Y-%m-%d")
        year, week, _ = d.isocalendar()
        key = f"{year}-W{week:02d}"
        if key not in weekly or item["date"] > weekly[key]["date"]:
            weekly[key] = item

    return sorted(weekly.values(), key=lambda x: x["date"])


def compute_equally_weighted_nav(
    portfolio_stocks: list[dict],
    prices_by_code: dict[str, list[dict]],
    start_date: str,
    rebalance: str = "月度再平衡",
) -> list[dict]:
    """
    计算等权组合的周度净值。
    """
    if not portfolio_stocks:
        return []

    n = len(portfolio_stocks)
    init_weight = 1.0 / n

    all_dates = set()
    code_to_data = {}
    for stock in portfolio_stocks:
        key = f"{stock['market']}:{stock['code']}"
        data = prices_by_code.get(key, [])
        code_to_data[key] = {d["date"]: d["close"] for d in data}
        all_dates.update(code_to_data[key].keys())

    all_dates = sorted(all_dates)
    if not all_dates:
        return []

    nav_history = []
    weights = {f"{s['market']}:{s['code']}": init_weight for s in portfolio_stocks}
    last_rebalance_month = None

    for date in all_dates:
        market_values = {}
        for stock in portfolio_stocks:
            key = f"{stock['market']}:{stock['code']}"
            if date in code_to_data[key]:
                start_close = code_to_data[key].get(start_date)
                if start_close is None:
                    start_close = next(iter(code_to_data[key].values()), 1.0)
                market_values[key] = weights[key] * (code_to_data[key][date] / start_close)

        if not market_values:
            continue

        total_mv = sum(market_values.values())
        nav = total_mv

        d = datetime.strptime(date, "%Y-%m-%d")
        month_key = f"{d.year}-{d.month:02d}"
        if rebalance == "月度再平衡" and last_rebalance_month != month_key and d.day <= 5:
            weights = {k: mv / total_mv for k, mv in market_values.items()}
            last_rebalance_month = month_key

        nav_history.append({"date": date, "nav": round(nav, 6)})

    return aggregate_weekly(nav_history)


def compute_index_nav(daily_data: list[dict], start_date: str) -> list[dict]:
    """计算指数净值（从起始日归一化到 1.0）。"""
    if not daily_data:
        return []

    start_close = None
    for item in daily_data:
        if item["date"] >= start_date:
            start_close = item["close"]
            break

    if start_close is None:
        return []

    weekly = aggregate_weekly(daily_data)
    return [
        {"date": item["date"], "nav": round(item["close"] / start_close, 6)}
        for item in weekly
        if item["date"] >= start_date
    ]


def resolve_portfolio_stocks(config: dict, portfolio_key: str) -> list[dict]:
    """展开组合标的：处理 exclude_from / exclude_codes 引用。"""
    portfolio = config["portfolios"][portfolio_key]

    if portfolio.get("exclude_from"):
        # 从父组合拷贝后剔除
        parent_key = portfolio["exclude_from"]
        parent_stocks = [dict(s) for s in config["portfolios"][parent_key]["stocks"]]
        exclude = set(portfolio.get("exclude_codes", []))
        return [s for s in parent_stocks if s["code"] not in exclude]
    else:
        return portfolio["stocks"]


def generate_demo_data(start_date: str, end_date: str | None = None) -> dict:
    """生成模拟数据。"""
    import random

    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    if isinstance(start_date, datetime):
        start_date = start_date.strftime("%Y-%m-%d")
    elif not isinstance(start_date, str):
        start_date = str(start_date)

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    dates = []
    cur = start
    while cur <= end:
        if cur.weekday() < 5:  # 跳过周末
            dates.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)

    def gen_series(drift, vol, seed):
        random.seed(seed)
        series = []
        v = 1.0
        for _ in dates:
            change = random.gauss(drift, vol)
            v *= (1 + change)
            series.append(round(v, 4))
        return series

    series = {
        "价值红利10只等权": gen_series(0.0008, 0.008, seed=42),
        "全枢约12只等权": gen_series(0.0002, 0.007, seed=43),
        "沪深300": gen_series(-0.0035, 0.012, seed=44),
        "中证红利": gen_series(0.0045, 0.009, seed=45),
    }

    return {
        "dates": dates,
        "series": series,
        "start_date": start_date,
        "rebalance": "月度再平衡",
        "generated_at": datetime.now().isoformat(),
        "demo": True,
    }


def main():
    parser = argparse.ArgumentParser(description="抓取组合净值数据")
    parser.add_argument("--demo", action="store_true", help="用模拟数据跑通")
    parser.add_argument("--start", default=None, help="覆盖起始日 (YYYY-MM-DD)")
    parser.add_argument("--max-rounds", default=None, help="多轮补抓的最大轮数（默认 8）")
    args = parser.parse_args()

    config = load_config()
    start_date = args.start or config.get("start_date", "2026-08-14")
    # 防御：YAML 可能把 2026-08-14 解析成 datetime.date 而非 str
    if not isinstance(start_date, str):
        start_date = start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else str(start_date)

    if args.demo:
        print("📊 用 demo 数据生成...")
        data = generate_demo_data(start_date)
    else:
        print(f"📡 抓取真实数据，起始日: {start_date}")
        prices_by_code = {}

        # 收集所有需要的标的
        all_stocks = set()
        for portfolio_key in config.get("portfolios", {}):
            stocks = resolve_portfolio_stocks(config, portfolio_key)
            for s in stocks:
                key = f"{s['market']}:{s['code']}"
                all_stocks.add(key)

        print(f"  📦 总共需要抓 {len(all_stocks)} 个标的")

        def fetch_with_retry(stock_key: str, start: str, retries: int,
                             base_delay: int) -> list[dict]:
            """带间隔 + 退避重试地抓单只标的。"""
            market, code = stock_key.split(":", 1)
            stock = {"market": market, "code": code, "name": stock_key}
            last_err = None
            for attempt in range(retries):
                try:
                    return fetch_stock_akshare(stock, start)
                except Exception as e:
                    last_err = e
                    if attempt < retries - 1:
                        print(f"    ⚠ {stock_key} 第{attempt + 1}次失败，{base_delay * (attempt + 1)}s 后重试")
                        time.sleep(base_delay * (attempt + 1))
            print(f"    ✗ {stock_key} 最终失败: {last_err}")
            return []

        # —— 多轮抓取：直到全部成功或达到轮次上限 ——
        # 东财接口对高频请求限流（RemoteDisconnected/ProxyError），
        # 靠"轮间冷却 + 退避重试"把 12 只全部集齐。
        max_rounds = int(args.max_rounds or 8)
        for round_no in range(1, max_rounds + 1):
            missing = sorted(k for k in all_stocks if not prices_by_code.get(k))
            if not missing:
                break
            tag = "首轮" if round_no == 1 else f"补抓第 {round_no - 1} 轮"
            print(f"  🔁 {tag}: 待抓 {len(missing)} 个")
            retries = 2 if round_no == 1 else 4
            base_delay = 2 if round_no == 1 else 3 + round_no
            for key in missing:
                data_list = fetch_with_retry(key, start_date, retries, base_delay)
                prices_by_code[key] = data_list
                status = '✓' if data_list else '✗'
                print(f"    {status} {key}: {len(data_list)} 条")
                time.sleep(2.5)
            if round_no < max_rounds:
                print(f"  ⏳ 轮间冷却 {8 + round_no}s...")
                time.sleep(8 + round_no)

        # 计算每个组合的净值
        series = {}
        dates_set = set()
        for portfolio_key, portfolio in config.get("portfolios", {}).items():
            stocks = resolve_portfolio_stocks(config, portfolio_key)
            print(f"  📊 计算 {portfolio['name']} ({len(stocks)} 只)")
            nav_history = compute_equally_weighted_nav(
                stocks, prices_by_code, start_date, config.get("rebalance", "月度再平衡")
            )
            series[portfolio["name"]] = [item["nav"] for item in nav_history]
            dates_set.update(item["date"] for item in nav_history)

        # 抓基准指数
        for benchmark_name in config.get("benchmark", []):
            print(f"  📈 抓基准 {benchmark_name}")
            try:
                bench_data = fetch_index_akshare(benchmark_name, start_date)
                nav_history = compute_index_nav(bench_data, start_date)
                series[benchmark_name] = [item["nav"] for item in nav_history]
                dates_set.update(item["date"] for item in nav_history)
            except Exception as e:
                print(f"    ✗ {benchmark_name} 失败: {e}")
                series[benchmark_name] = []

        # 统一日期序列
        dates = sorted(dates_set)

        # 对齐长度（短的补 1.0）
        max_len = max((len(v) for v in series.values()), default=0)
        for k in series:
            if len(series[k]) < max_len:
                pad = [1.0] * (max_len - len(series[k]))
                series[k] = pad + series[k]

        data = {
            "dates": dates[-max_len:] if dates else [],
            "series": series,
            "start_date": start_date,
            "rebalance": config.get("rebalance", "月度再平衡"),
            "generated_at": datetime.now().isoformat(),
            "demo": False,
        }

    # 写 portfolio.json
    portfolio_path = DATA_DIR / "portfolio.json"
    with open(portfolio_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ {portfolio_path}")

    # 写 holdings.json
    holdings = {}
    for portfolio_key in config.get("portfolios", {}):
        stocks = resolve_portfolio_stocks(config, portfolio_key)
        holdings[portfolio_key] = [
            {
                "code": stock["code"],
                "name": stock.get("name", stock["code"]),
                "market": stock["market"],
                "weight": f"{100.0 / max(len(stocks), 1):.2f}%",
            }
            for stock in stocks
        ]

    holdings_path = DATA_DIR / "holdings.json"
    with open(holdings_path, "w", encoding="utf-8") as f:
        json.dump(holdings, f, ensure_ascii=False, indent=2)
    print(f"✅ {holdings_path}")


if __name__ == "__main__":
    main()