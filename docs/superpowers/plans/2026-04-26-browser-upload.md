# ブラウザ取込UI 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `start.bat` をダブルクリックするだけでFlaskサーバーが起動し、ブラウザからLINEログをドラッグ&ドロップしてタスク表を生成できるWebアプリを作る。

**Architecture:** FlaskサーバーがPOST /uploadでファイルを受け取り、既存の `line_tasks.py` の関数を再利用してタスク表HTMLを生成し、ブラウザに返す。APIキーは `.env` ファイルで管理する。

**Tech Stack:** Python 3.8+, Flask, python-dotenv, 既存の anthropic SDK

---

## ファイル構成

```
C:\Users\admin\.local\bin\
├── server.py              ← 新規: Flaskサーバー
├── start.bat              ← 新規: ダブルクリック起動
├── .env                   ← ユーザーが手動作成（コードに含まない）
├── templates\
│   └── index.html         ← 新規: アップロード画面
├── tests\
│   └── test_server.py     ← 新規: サーバーのテスト
└── line_tasks.py          ← 変更なし
```

---

## Task 1: 依存パッケージのインストールとプロジェクト骨格

**Files:**
- Create: `C:\Users\admin\.local\bin\server.py`
- Create: `C:\Users\admin\.local\bin\tests\test_server.py`
- Create: `C:\Users\admin\.local\bin\templates\index.html`（空ファイル）

- [ ] **Step 1: Flask と python-dotenv をインストール**

```bash
pip install flask python-dotenv
```

期待出力: `Successfully installed flask-... python-dotenv-...`

- [ ] **Step 2: templates ディレクトリを作成**

```bash
mkdir "C:\Users\admin\.local\bin\templates"
```

- [ ] **Step 3: server.py の骨格を作成**

`C:\Users\admin\.local\bin\server.py` を以下の内容で作成：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from datetime import date
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
import line_tasks

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    pass


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
```

- [ ] **Step 4: テストファイルの骨格を作成**

`C:\Users\admin\.local\bin\tests\test_server.py` を以下の内容で作成：

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import server
```

- [ ] **Step 5: 空の templates/index.html を作成**

`C:\Users\admin\.local\bin\templates\index.html` を以下の内容で作成：

```html
<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><title>LINEタスク抽出</title></head>
<body><p>準備中</p></body></html>
```

- [ ] **Step 6: テストが実行できることを確認**

```bash
cd C:\Users\admin\.local\bin
python -m pytest tests\test_server.py -v
```

期待出力: `no tests ran`（エラーなし）

- [ ] **Step 7: コミット**

```bash
git add server.py tests\test_server.py templates\index.html
git commit -m "feat: scaffold Flask server"
```

---

## Task 2: POST /upload エンドポイント

**Files:**
- Modify: `C:\Users\admin\.local\bin\server.py`
- Modify: `C:\Users\admin\.local\bin\tests\test_server.py`

- [ ] **Step 1: /upload エンドポイントの失敗テストを書く**

`tests\test_server.py` に追加：

