**语言 / Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# 格物（Dianalyze）— 辩证周报

[![Tests](https://img.shields.io/badge/tests-70%20unit%20%2B%209%20integration-green)](https://github.com/sixtdreanight/weekly-hotspot/actions)
[![Coverage](https://img.shields.io/badge/coverage-82%25-brightgreen)](https://github.com/sixtdreanight/weekly-hotspot/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)

以唯物辩证法和历史唯物主义为核心方法论的 AI 热点分析系统。每周自动抓取热点新闻，通过辩证认识运动五阶段（现象把握→矛盾识别→辩证展开→历史定位→实践指向）进行深度分析，辅以证据验证、定量数据、多轮对抗等现代分析手段。输出结构化 JSON + Markdown 文章到博客渲染。

## 架构

```
微博 / 知乎 / Hacker News（实时抓取）
  ↓ 获取热点话题 + 去重
[Phase 0] 抓取 & 缓存
  ↓ 抓取全失败时回退缓存
[Phase 1] 政审过滤（MLM 相关性）
  ↓ 排除娱乐八卦 / 政治敏感内容
[Phase 2] AI 评分筛选
  ↓ 事件影响 × 信息增量 → 前 8 个
[Phase 3] 逐事件深度梳理（并行 3 线程）
  ↓ DuckDuckGo + Bing 搜索 → 时间线 + 证据 + 关系
[Phase 4] 跨事件综合梳理
  ↓ 主题 + 趋势 + 矛盾运动
输出 → JSON + Markdown 文章 → Blog-mizuki 仓库
```

## 项目结构

```
weekly-cli/          # Python CLI 流水线
  main.py            # 编排器：5 阶段流水线驱动
  config.py           # 环境变量配置 + 路径安全校验
  schema.py           # Pydantic v2 数据模型（14 个模型）
  censor.py           # Phase 1：政审过滤
  scorer.py           # Phase 2：评分筛选
  analyzer.py         # Phase 3：逐事件深度梳理
  search.py           # 并行 DDG + Bing 搜索 + 去重
  synthesizer.py      # Phase 4：跨事件综合梳理
  article.py          # Markdown 文章生成器
  cache.py            # 抓取缓存回退
  test_*.py           # 单元测试 & 集成测试（80%+ 覆盖率）
prompts/              # 外部化 LLM 提示词模板

## 使用

### 手动执行

```bash
export DEEPSEEK_API_KEY=sk-your-key
export BLOG_CONTENT_DIR=/path/to/Blog-mizuki/src/content/weekly
cd weekly-cli && pip install -r requirements.txt && python main.py
```

### 自动执行（GitHub Actions）

每周一 00:00 UTC 自动运行，结果推送到 Blog-mizuki repo。

需要设置 GitHub Secrets：
- `DEEPSEEK_API_KEY` — DeepSeek API 密钥
- `BLOG_PAT` — 对 Blog-mizuki repo 有写权限的 Personal Access Token

## 技术栈

- **AI**: DeepSeek API (deepseek-chat)
- **后端**: Python 3 + openai SDK + Pydantic
- **前端**: Astro 4 + React 18 + TypeScript + Tailwind CSS
- **可视化**: react-force-graph-2d (D3-force)

## 相关项目

- [chinese-scraper-utils](https://github.com/sixtdreanight/chinese-scraper-utils) — 本项目使用的通用工具库
- [Blog-mizuki](https://github.com/sixtdreanight/Blog-mizuki) — 每周报告发布在 dreamnight.net.cn

---

<div align="center">

**Language / 语言 / 言語**

[**English**](README.md) | [**简体中文**](README.zh-CN.md) | [**繁體中文**](README.zh-Hant.md) | [**日本語**](README.ja.md)

</div>
