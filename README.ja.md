**言語 / Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# ComiRadar

[![CI](https://github.com/dreamnight16/anime-con-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/dreamnight16/anime-con-radar/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-orange)](https://github.com/dreamnight16/anime-con-radar)

**今後90日間の全国の同人誌即売会・漫画イベント・アニソンライブなどのイベント情報を自動検出します。**

Bilibili會員購、大麥、秀動、貓眼、票星球、永樂などの9つのチケットプラットフォーム、およびWeibo、Bilibili動態、小紅書からスクレイピングし、統一フォーマットで出力します。

### データソース

Bilibili (會員購) · Damai (大麥) · Showstart (秀動) · Maoyan (貓眼) · Piaoxingqiu (票星球) · Yongle (永樂) · Weibo (微博) · Bilibili Dynamics · Xiaohongshu (小紅書)

### 重複排除戦略

2層の重複排除：SHA256フィンガープリントによる完全一致 + 都市/日付/タイトルによる曖昧マージ。欠落フィールドを補完します。

## 使い方

```bash
pip install -r requirements.txt
python main.py scrape   # 全プラットフォームをスクレイピング
python main.py export   # events.json をエクスポート
python main.py notify   # 通知をプッシュ（キーの設定が必要）
python main.py run      # ワンクリックで全実行
```

任意のモデル抽出を使う場合は `pip install openai`（または `uv sync --extra llm --no-install-project`）を実行し、`DEEPSEEK_API_KEY` を設定してください。SDK またはキーがなければ、投稿をルールで解析します。

## Docker

```bash
# ビルドして完全なパイプラインを実行
docker compose run --rm comiradar

# 個別のステップを実行
docker compose run --rm scrape   # スクレイピングのみ
docker compose run --rm export   # エクスポートのみ
docker compose run --rm notify   # 通知のみ

# データは ./data/ に永続化されます
```

## 設定

`config.py` を編集して通知キーを設定します：

```python
NOTIFIERS = {
    "serverchan": {"key": "your-SendKey"},
    "bark": {"url": "https://api.day.app/your-key"},
}
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `BILI_BUVID3` | B站 cookies の `buvid3` |
| `BILI_SESSDATA` | B站 cookies の `SESSDATA` |
| `BILI_BILI_JCT` | B站 cookies の `bili_jct` |
| `DAMAI_M_H5_TK` | 大麥 cookies の `m_h5_tk` |
| `DAMAI_COOKIE2` | 大麥 cookies の `cookie2` |
| `DEEPSEEK_API_KEY` | 任意の DeepSeek キー（ソーシャル投稿の構造化抽出用）。未設定時は決定的な解析を使用 |
| `COMI_EXPORT_PATH` | エクスポートパス（オプション、デフォルトはプロジェクトディレクトリ） |

## ブログ連携

このリポジトリは git submodule として [Blog-mizuki](https://github.com/dreamnight16/Blog-mizuki) を導入しており、GitHub Actions で定期的に実行され、データは [イベントページ](https://comi.dreamnight.net.cn) に自動反映されます。

## 技術スタック

- **スクレイピング**: Python 3.11+ · Playwright · HTTPX
- **ストレージ**: SQLite
- **スケジュール**: GitHub Actions (cron)
- **連携**: Git submodule → Astro ブログ

## 関連プロジェクト

- [chinese-scraper-utils](https://github.com/dreamnight16/chinese-scraper-utils) — 本プロジェクトから抽出した汎用ユーティリティライブラリ
- [Blog-mizuki](https://github.com/dreamnight16/Blog-mizuki) — イベントデータを dreamnight.net.cn/anime-events で表示（現在）
- [myBlog](https://github.com/dreamnight16/myBlog) — 旧ブログ（アーカイブ済み）

## ライセンス

MIT

---

<div align="center">

**Language / 言語**

[**English**](README.md) | [**简体中文**](README.zh-CN.md) | [**繁體中文**](README.zh-Hant.md) | [**日本語**](README.ja.md)

</div>