```python
import json
from unittest.mock import patch, MagicMock


class TestUploadEndpoint(unittest.TestCase):

    def setUp(self):
        server.app.config["TESTING"] = True
        self.client = server.app.test_client()

    def _make_sample_txt(self):
        content = (
            "[LINE] \"テストグループ\"のトーク履歴\n\n"
            "保存日時：2026年4月26日 10:00\n\n"
            "2026/04/20(月) 10:32\t田中\t見積書を提出してください\n"
            "2026/04/20(月) 10:35\t課長\t木曜までにお願いします\n"
        )
        return content.encode("utf-8")

    def test_no_file_returns_400(self):
        resp = self.client.post("/upload")
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    def test_non_txt_file_returns_400(self):
        from io import BytesIO
        resp = self.client.post(
            "/upload",
            data={"file": (BytesIO(b"dummy"), "log.pdf")},
            content_type="multipart/form-data"
        )
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    def test_valid_txt_calls_pipeline_and_returns_html(self):
        from io import BytesIO
        mock_tasks = [{
            "content": "見積書を提出する", "assignee": "田中",
            "deadline": "4/28", "priority": "高",
            "speaker": "課長", "datetime": "2026/04/20(月) 10:35"
        }]
        with patch("server.line_tasks.extract_tasks_via_api", return_value=mock_tasks):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-dummy"}):
                resp = self.client.post(
                    "/upload",
                    data={"file": (BytesIO(self._make_sample_txt()), "log.txt")},
                    content_type="multipart/form-data"
                )
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("見積書を提出する", html)

    def test_missing_api_key_returns_500(self):
        from io import BytesIO
        with patch.dict(os.environ, {}, clear=True):
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]
            resp = self.client.post(
                "/upload",
                data={"file": (BytesIO(self._make_sample_txt()), "log.txt")},
                content_type="multipart/form-data"
            )
        self.assertEqual(resp.status_code, 500)
        data = json.loads(resp.data)
        self.assertIn("error", data)
```

- [ ] **Step 2: テストを実行して FAIL を確認**

```bash
python -m pytest tests\test_server.py::TestUploadEndpoint -v
```

期待出力: 全テストが FAIL または ERROR

- [ ] **Step 3: /upload エンドポイントを実装**

`server.py` の `upload` 関数を置き換え：

```python
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "ファイルが送信されていません"}), 400

    f = request.files["file"]
    if not f.filename.endswith(".txt"):
        return jsonify({"error": ".txtファイルを選択してください"}), 400

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": ".envファイルにAPIキーを設定してください"}), 500

    raw_text = f.read().decode("utf-8", errors="replace")
    parsed = line_tasks.parse_line_log(raw_text)
    messages = parsed["messages"]

    if not messages:
        return jsonify({"error": "メッセージが見つかりませんでした。LINEのエクスポート形式を確認してください"}), 400

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    chunks = line_tasks.split_into_chunks(messages)
    all_tasks = []
    for chunk in chunks:
        tasks = line_tasks.extract_tasks_via_api(chunk, client)
        all_tasks.extend(tasks)

    all_tasks = line_tasks.deduplicate_tasks(all_tasks)

    if not all_tasks:
        return jsonify({"error": "タスクが見つかりませんでした"}), 200

    meta = {
        "start_date": parsed["start_date"],
        "end_date": parsed["end_date"],
        "generated_at": date.today().isoformat(),
    }
    html = line_tasks.generate_html(all_tasks, meta)
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}
```

- [ ] **Step 4: テストを実行して PASS を確認**

```bash
python -m pytest tests\test_server.py::TestUploadEndpoint -v
```

期待出力: 全4テストが PASS

- [ ] **Step 5: コミット**

```bash
git add server.py tests\test_server.py
git commit -m "feat: add POST /upload endpoint"
```

---

## Task 3: アップロード画面 HTML

**Files:**
- Modify: `C:\Users\admin\.local\bin\templates\index.html`

テストは不要（静的HTML）。ブラウザで目視確認する。

- [ ] **Step 1: index.html を実装**

