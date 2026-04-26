# ブラウザ取込UI — 設計書

**作成日:** 2026-04-26
**ステータス:** 承認済み

---

## 概要

`start.bat` をダブルクリックするだけで Flask サーバーが起動し、ブラウザからLINEのトーク履歴（.txt）をドラッグ&ドロップしてタスク表を生成できるWebアプリ。既存の `line_tasks.py` の処理関数はそのまま再利用する。

---

## ファイル構成

```
C:\Users\admin\.local\bin\
├── server.py          ← Flaskサーバー本体（新規）
├── start.bat          ← ダブルクリック起動バッチ（新規）
├── .env               ← APIキー保存（ユーザーが手動作成）
├── templates\
│   └── index.html     ← アップロード画面HTML（新規）
└── line_tasks.py      ← 変更なし
```

---

## 使い方（完成後）

| 手順 | 操作 |
|------|------|
| 初回のみ | `.env` ファイルに `ANTHROPIC_API_KEY=sk-ant-...` を1行書く |
| 毎回 | `start.bat` をダブルクリック → ブラウザが自動で開く |
| ログ取込 | ファイルをドロップまたは「ファイルを選択」ボタンで選ぶ |
| 結果確認 | 同じページにタスク表が表示される |

---

## アーキテクチャ

```
[ブラウザ]
  ファイル選択 / ドラッグ&ドロップ
        ↓ POST /upload (multipart)
[server.py — Flask]
  1. .txt ファイルを受け取る
  2. line_tasks.parse_line_log() でメッセージ抽出
  3. line_tasks.split_into_chunks() で分割
  4. line_tasks.extract_tasks_via_api() でClaude API呼び出し
  5. line_tasks.deduplicate_tasks() で重複除去
  6. line_tasks.generate_html() でHTML生成
  7. HTMLをブラウザに返す（ファイル保存なし）
        ↓ レスポンス: タスク表HTML
[ブラウザ]
  タスク表を表示（進捗管理・フィルター・印刷 すべてそのまま）
```

---

## 各ファイルの仕様

### server.py

```python
# エンドポイント
GET  /          → templates/index.html を返す
POST /upload    → .txt を受け取り、タスク表HTMLを返す
```

- `python-dotenv` で `.env` からAPIキーを読む
- アップロードされたファイルはメモリ上で処理（ディスク保存なし）
- エラー時はブラウザにエラーメッセージを表示

### start.bat

```bat
@echo off
cd /d %~dp0
start http://localhost:5000
python server.py
pause
```

- `start http://localhost:5000` でブラウザを先に開く（サーバー起動前に開くが、リロードで対応）
- `pause` でエラー発生時にウィンドウが閉じない

### .env（ユーザーが作成）

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
```

### templates/index.html

- ドラッグ&ドロップ対応のファイルアップロードUI
- ファイル選択後、JavaScriptで自動的に `POST /upload` を送信
- 処理中は「処理中...」の表示
- レスポンスのHTMLをそのままページに差し込む（`innerHTML`）

---

## エラーハンドリング

| エラー | 表示 |
|--------|------|
| .txt 以外のファイル | 「.txtファイルを選択してください」 |
| APIキー未設定 | 「.envファイルにAPIキーを設定してください」 |
| API呼び出し失敗 | 「AI処理に失敗しました。再試行してください」 |
| タスクが0件 | 「タスクが見つかりませんでした」 |

---

## 追加インストール

```bash
pip install flask python-dotenv
```

---

## 制約

- ローカル専用（外部公開しない）
- ファイルはメモリ上のみで処理、ディスクに保存しない
- 同時アクセスは1ユーザーのみ想定
