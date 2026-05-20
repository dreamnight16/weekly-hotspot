# 每周热点深度梳理 / Weekly Hotspot Analysis

[![Tests](https://img.shields.io/badge/tests-7%20passed%20%2B%207%20integration-green)](https://github.com/sixtdreanight/weekly-hotspot/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)

Grabs trending news every Monday, runs each story through DeepSeek for filtering, scoring, and deep analysis. Output: timelines, evidence chains, and relationship graphs as structured JSON. Rendered on the blog.

AI 驱动的热点事件分析工具。每周自动抓取热点新闻，通过 DeepSeek 进行政审过滤、价值评分、深度梳理（时间线 + 证据链 + 关系网），输出结构化 JSON 到博客渲染。

## 架构

```
DeepSeek API（联网搜索）
  ↓ 获取本周热点候选
[Phase 0] 政审过滤
  ↓ 排除敏感内容
[Phase 1] AI 评分筛选
  ↓ 事件影响 × 信息增量 → 前 5-8 个
[Phase 2] 逐事件深度梳理
  ↓ 时间线 + 证据真伪 + 因果/关联/反驳关系
输出 JSON → myBlog content collection
  ↓ Astro 静态构建
溯源报告风格页面
```

## 项目结构

```
weekly-cli/         # Python CLI
  main.py           # 编排器：获取→政审→评分→梳理→输出
  config.py         # 环境变量配置
  schema.py         # Pydantic 数据模型
  client.py         # DeepSeek API 封装
  censor.py         # Phase 0: 政审过滤
  scorer.py         # Phase 1: 评分筛选
  analyzer.py       # Phase 2: 逐事件深度梳理
  test_*.py         # 测试
docs/               # 设计文档 & 实现计划
```

## 使用

### 手动执行

```bash
export DEEPSEEK_API_KEY=sk-your-key
export BLOG_CONTENT_DIR=/path/to/myBlog/src/content/weekly
cd weekly-cli && pip install -r requirements.txt && python main.py
```

### 自动执行（GitHub Actions）

每周一 00:00 UTC 自动运行，结果推送到 myBlog repo。

需要设置 GitHub Secrets：
- `DEEPSEEK_API_KEY` — DeepSeek API 密钥
- `BLOG_PAT` — 对 myBlog repo 有写权限的 Personal Access Token

## 技术栈

- **AI**: DeepSeek API (deepseek-chat)
- **后端**: Python 3 + openai SDK + Pydantic
- **前端**: Astro 4 + React 18 + TypeScript + Tailwind CSS
- **可视化**: react-force-graph-2d (D3-force)