`C:\Users\admin\.local\bin\templates\index.html` を以下の内容で置き換え：

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LINEタスク抽出ツール</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Hiragino Sans', 'Meiryo', sans-serif;
      background: #f5f7fa;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .card {
      background: #fff;
      border-radius: 16px;
      padding: 40px;
      width: 100%;
      max-width: 480px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.08);
      text-align: center;
    }
    h1 { font-size: 22px; color: #1a1a2e; margin-bottom: 8px; }
    .subtitle { font-size: 14px; color: #888; margin-bottom: 32px; }
    .dropzone {
      border: 2px dashed #4a90e2;
      border-radius: 12px;
      padding: 48px 24px;
      background: #f0f7ff;
      cursor: pointer;
      transition: background 0.2s, border-color 0.2s;
      margin-bottom: 16px;
    }
    .dropzone.dragover {
      background: #dbeeff;
      border-color: #1a6fcc;
    }
    .dropzone .icon { font-size: 48px; margin-bottom: 12px; }
    .dropzone .main-text { font-size: 16px; font-weight: bold; color: #333; margin-bottom: 6px; }
    .dropzone .or { font-size: 13px; color: #aaa; margin-bottom: 14px; }
    .btn-select {
      display: inline-block;
      background: #4a90e2;
      color: #fff;
      padding: 10px 28px;
      border-radius: 8px;
      font-size: 14px;
      cursor: pointer;
      border: none;
      transition: background 0.2s;
    }
    .btn-select:hover { background: #357abd; }
    .hint { font-size: 12px; color: #bbb; margin-bottom: 20px; }
    #status {
      display: none;
      padding: 14px 18px;
      border-radius: 8px;
      font-size: 14px;
      margin-top: 8px;
    }
    #status.processing { background: #e8f4fd; color: #1a6fcc; border: 1px solid #b3d9f7; }
    #status.error { background: #fff0f0; color: #cc0000; border: 1px solid #ffb3b3; }
    #file-input { display: none; }
    #result { display: none; margin-top: 24px; }
    .result-btn {
      display: inline-block;
      background: #52c41a;
      color: #fff;
      padding: 12px 32px;
      border-radius: 8px;
      font-size: 15px;
      cursor: pointer;
      border: none;
      font-weight: bold;
      transition: background 0.2s;
    }
    .result-btn:hover { background: #389e0d; }
  </style>
</head>
<body>
<div class="card">
  <h1>LINEタスク抽出ツール</h1>
  <p class="subtitle">LINEのトーク履歴からタスクをAIが自動抽出します</p>

  <div class="dropzone" id="dropzone">
    <div class="icon">📂</div>
    <div class="main-text">ここにファイルをドロップ</div>
    <div class="or">または</div>
    <button class="btn-select" onclick="document.getElementById('file-input').click()">
      ファイルを選択
    </button>
  </div>
  <div class="hint">対応形式: .txt（LINEのトーク履歴エクスポート）</div>
  <input type="file" id="file-input" accept=".txt">

  <div id="status"></div>
  <div id="result">
    <button class="result-btn" id="open-btn">タスク表を開く</button>
  </div>
</div>

<script>
  let resultHtml = "";

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const status = document.getElementById("status");
  const result = document.getElementById("result");

  dropzone.addEventListener("dragover", e => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
  dropzone.addEventListener("drop", e => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) processFile(fileInput.files[0]);
  });

  function showStatus(msg, type) {
    status.textContent = msg;
    status.className = type;
    status.style.display = "block";
  }

  async function processFile(file) {
    if (!file.name.endsWith(".txt")) {
      showStatus(".txtファイルを選択してください", "error");
      return;
    }

    result.style.display = "none";
    showStatus("⏳ AIがタスクを抽出中です。しばらくお待ちください...", "processing");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const resp = await fetch("/upload", { method: "POST", body: formData });
      const contentType = resp.headers.get("content-type") || "";

      if (contentType.includes("text/html")) {
        resultHtml = await resp.text();
        status.style.display = "none";
        result.style.display = "block";
      } else {
        const data = await resp.json();
        showStatus("エラー: " + (data.error || "不明なエラーが発生しました"), "error");
      }
    } catch (e) {
      showStatus("エラー: サーバーに接続できませんでした", "error");
    }
  }

  document.getElementById("open-btn").addEventListener("click", () => {
    const win = window.open("", "_blank");
    win.document.write(resultHtml);
    win.document.close();
  });
</script>
</body>
</html>
```

- [ ] **Step 2: サーバーを起動してブラウザで確認**

```bash
cd C:\Users\admin\.local\bin
set ANTHROPIC_API_KEY=dummy_for_test
python server.py
```

ブラウザで `http://localhost:5000` を開いて確認：
- カード中央に表示される
- ドロップゾーンが見える
- 「ファイルを選択」ボタンが機能する
- `.txt` 以外のファイルを選んだとき「.txtファイルを選択してください」と出る

確認後、`Ctrl+C` でサーバーを止める。

- [ ] **Step 3: コミット**

```bash
git add templates\index.html
git commit -m "feat: add drag-and-drop upload UI"
```

---

## Task 4: start.bat の作成

**Files:**
- Create: `C:\Users\admin\.local\bin\start.bat`

テストは不要（バッチファイル）。

- [ ] **Step 1: start.bat を作成**

`C:\Users\admin\.local\bin\start.bat` を以下の内容で作成：

```bat
@echo off
cd /d %~dp0

if not exist ".env" (
    echo .envファイルが見つかりません。
    echo 同じフォルダに .env ファイルを作成して、
    echo ANTHROPIC_API_KEY=sk-ant-ここにキーを貼り付け
    echo と書いてください。
    pause
    exit /b 1
)

echo LINEタスク抽出ツールを起動しています...
start http://localhost:5000
python server.py
pause
```

- [ ] **Step 2: .env のサンプルファイルを作成**

`C:\Users\admin\.local\bin\.env.example` を以下の内容で作成（実際のキーは含まない）：

```
ANTHROPIC_API_KEY=sk-ant-ここにAPIキーを貼り付け
```

- [ ] **Step 3: .env を .gitignore に追加**

`C:\Users\admin\.local\bin\.gitignore` を作成：

```
.env
__pycache__/
*.pyc
.superpowers/
```

- [ ] **Step 4: コミット**

```bash
git add start.bat .env.example .gitignore
git commit -m "feat: add start.bat launcher and .env setup"
```

---

## Task 5: 全テストを通して動作確認

**Files:**
- なし（確認のみ）

- [ ] **Step 1: 全テストを実行**

```bash
cd C:\Users\admin\.local\bin
python -m pytest tests\ -v
```

期待出力: `23 passed`（既存19 + 新規4）

- [ ] **Step 2: .env ファイルを作成して実際に動作確認**

`.env` ファイルを作成（実際のAPIキーを使う）：

```
ANTHROPIC_API_KEY=sk-ant-実際のキー
```

`start.bat` をダブルクリック（またはコマンドプロンプトで実行）：
```bash
start.bat
```

確認項目：
- ブラウザが `http://localhost:5000` を開く
- アップロード画面が表示される
- `sample_log.txt` をドラッグ&ドロップして「タスク表を開く」ボタンが出る
- ボタンをクリックするとタスク表が新しいタブで開く
- タスク表でステータスの切り替えが動く

- [ ] **Step 3: 最終コミット**

```bash
git add -A
git commit -m "feat: browser upload UI complete"
```

---

## セルフレビュー結果

**スペックカバレッジ:**
- ✅ `start.bat` ダブルクリックで起動
- ✅ ブラウザ自動オープン
- ✅ ドラッグ&ドロップ対応
- ✅ ファイル選択ボタン
- ✅ `.env` でAPIキー管理
- ✅ メモリ上のみで処理（ディスク保存なし）
- ✅ .txt 以外のファイルのエラー表示
- ✅ APIキー未設定のエラー表示
- ✅ API呼び出し失敗のエラー表示
- ✅ タスク0件のメッセージ
- ✅ タスク表を新しいタブで表示
- ✅ line_tasks.py は変更なし（既存関数を再利用）

**プレースホルダーなし:** 全ステップに実際のコードを記載済み

**型・関数名の一貫性:**
- `line_tasks.parse_line_log` → Task 2で使用 ✅
- `line_tasks.split_into_chunks` → Task 2で使用 ✅
- `line_tasks.extract_tasks_via_api` → Task 2で使用 ✅
- `line_tasks.deduplicate_tasks` → Task 2で使用 ✅
- `line_tasks.generate_html` → Task 2で使用 ✅
