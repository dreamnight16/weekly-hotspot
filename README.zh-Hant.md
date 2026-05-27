**語言 / Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# 每週熱點深度梳理

[![Tests](https://img.shields.io/badge/tests-7%20passed%20%2B%207%20integration-green)](https://github.com/sixtdreanight/weekly-hotspot/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)

AI 驅動的熱點事件分析工具。每週自動抓取熱點新聞，透過 DeepSeek 進行政審過濾、價值評分、深度梳理（時間線 + 證據鏈 + 關係網），輸出結構化 JSON 到部落格渲染。

## 架構

```
DeepSeek API（聯網搜尋）
  ↓ 獲取本週熱點候選
[Phase 0] 政審過濾
  ↓ 排除敏感內容
[Phase 1] AI 評分篩選
  ↓ 事件影響 × 資訊增量 → 前 5-8 個
[Phase 2] 逐事件深度梳理
  ↓ 時間線 + 證據真偽 + 因果/關聯/反駁關係
輸出 JSON → myBlog content collection
  ↓ Astro 靜態建構
溯源報告風格頁面
```

## 專案結構

```
weekly-cli/         # Python CLI
  main.py           # 編排器：獲取→政審→評分→梳理→輸出
  config.py         # 環境變數配置
  schema.py         # Pydantic 資料模型
  client.py         # DeepSeek API 封裝
  censor.py         # Phase 0: 政審過濾
  scorer.py         # Phase 1: 評分篩選
  analyzer.py       # Phase 2: 逐事件深度梳理
  test_*.py         # 測試
docs/               # 設計文件 & 實現計畫
```

## 使用

### 手動執行

```bash
export DEEPSEEK_API_KEY=sk-your-key
export BLOG_CONTENT_DIR=/path/to/myBlog/src/content/weekly
cd weekly-cli && pip install -r requirements.txt && python main.py
```

### 自動執行（GitHub Actions）

每週一 00:00 UTC 自動執行，結果推送到 myBlog repo。

需要設定 GitHub Secrets：
- `DEEPSEEK_API_KEY` — DeepSeek API 金鑰
- `BLOG_PAT` — 對 myBlog repo 有寫入權限的 Personal Access Token

## 技術棧

- **AI**: DeepSeek API (deepseek-chat)
- **後端**: Python 3 + openai SDK + Pydantic
- **前端**: Astro 4 + React 18 + TypeScript + Tailwind CSS
- **視覺化**: react-force-graph-2d (D3-force)

## 相關專案

- [chinese-scraper-utils](https://github.com/sixtdreanight/chinese-scraper-utils) — 本專案使用的通用工具庫
- [myBlog](https://github.com/sixtdreanight/myBlog) — 每週報告發佈在 dreamnight.net.cn

---

<div align="center">

**Language / 語言 / 言語**

[**English**](README.md) | [**简体中文**](README.zh-CN.md) | [**繁體中文**](README.zh-Hant.md) | [**日本語**](README.ja.md)

</div>
