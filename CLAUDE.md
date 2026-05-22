# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このリポジトリには2つの独立したWebアプリが含まれる。

| アプリ | 起動ファイル | 説明 |
|--------|------------|------|
| LINEタスク抽出 | `server.py` | LINEのトーク履歴(.txt)をアップロードしてタスクをAI抽出するFlaskアプリ |
| ことだま占い | `kotodama/app.py` | 名前の言霊と気象・暦データをもとにClaude APIで占い結果を生成するFlaskアプリ |

また `line_log_app.py` はStreamlitベースの別実装（LINEログ整理UI）。

## コマンド

```bash
# テスト（全体）
python -m pytest tests/ kotodama/tests/ -q

# テスト（単一ファイル）
python -m pytest tests/test_server.py -q
python -m pytest kotodama/tests/test_fortune_engine.py -q

# LINEタスク抽出アプリをローカル起動
python server.py           # http://localhost:5000
# または
start.bat                  # Windowsでブラウザを自動オープン

# ことだま占いアプリをローカル起動
cd kotodama && python app.py

# 本番（Heroku想定）
gunicorn server:app --bind 0.0.0.0:$PORT
```

## 環境変数

**LINEタスク抽出** (`.env`):
```
ANTHROPIC_API_KEY=sk-ant-...
```

**ことだま占い** (`kotodama/.env`):
```
ANTHROPIC_API_KEY=...
FLASK_SECRET_KEY=...
```

`server.py` は `.env` を2重ロード（`dotenv` + 手動パース）している。これは BOM付きUTF-8 ファイルへの対応のため意図的。

## アーキテクチャ

### LINEタスク抽出 (`server.py` + `line_tasks.py`)

```
server.py (Flask routes)
  └─ /upload → line_tasks.py
       ├─ parse_line_log()      # LINEエクスポート形式を2種類サポート（旧: タブ区切り1行 / 新: 日付行+時刻行）
       ├─ split_into_chunks()   # API制限を考慮してメッセージをチャンク分割
       ├─ extract_tasks_via_api()  # Claude claude-3-5-haiku でタスク抽出（JSON応答）
       ├─ deduplicate_tasks()   # 重複排除
       └─ generate_html()       # 結果をHTML文字列で返す（テンプレートなし）
```

- LINEエクスポート形式は旧形式（`YYYY/MM/DD(曜日) HH:MM\t送信者\t本文`）と新形式（日付行 + 時刻行）の両方に対応
- 抽出結果HTMLは `server.py` の `/upload` エンドポイントがそのまま返す（テンプレートファイルなし）

### ことだま占い (`kotodama/`)

```
app.py (Flask routes)
  ├─ name_analyzer.py    # 姓名の漢字画数・意味・音韻分析
  ├─ kanji_dict.py       # 漢字画数・意味データ
  ├─ popular_names.py    # 人気名前データ（関連名表示用）
  ├─ stats_fetcher.py    # 気象API(Open-Meteo) + 暦データ（六曜・節気・祝日）取得
  ├─ fortune_engine.py   # Claude APIに渡すプロンプト構築 + JSON応答パース
  ├─ image_generator.py  # 占い結果の画像生成（Pillow）
  └─ cache.py            # SHA-256キーでJSONをファイルキャッシュ（kotodama/.fortune_cache/）
```

- 占い結果は `(姓+名+日付)` のSHA-256ハッシュをキーとしてファイルキャッシュ。同じ名前・同じ日は再生成しない
- `stats_fetcher.py` の都市座標は `CITY_COORDS` dictで管理。対応都市外はデフォルト（東京）を使用
- `app.py` は `kotodama/` ディレクトリから起動する必要がある（相対importのため）

## テンプレート

- LINEタスク抽出: `templates/index.html`（`server.py` 用）
- ことだま占い: `kotodama/templates/`（`base.html` を継承）

## 履歴管理ツール（PowerShell）

`generate_history.ps1` はデスクトップに `history.html`（作業履歴ビューアー）を生成するローカルツール。このファイルはプロダクションコードではなく開発補助ツール。
