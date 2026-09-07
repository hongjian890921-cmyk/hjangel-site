# 美橙互联 DNS 配置指南 —— 把 hjangel.com 指向 Cloudflare Pages

> **写在前面**：DNS 解析配置有 5 - 60 分钟延迟（DNS 全球生效时间），配好后不要急着刷新访问，耐心等几分钟。

---

## 前置条件

✅ 域名 `hjangel.com` 已在美橙互联购买
✅ Cloudflare Pages 项目已部署好（参考 `docs/cloudflare-deploy.md`）
✅ 拿到 Cloudflare Pages 分配的默认域名：`xxx.pages.dev`

---

## 步骤 1：登录美橙互联控制台

1. 打开 https://www.cndns.com/
2. 登录账号
3. 进入 **会员中心** → **我的域名** → 找到 `hjangel.com`
4. 点击 **管理** → **域名解析**（或 DNS 管理）

---

## 步骤 2：添加解析记录

### 主域名 `hjangel.com` → Cloudflare Pages

| 字段 | 值 |
|---|---|
| 主机记录 | `@` |
| 记录类型 | **CNAME** |
| 记录值 | `your-project.pages.dev`（**替换成你实际分配到的**，如 `hjangel.pages.dev`） |
| TTL | 3600（或自动） |

⚠️ **如果美橙互联控制台提示"@ 记录不支持 CNAME"**：
- 方案 A：把记录类型改为 **URL 转发（301）**，转发到 `https://your-project.pages.dev`
- 方案 B：去 Cloudflare 控制台获取 Pages 的 IP，加 **A 记录**（Cloudflare Pages 的 IP 通常是 `100.64.0.0/10` 范围内的，需要在 Cloudflare 后台查）

---

### 二级域名 `www.hjangel.com` → Cloudflare Pages

| 字段 | 值 |
|---|---|
| 主机记录 | `www` |
| 记录类型 | **CNAME** |
| 记录值 | `your-project.pages.dev`（同上） |
| TTL | 3600 |

---

### 步骤 3：在 Cloudflare Pages 后台添加自定义域名

1. 登录 https://dash.cloudflare.com/
2. 进入 **Workers & Pages** → 选择你的项目
3. **Custom domains** → **Set up a custom domain**
4. 输入 `hjangel.com`
5. Cloudflare 会自动校验 DNS 记录

---

## 步骤 4：验证

打开 https://hjangel.com 应该能看到你的网站。

**验证命令（终端）**：

```bash
# DNS 是否生效
dig hjangel.com +short
nslookup hjangel.com

# 网站是否可访问
curl -I https://hjangel.com
```

---

## 常见问题

| 问题 | 排查 |
|---|---|
| 浏览器提示"网站未备案" | 不要紧，因为 Cloudflare Pages 走境外节点，不需备案 |
| Cloudflare 后台显示 "DNS verification failed" | 等 5 分钟；如果一直失败，检查 CNAME 记录值是否正确（不要带 `https://`） |
| 部分地区访问慢 | Cloudflare 国内访问偶尔慢，可加配 **Cloudflare 中国网络**（需 Workers 套餐） |
| 之前用阿里云 DNS，能不能迁移？ | 可以：在 Cloudflare 注册同名域，Cloudflare 会给两套 NS，去原注册商改 NS 即可 |

---

## 进阶：把 DNS 全交给 Cloudflare（可选）

如果你将来想用 Cloudflare 的全套能力（WAF、CDN 优化、Workers），可以：

1. 在 Cloudflare 注册并添加 `hjangel.com`（**这步是免费的，** 不收费）
2. Cloudflare 会给你两套 NS 记录（`xxx.ns.cloudflare.com`）
3. 去美橙互联把 NS 记录改为 Cloudflare 的
4. 后续所有解析都在 Cloudflare 后台管理（更直观、更强大）

但这一步**不是必须的**，保留美橙互联的 DNS 也完全够用。