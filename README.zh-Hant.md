**語言 / Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# 每週熱點深度梳理

[![Tests](https://img.shields.io/badge/tests-70%20unit%20%2B%209%20integration-green)](https://github.com/sixtdreanight/weekly-hotspot/actions)
[![Coverage](https://img.shields.io/badge/coverage-82%25-brightgreen)](https://github.com/sixtdreanight/weekly-hotspot/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)

AI 驅動的熱點事件分析工具。每週自動抓取熱點新聞，透過 DeepSeek 進行政審過濾、價值評分、深度梳理（時間線 + 證據鏈 + 關係網），輸出結構化 JSON 到部落格渲染。

## 架構

```
微博 / 知乎 / Hacker News（即時抓取）
  ↓ 獲取熱點話題 + 去重
[Phase 0] 抓取 & 快取
  ↓ 抓取全失敗時回退快取
[Phase 1] 政審過濾（MLM 相關性）
  ↓ 排除娛樂八卦 / 政治敏感內容
[Phase 2] AI 評分篩選
  ↓ 事件影響 × 資訊增量 → 前 8 個
[Phase 3] 逐事件深度梳理（並行 3 執行緒）
  ↓ DuckDuckGo + Bing 搜尋 → 時間線 + 證據 + 關係
[Phase 4] 跨事件綜合梳理
  ↓ 主題 + 趨勢 + 矛盾運動
輸出 → JSON + Markdown 文章 → Blog-mizuki 倉庫
```

## 專案結構

```
weekly-cli/          # Python CLI 流水線
  main.py            # 編排器：5 階段流水線驅動
  config.py           # 環境變數配置 + 路徑安全校驗
  schema.py           # Pydantic v2 資料模型（14 個模型）
  censor.py           # Phase 1：政審過濾
  scorer.py           # Phase 2：評分篩選
  analyzer.py         # Phase 3：逐事件深度梳理
  search.py           # 並行 DDG + Bing 搜尋 + 去重
  synthesizer.py      # Phase 4：跨事件綜合梳理
  article.py          # Markdown 文章生成器
  cache.py            # 抓取快取回退
  test_*.py           # 單元測試 & 整合測試（80%+ 覆蓋率）
prompts/              # 外部化 LLM 提示詞模板

## 使用

### 手動執行

```bash
export DEEPSEEK_API_KEY=sk-your-key
export BLOG_CONTENT_DIR=/path/to/Blog-mizuki/src/content/weekly
cd weekly-cli && pip install -r requirements.txt && python main.py
```

### 自動執行（GitHub Actions）

每週一 00:00 UTC 自動執行，結果推送到 Blog-mizuki repo。

需要設定 GitHub Secrets：
- `DEEPSEEK_API_KEY` — DeepSeek API 金鑰
- `BLOG_PAT` — 對 Blog-mizuki repo 有寫入權限的 Personal Access Token

## 技術棧

- **AI**: DeepSeek API (deepseek-chat)
- **後端**: Python 3 + openai SDK + Pydantic
- **前端**: Astro 4 + React 18 + TypeScript + Tailwind CSS
- **視覺化**: react-force-graph-2d (D3-force)

## 相關專案

- [chinese-scraper-utils](https://github.com/sixtdreanight/chinese-scraper-utils) — 本專案使用的通用工具庫
- [Blog-mizuki](https://github.com/sixtdreanight/Blog-mizuki) — 每週報告發佈在 dreamnight.net.cn

---

<div align="center">

**Language / 語言 / 言語**

[**English**](README.md) | [**简体中文**](README.zh-CN.md) | [**繁體中文**](README.zh-Hant.md) | [**日本語**](README.ja.md)

</div>
