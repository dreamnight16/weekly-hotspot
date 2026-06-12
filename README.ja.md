**言語 / Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# 週間ホットスポット深掘り分析

[![Tests](https://img.shields.io/badge/tests-70%20unit%20%2B%209%20integration-green)](https://github.com/sixtdreanight/weekly-hotspot/actions)
[![Coverage](https://img.shields.io/badge/coverage-82%25-brightgreen)](https://github.com/sixtdreanight/weekly-hotspot/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)

AI 駆動のホットスポット分析ツール。毎週自動でホットニュースを収集し、DeepSeek による思想審査フィルタリング、価値スコアリング、深掘り分析（タイムライン + 証拠連鎖 + 関係性ネットワーク）を実施し、構造化 JSON をブログに出力してレンダリングします。

## アーキテクチャ

```
Weibo / Zhihu / Hacker News（リアルタイムスクレイピング）
  ↓ ホットトピック取得 + 重複排除
[Phase 0] スクレイピング & キャッシュ
  ↓ 全ソース失敗時はキャッシュにフォールバック
[Phase 1] 思想審査フィルタリング（MLM 関連性）
  ↓ エンタメ / 政治的にセンシティブな内容を除外
[Phase 2] AI スコアリング選別
  ↓ イベント影響度 × 情報付加価値 → 上位 8 件
[Phase 3] イベントごとの深掘り分析（並列 3 スレッド）
  ↓ DuckDuckGo + Bing 検索 → タイムライン + 証拠 + 関係
[Phase 4] イベント間の総合整理
  ↓ テーマ + トレンド + 矛盾の運動
出力 → JSON + Markdown 記事 → Blog-mizuki リポジトリ
```

## プロジェクト構成

```
weekly-cli/          # Python CLI パイプライン
  main.py            # オーケストレーター：5 フェーズパイプライン
  config.py           # 環境変数設定 + パスセーフティ
  schema.py           # Pydantic v2 データモデル（14 モデル）
  censor.py           # Phase 1：思想審査フィルタリング
  scorer.py           # Phase 2：スコアリング選別
  analyzer.py         # Phase 3：イベントごとの深掘り分析
  search.py           # 並列 DDG + Bing 検索 + 重複排除
  synthesizer.py      # Phase 4：イベント間総合整理
  article.py          # Markdown 記事生成
  cache.py            # スクレイピングキャッシュ
  test_*.py           # 単体テスト & 統合テスト（80%+ カバレッジ）
prompts/              # 外部化 LLM プロンプトテンプレート

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
