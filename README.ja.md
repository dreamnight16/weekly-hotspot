**言語 / Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# 格物（Dianalyze）— 弁証法的週次分析

[![Tests](https://img.shields.io/badge/tests-70%20unit%20%2B%209%20integration-green)](https://github.com/dreamnight16/weekly-hotspot/actions)
[![Coverage](https://img.shields.io/badge/coverage-82%25-brightgreen)](https://github.com/dreamnight16/weekly-hotspot/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)

毎週のホットスポット素材を収集し、必要に応じて分析するツールです。モデルがなくても取得またはキャッシュの読み込みと、出典付き JSON + Markdown レポートの出力ができます。モデルを設定した場合は、既存の分析、証拠確認、シナリオ整理を追加します。

## アーキテクチャ

```
Weibo / Zhihu / Hacker News（リアルタイムスクレイピング）
  ↓ ホットトピック取得 + 重複排除
[Phase 0] スクレイピング & キャッシュ
  ↓ 全ソース失敗時はキャッシュにフォールバック
[Phase 1] 思想審査フィルタリング（MLM 関連性）
  ↓ エンタメ / 政治的にセンシティブな内容を除外
[Phase 2] 任意のスコアリング選別
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
# 任意：分析フェーズを有効にする
export DEEPSEEK_API_KEY=sk-your-key
export BLOG_CONTENT_DIR=/path/to/Blog-mizuki/src/content/weekly
cd weekly-cli && pip install -r requirements.txt && python main.py
```

### 自動実行（GitHub Actions）

毎週月曜 00:00 UTC に自動実行され、結果が Blog-mizuki リポジトリにプッシュされます。

任意の GitHub Secrets：
- `DEEPSEEK_API_KEY` — 分析を有効にする。素材収集と証拠レポートには不要
- `pip install -r requirements-llm.txt` — モデル分析用のオプション依存関係
- `BLOG_PAT` — Blog-mizuki リポジトリへの書き込み権限を持つ Personal Access Token

## 技術スタック

- **任意の分析**: DeepSeek API (deepseek-chat)
- **バックエンド**: Python 3 + Pydantic。モデル分析時のみ OpenAI SDK が必要
- **フロントエンド**: Astro 4 + React 18 + TypeScript + Tailwind CSS
- **可視化**: react-force-graph-2d (D3-force)

## 関連プロジェクト

- [chinese-scraper-utils](https://github.com/dreamnight16/chinese-scraper-utils) — 本プロジェクトで使用する汎用ユーティリティライブラリ
- [Blog-mizuki](https://github.com/dreamnight16/Blog-mizuki) — 毎週のレポートは dreamnight.net.cn で公開

---

<div align="center">

**Language / 語言 / 言語**

[**English**](README.md) | [**简体中文**](README.zh-CN.md) | [**繁體中文**](README.zh-Hant.md) | [**日本語**](README.ja.md)

</div>
