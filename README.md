# hjangel.com · 投研手记

> 个人投研主页：把判断公开，用净值验证。
> 域名：**hjangel.com**（Cloudflare Pages 托管）
> 内容：十大金股周报 · 个股深度 · 财报点评 · 双组合净值实证（价值红利10只 / 全枢约12只 vs 沪深300、中证红利）

---

## 页面结构

```
/                 首页：一句话定位 + 最新研究 + 组合净值快照
/research.html    研究：十大金股周报 / 个股深度 / 财报点评 / 随笔
/portfolio.html   组合追踪：净值曲线 + 完整数据表
/holdings.html    持仓明细：两个组合的具体构成
/about.html       关于：作者 / 方法论 / 栏目 / 免责声明
```

## 📁 目录结构

```
.
├── index.html              # 首页（投研主页）
├── research.html           # 研究列表页
├── portfolio.html          # 组合追踪页
├── holdings.html           # 持仓明细页
├── about.html              # 关于页
├── assets/
│   └── style.css           # 全站样式
├── data/
│   ├── portfolio.json      # 净值数据（前端消费）
│   └── holdings.json       # 持仓数据
├── charts/
│   └── portfolio.png       # 主图表（matplotlib 生成）
├── scripts/
│   ├── fetch_data.py       # 抓取 A股/港股/美股 + 指数，按周聚合算净值
│   ├── plot.py             # 画图
│   └── portfolio.yaml      # 组合配置（名单 + 市场标记 + 起始日）
├── docs/
│   └── dns-guide.md        # 美橙互联 DNS 配置指南
├── .venv/                  # Python 虚拟环境（本地）
├── wrangler.toml           # Cloudflare Pages 配置
├── _redirects              # URL 重定向
├── _headers                # HTTP 头
├── requirements.txt        # Python 依赖
└── README.md               # 本文件
```

---

## 🚀 快速开始（本地）

```bash
# 1. 激活环境（已建 .venv 则直接激活）
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. demo 模式跑通（无需网络）
python scripts/fetch_data.py --demo && python scripts/plot.py

# 3. 真实数据（需能访问东财行情接口；沙盒/代理环境可能被限流）
python scripts/fetch_data.py && python scripts/plot.py

# 4. 本地预览
python3 -m http.server 8000   # 浏览器打开 http://localhost:8000
```

> 组合名单与市场标记在 `scripts/portfolio.yaml` 维护。
> `start_date` 必须写成带引号的 `"2026-08-14"`——YAML 会把裸日期解析成 date 对象导致脚本报错。

---

## 🌐 部署到 Cloudflare Pages

1. 代码 push 到 GitHub
2. dash.cloudflare.com → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
3. Build 设置：Build command 留空，Build output directory 填 `.`
4. **Custom domains** → 添加 `hjangel.com`

DNS 绑定详见 [`docs/dns-guide.md`](./docs/dns-guide.md)（美橙互联加 CNAME → `xxx.pages.dev`）。

---

## 🔄 每周更新流程

```bash
# 1.（可选）有调仓就改 portfolio.yaml
# 2. 抓数 + 画图
python scripts/fetch_data.py && python scripts/plot.py
# 3. 提交自动部署
git add . && git commit -m "w$(date +%V): 周报更新" && git push
```

---

## 📝 待办

- [ ] 跑通 12 只标的 + 双指数的完整真实数据（沙盒代理不稳，本地/真实网络下稳定）
- [ ] 修复首周净值起点：确保 12 只全部抓齐后再 plot（缺数据会导致首点 < 1.0）
- [ ] 研究页首批文章迁移（十大金股周报往期从公众号归档）
- [ ] GitHub 仓库 + Cloudflare Pages 首次部署
- [ ] 美橙互联 DNS 绑定 hjangel.com

---

## ⚠️ 免责声明

本项目仅作个人投研跟踪记录，**不构成任何投资建议**。所有数据均来自公开 API，可能存在延迟或错误。
