**言語 / Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# 週間ホットスポット深掘り分析

[![Tests](https://img.shields.io/badge/tests-7%20passed%20%2B%207%20integration-green)](https://github.com/sixtdreanight/weekly-hotspot/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)

AI 駆動のホットスポット分析ツール。毎週自動でホットニュースを収集し、DeepSeek による思想審査フィルタリング、価値スコアリング、深掘り分析（タイムライン + 証拠連鎖 + 関係性ネットワーク）を実施し、構造化 JSON をブログに出力してレンダリングします。

## アーキテクチャ

```
DeepSeek API（Web 検索連携）
  ↓ 今週のホットスポット候補を取得
[Phase 0] 思想審査フィルタリング
  ↓ センシティブな内容を除外
[Phase 1] AI スコアリング選別
  ↓ イベント影響度 × 情報付加価値 → 上位 5〜8 件
[Phase 2] イベントごとの深掘り分析
  ↓ タイムライン + 証拠の真偽 + 因果/関連/反論関係
JSON 出力 → myBlog content collection
  ↓ Astro 静的ビルド
トレーサビリティレポート形式のページ
```

## プロジェクト構成

```
weekly-cli/         # Python CLI
  main.py           # オーケストレーター：取得→審査→スコアリング→分析→出力
  config.py         # 環境変数設定
  schema.py         # Pydantic データモデル
  client.py         # DeepSeek API ラッパー
  censor.py         # Phase 0: 思想審査フィルタリング
  scorer.py         # Phase 1: スコアリング選別
  analyzer.py       # Phase 2: イベントごとの深掘り分析
  test_*.py         # テスト
docs/               # 設計ドキュメント & 実装計画
```

## 使用方法

### 手動実行

```bash
export DEEPSEEK_API_KEY=sk-your-key
export BLOG_CONTENT_DIR=/path/to/myBlog/src/content/weekly
cd weekly-cli && pip install -r requirements.txt && python main.py
```

### 自動実行（GitHub Actions）

毎週月曜 00:00 UTC に自動実行され、結果が myBlog リポジトリにプッシュされます。

GitHub Secrets の設定が必要：
- `DEEPSEEK_API_KEY` — DeepSeek API キー
- `BLOG_PAT` — myBlog リポジトリへの書き込み権限を持つ Personal Access Token

## 技術スタック

- **AI**: DeepSeek API (deepseek-chat)
- **バックエンド**: Python 3 + openai SDK + Pydantic
- **フロントエンド**: Astro 4 + React 18 + TypeScript + Tailwind CSS
- **可視化**: react-force-graph-2d (D3-force)

## 関連プロジェクト

- [chinese-scraper-utils](https://github.com/sixtdreanight/chinese-scraper-utils) — 本プロジェクトで使用する汎用ユーティリティライブラリ
- [myBlog](https://github.com/sixtdreanight/myBlog) — 毎週のレポートは dreamnight.net.cn で公開

---

<div align="center">

**Language / 語言 / 言語**

[**English**](README.md) | [**简体中文**](README.zh-CN.md) | [**繁體中文**](README.zh-Hant.md) | [**日本語**](README.ja.md)

</div>
