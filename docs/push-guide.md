# 上传代码到 GitHub

## 一次性操作（约 1 分钟）

打开终端（Terminal.app），逐行执行：

```bash
cd /Users/apple/WorkBuddy/2026-09-05-22-23-31

# 检查 remote 是否已存在
git remote -v
```

如果显示已经有 origin，先清理：

```bash
git remote remove origin
```

然后添加 GitHub 仓库地址：

```bash
git remote add origin https://github.com/你的用户名/hjangel-site.git

# 推送主分支
git push -u origin main
```

> **用户名替换**：把"你的用户名"换成实际的 GitHub 用户名。
> 完整命令例子（hjangel-site 这个仓库）：
> `git remote add origin https://github.com/hongjian890921-cmyk/hjangel-site.git`

## 推送时遇到的认证方式

### 方式 1：浏览器 OAuth（最方便）

如果系统里已经登录过 GitHub 桌面/网页，终端 push 时会**自动弹浏览器窗口**，点 "Authorize" 即可。

### 方式 2：Personal Access Token（如果方式 1 不弹）

GitHub 已不允许密码推送。需要生成 PAT：

1. 打开 https://github.com/settings/tokens
2. 点 **Generate new token** → **Generate new token (classic)**
3. Note 填 `hjangel-site-deploy`
4. Expiration 选 `7 days`（或更长）
5. 勾选权限：**`repo`**（完整仓库访问）
6. 点 **Generate token**
7. **复制显示的 token**（页面关闭后再也看不到）

回到终端：
- Username：填 GitHub 用户名
- Password：**粘贴刚才复制的 token**（不是 GitHub 登录密码）

## 推送成功的标志

终端最后一行类似：

```
Branch 'main' set up to track remote origin/main.
```

刷新 GitHub 仓库页面，应能看到 **约 21 个文件**，含：

- `index.html`
- `research.html`
- `portfolio.html`
- `holdings.html`
- `about.html`
- `assets/style.css`
- `scripts/fetch_data.py`
- `docs/launch-guide.md`

## 推送失败常见原因

| 报错信息片段 | 原因 | 解法 |
|---|---|---|
| `Authentication failed` | 用密码登录或 PAT 错误 | 改用方式 2 重新生成 PAT |
| `Repository not found` | 用户名或仓库名错 | 检查 URL 中用户名是否正确 |
| `failed to push some refs` | 远程仓库已有 README 等文件 | 在 GitHub 仓库 Settings 删除 README 或本地 `git pull --rebase origin main` 后再 push |

## 推送成功后下一步

回到 WorkBuddy 对话，告诉 AI "push 成功了"，AI 会引导完成 Cloudflare Pages 绑定 → 美橙互联 DNS 解析 → `hjangel.com` 上线。
