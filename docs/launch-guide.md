# hjangel.com 从零上线操作手册

> 目标：让全世界通过 `https://hjangel.com` 访问你的个人投研主页。
> 时长：约 40 分钟，一次性。之后每周更新只需 1 条 git 命令。
> 全程免费（GitHub + Cloudflare 免费套餐足够）。

---

## 三阶段总览

| 阶段 | 做什么 | 时间 | 需要 |
|---|---|---|---|
| ① | 注册 GitHub | ~5 分钟 | 邮箱 |
| ② | 注册 Cloudflare + 创建 Pages 项目 | ~15 分钟 | 邮箱 |
| ③ | 本地 push + 绑定 hjangel.com | ~15 分钟 | 美橙互联账号 |

> ✅ 本地 git 仓库**已初始化并完成首次提交**（commit `5dc1538`），你只需要把它推到 GitHub。

---

## 阶段 ①：注册 GitHub（~5 分钟）

1. 浏览器打开 **https://github.com/signup**
2. 填邮箱 → 设置密码 → 选用户名（建议 **`hjangel`**，好记）→ 验证邮箱
3. 登录后，点右上角 **+ → New repository**
   - Repository name 填：**`hjangel-site`**（随便起，推荐这个）
   - 选择 **Private（私有）**，不要选 Public（你的净值数据暂时不公开）
   - 不要勾选 "Add a README"（本地已有）
   - 点 **Create repository**
4. 创建后页面会显示一串命令（**git remote add origin ...**），**先别关这个页面**，阶段 ③ 要用

---

## 阶段 ②：注册 Cloudflare + 创建 Pages（~15 分钟）

1. 浏览器打开 **https://dash.cloudflare.com/signup**，用邮箱注册（免费）
2. 登录后，左侧菜单点 **Workers & Pages**（或首页快捷入口 "Pages"）
3. 点 **Create** → 选 **Pages** 标签 → **Connect to Git**
4. 点 **Connect to GitHub** → 授权 Cloudflare 访问你的 GitHub
   - 授权范围只勾选刚建的 **hjangel-site** 仓库即可（更安全）
5. 选择仓库 **hjangel-site** → 点 **Begin setup**
6. 构建配置（**关键，不要填错**）：

   | 字段 | 填什么 |
   |---|---|
   | Framework preset | **None** |
   | Build command | **留空**（纯静态站，不需要构建） |
   | Build output directory | **留空** |

   > 如果界面强制要求填 output directory，填 **`/`**（根目录即网站根）。

7. 点 **Save and Deploy** → 等 1-2 分钟
8. 部署成功后你会得到一个地址：**`https://hjangel-site.pages.dev`**
   - **现在点开测试**：能看到你的网站就说明部署成功了 ✅

> 记下这个 `xxx.pages.dev` 地址，阶段 ③ 绑定域名要用。

---

## 阶段 ③：本地 push + 绑定域名（~15 分钟）

### 第 1 步：把本地代码推到 GitHub

回到阶段 ① 创建仓库后留下的页面，在**本地终端（Mac 的「终端」App）**执行：

```bash
cd /Users/apple/WorkBuddy/2026-09-05-22-23-31

# 把下面这行换成 GitHub 页面显示的真实地址（用户名替换成你注册的）
git remote add origin https://github.com/你的用户名/hjangel-site.git

git push -u origin main
```

- 首次 push 会弹出窗口让你登录 GitHub（网页授权即可）
- push 成功后，回到 Cloudflare Pages 项目页，会看到它自动触发一次新部署

> 💡 以后每次更新网站内容，只需要：
> ```bash
> cd /Users/apple/WorkBuddy/2026-09-05-22-23-31
> git add -A && git commit -m "更新说明" && git push
> ```
> 30 秒内 Cloudflare 自动把新内容发布到线上。

### 第 2 步：Cloudflare Pages 添加自定义域名

1. Cloudflare → Workers & Pages → 你的项目 **hjangel-site** → **Custom domains**
2. 点 **Set up a custom domain** → 输入 **`hjangel.com`** → Continue
3. 它会提示你去 DNS 加一条记录（先别关，下一步用）

### 第 3 步：美橙互联 DNS 加 CNAME（让 hjangel.com 指向 Cloudflare）

1. 登录**美橙互联**（www.cndns.com）→ 控制台 → 域名管理 → 找到 hjangel.com → **DNS 解析管理**
2. 添加一条记录：

   | 字段 | 值 |
   |---|---|
   | 主机记录 | **`@`** |
   | 记录类型 | **CNAME** |
   | 记录值 | **`hjangel-site.pages.dev`**（第 2 步里 Cloudflare 显示的地址） |
   | TTL | 默认 / 自动 |

3. 保存。回到 Cloudflare 的自定义域名页面，点 **Activate**
4. 等待验证通过 + 自动签发 HTTPS 证书（一般 5~15 分钟）
5. 完成！浏览器打开 **https://hjangel.com** 验证

> ⚠️ 避坑：如果美橙互联不支持 `@` 根域名的 CNAME：
> - 方案 A：在美橙加 **A 记录**，主机记录 `@`，记录值填 Cloudflare 自定义域名页里显示的 IP
> - 方案 B：先用 URL 转发（301）把 hjangel.com 转到 pages.dev 地址过渡，Cloudflare 侧照样能 Activate

---

## 每周更新工作流（上线后常态化）

周日收盘后，5 分钟完成：

```bash
cd /Users/apple/WorkBuddy/2026-09-05-22-23-31
.venv/bin/python3 scripts/fetch_data.py   # ① 抓本周行情（如调仓，先改 portfolio.yaml）
.venv/bin/python3 scripts/plot.py          # ② 重画净值图
git add -A
git commit -m "week-XX 净值更新"
git push                                   # ③ 自动部署 → hjangel.com 已是最新
```

## 发布一篇新的研究文章

1. 新建 `articles/2026-xx-xx-标题.html`（可从公众号 HTML 直接复用）
2. 首页/研究页加一张卡片链接
3. 执行上面 3 条 git 命令 → 自动上线

---

## 常见问题

| 问题 | 处理 |
|---|---|
| push 时报认证错误 | 用 GitHub 网页授权登录，或生成 Personal Access Token 代替密码 |
| pages.dev 能开但 hjangel.com 打不开 | DNS 未生效，等 5-30 分钟；或检查 CNAME 记录值是否带 .pages.dev |
| 证书状态显示 Pending | 等几分钟，Let's Encrypt 自动签发，无需手动操作 |
| 想换回 Public 公开 | GitHub 仓库 Settings → Danger Zone → Change visibility |
| 忘记更新命令 | 看本文档「每周更新工作流」，复制即用 |

---

*配置参考：本项目的 Cloudflare 部署文件 `wrangler.toml`、`_redirects`、`_headers` 已就绪；DNS 细节另见 `docs/dns-guide.md`。*
