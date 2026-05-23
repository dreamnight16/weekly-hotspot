# GitHub Pinned Repos → Blog Sync

## Overview

GitHub Actions 定时任务，检测 GitHub profile 上的 pinned 项目变化，自动同步到 Astro 博客的 projects 集合。

## Architecture

```
GitHub Actions (schedule: daily)
  ↓
Node.js script (sync-pinned.mjs)
  ↓ GitHub GraphQL API
pinnedItems { name, description, url }
  ↓ compare
src/content/projects/*.yaml
  ↓ diff
新增 → 创建 YAML (image: opengraph.githubassets.com/{owner}/{repo})
移除 → 删除 YAML
  ↓
git commit & push (仅在有变更时)
```

## Tech Stack

- **Runtime:** Node.js (博客已有 Node 生态，零额外依赖)
- **GitHub API:** GraphQL（`user.pinnedItems` 一次查询拿全量）
- **CI:** GitHub Actions workflow（博客仓库内 `.github/workflows/`）
- **频率:** 每天一次，手动触发

## Components

### 1. GitHub Actions Workflow

- 位置：`myBlog/.github/workflows/sync-pinned.yml`
- schedule: 每天北京时间凌晨 3:00
- 支持 `workflow_dispatch` 手动触发
- 用 `secrets.PINNED_SYNC_PAT` 鉴权（需用户创建 Personal Access Token，`read:user` scope）

### 2. 同步脚本 (`scraper/sync-pinned.mjs`)

- 调用 GitHub GraphQL 查询 `viewer.pinnedItems`
- 读取 `src/content/projects/` 下所有 YAML，解析出 repo URL set
- Diff 逻辑：
  - 新 pinned 但不在 projects 中 → 生成 YAML 文件
  - 在 projects 中但不在 pinned 中 → 删除 YAML 文件
- 图片来源：`https://opengraph.githubassets.com/1/{owner}/{repo}`
- 文件名：将 repo 名转为 kebab-case，如 `my-project.yaml`
- 去重：`{owner}/{repo}` 作为唯一标识（存在 link 字段中）

### 3. YAML 格式

与现有内容一致：
```yaml
title: RepoName
description: Repo description from GitHub
image: https://opengraph.githubassets.com/1/sixtdreanight/RepoName
link: https://github.com/sixtdreanight/RepoName
```

## Error Handling

- GitHub API 失败 → 日志记录，不提交
- 无变化 → 跳过 commit
- 图片获取失败 → 兜底使用 `https://github.com/{owner}.png`（GitHub 头像）

## Scope

- 当前 scope：单人 profile，硬编码 username `sixtdreanight`
- 仅处理公开仓库
- 不更新已有项目的描述/图片（首次同步后不修改）
