# LINE タスク抽出ツール 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** LINEエクスポートの .txt ファイルを読み込み、Claude API でタスクを抽出して、進捗管理付きのHTMLタスク表を生成する Python CLIツールを作る。

**Architecture:** Python スクリプト1ファイル（`line_tasks.py`）が、LINEログのパース → Claude API呼び出し → HTML生成 を順に実行する。HTMLは埋め込みCSS/JSで完結し、外部依存なし。

**Tech Stack:** Python 3.8+, anthropic SDK, unittest + unittest.mock（テスト用）

---

## ファイル構成

```
C:\Users\admin\.local\bin\
├── line_tasks.py          ← メインスクリプト（全機能を含む）
├── tests\
│   └── test_line_tasks.py ← ユニットテスト
└── docs\
    └── superpowers\
        └── plans\
            └── 2026-04-26-line-task-extractor.md  ← このファイル
```

---

## Task 1: プロジェクトセットアップ

**Files:**
- Create: `C:\Users\admin\.local\bin\line_tasks.py`
- Create: `C:\Users\admin\.local\bin\tests\test_line_tasks.py`

- [ ] **Step 1: anthropic パッケージをインストール**

```bash
pip install anthropic
```

期待出力: `Successfully installed anthropic-...`

- [ ] **Step 2: テストファイルの骨格を作成**

`tests\test_line_tasks.py` を以下の内容で作成：

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from unittest.mock import patch, MagicMock
import line_tasks
```

- [ ] **Step 3: メインスクリプトの骨格を作成**

`line_tasks.py` を以下の内容で作成：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import os
import re
import sys
from datetime import date


def parse_line_log(text: str) -> dict:
    pass


def split_into_chunks(messages: list, max_chars: int = 80000) -> list:
    pass


def extract_tasks_via_api(chunk_text: str, client) -> list:
    pass


def deduplicate_tasks(tasks: list) -> list:
    pass


def generate_html(tasks: list, meta: dict) -> str:
    pass


def main():
    pass


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: テストが実行できることを確認**

```bash
cd C:\Users\admin\.local\bin
python -m pytest tests\test_line_tasks.py -v
```

期待出力: `no tests ran` または `0 passed`（エラーなし）

---

## Task 2: LINEログパーサー

**Files:**
- Modify: `C:\Users\admin\.local\bin\line_tasks.py`
- Modify: `C:\Users\admin\.local\bin\tests\test_line_tasks.py`

LINEエクスポートの形式:
```
[LINE] "グループ名"のトーク履歴

保存日時：2026年4月26日 10:00

2026/04/20(月) 10:32	田中	こんにちは
2026/04/20(月) 10:35	課長	はい、木曜までに提出してください
2026/04/20(月) 10:40	田中	[スタンプ]
```

- [ ] **Step 1: パーサーの失敗テストを書く**

`tests\test_line_tasks.py` に追加：

```python
class TestParseLineLog(unittest.TestCase):

    SAMPLE_LOG = """[LINE] "業務グループ"のトーク履歴

保存日時：2026年4月26日 10:00

2026/04/20(月) 10:32\t田中\t見積書って今週中に出せますか？
2026/04/20(月) 10:35\t課長\tはい、木曜までに営業部へ提出してください
2026/04/20(月) 10:40\t田中\tわかりました
2026/04/20(月) 10:45\t田中\t[スタンプ]
2026/04/20(月) 11:00\t鈴木\t倉庫の在庫チェックをお願いします
"""

    def test_returns_messages_list(self):
        result = line_tasks.parse_line_log(self.SAMPLE_LOG)
        self.assertIn("messages", result)
        self.assertIsInstance(result["messages"], list)

    def test_filters_stamps(self):
        result = line_tasks.parse_line_log(self.SAMPLE_LOG)
        texts = [m["text"] for m in result["messages"]]
        self.assertNotIn("[スタンプ]", texts)

    def test_parses_sender_and_text(self):
        result = line_tasks.parse_line_log(self.SAMPLE_LOG)
        first = result["messages"][0]
        self.assertEqual(first["sender"], "田中")
        self.assertEqual(first["text"], "見積書って今週中に出せますか？")
        self.assertEqual(first["datetime"], "2026/04/20(月) 10:32")

    def test_extracts_date_range(self):
        result = line_tasks.parse_line_log(self.SAMPLE_LOG)
        self.assertEqual(result["start_date"], "2026/04/20")
        self.assertEqual(result["end_date"], "2026/04/20")

    def test_message_count(self):
        result = line_tasks.parse_line_log(self.SAMPLE_LOG)
        self.assertEqual(len(result["messages"]), 4)  # スタンプ除外後
```

- [ ] **Step 2: テストを実行して FAIL を確認**

```bash
python -m pytest tests\test_line_tasks.py::TestParseLineLog -v
```

期待出力: 全テストが FAIL または ERROR

- [ ] **Step 3: parse_line_log を実装**

`line_tasks.py` の `parse_line_log` を置き換え：

```python
NON_TEXT_PATTERNS = re.compile(
    r'^\[(スタンプ|写真|動画|ファイル|ボイスメッセージ|GIF|連絡先|位置情報)\]$'
)
MESSAGE_PATTERN = re.compile(
    r'^(\d{4}/\d{2}/\d{2}\([月火水木金土日]\) \d{2}:\d{2})\t(.+?)\t(.+)$'
)

def parse_line_log(text: str) -> dict:
    messages = []
    dates = []

    for line in text.splitlines():
        line = line.strip()
        m = MESSAGE_PATTERN.match(line)
        if not m:
            continue
        dt, sender, body = m.group(1), m.group(2), m.group(3)
        if NON_TEXT_PATTERNS.match(body.strip()):
            continue
        messages.append({"datetime": dt, "sender": sender, "text": body})
        dates.append(dt[:10])

    return {
        "messages": messages,
        "start_date": min(dates) if dates else "",
        "end_date": max(dates) if dates else "",
    }
```

- [ ] **Step 4: テストを実行して PASS を確認**

```bash
python -m pytest tests\test_line_tasks.py::TestParseLineLog -v
```

期待出力: 全5テストが PASS

- [ ] **Step 5: コミット**

```bash
git add line_tasks.py tests\test_line_tasks.py
git commit -m "feat: add LINE log parser"
```

※ gitリポジトリが未初期化の場合は先に `git init` を実行

---

## Task 3: ログ分割処理

**Files:**
- Modify: `C:\Users\admin\.local\bin\line_tasks.py`
- Modify: `C:\Users\admin\.local\bin\tests\test_line_tasks.py`

長いログをAPIの上限（80,000文字）以内に収まるように分割する。

- [ ] **Step 1: 分割処理の失敗テストを書く**

`tests\test_line_tasks.py` に追加：

```python
class TestSplitIntoChunks(unittest.TestCase):

    def _make_messages(self, n, text_len=100):
        return [
            {"datetime": "2026/04/20(月) 10:00", "sender": "田中", "text": "あ" * text_len}
            for _ in range(n)
        ]

    def test_short_log_returns_one_chunk(self):
        messages = self._make_messages(5, text_len=10)
        chunks = line_tasks.split_into_chunks(messages, max_chars=10000)
        self.assertEqual(len(chunks), 1)

    def test_long_log_splits_into_multiple_chunks(self):
        messages = self._make_messages(100, text_len=900)
        chunks = line_tasks.split_into_chunks(messages, max_chars=10000)
        self.assertGreater(len(chunks), 1)

    def test_no_messages_lost(self):
        messages = self._make_messages(50, text_len=200)
        chunks = line_tasks.split_into_chunks(messages, max_chars=5000)
        total = sum(len(c) for c in chunks)
        self.assertEqual(total, 50)
```

- [ ] **Step 2: テストを実行して FAIL を確認**

```bash
python -m pytest tests\test_line_tasks.py::TestSplitIntoChunks -v
```

期待出力: 全テストが FAIL または ERROR

- [ ] **Step 3: split_into_chunks を実装**

`line_tasks.py` の `split_into_chunks` を置き換え：

```python
def split_into_chunks(messages: list, max_chars: int = 80000) -> list:
    chunks = []
    current = []
    current_len = 0

    for msg in messages:
        line = f"{msg['datetime']}\t{msg['sender']}\t{msg['text']}\n"
        if current and current_len + len(line) > max_chars:
            chunks.append(current)
            current = []
            current_len = 0
        current.append(msg)
        current_len += len(line)

    if current:
        chunks.append(current)

    return chunks
```

- [ ] **Step 4: テストを実行して PASS を確認**

```bash
python -m pytest tests\test_line_tasks.py::TestSplitIntoChunks -v
```

期待出力: 全3テストが PASS

- [ ] **Step 5: コミット**

```bash
git add line_tasks.py tests\test_line_tasks.py
git commit -m "feat: add log chunk splitter"
```

---

## Task 4: Claude API 呼び出し

**Files:**
- Modify: `C:\Users\admin\.local\bin\line_tasks.py`
- Modify: `C:\Users\admin\.local\bin\tests\test_line_tasks.py`

- [ ] **Step 1: API呼び出しの失敗テストを書く**

`tests\test_line_tasks.py` に追加：

```python
class TestExtractTasksViaApi(unittest.TestCase):

    def _make_client_mock(self, response_text):
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=response_text)]
        mock_client.messages.create.return_value = mock_msg
        return mock_client

    def test_returns_task_list(self):
        response_json = json.dumps({
            "tasks": [{
                "content": "見積書を提出する",
                "assignee": "田中",
                "deadline": "4/28",
                "priority": "高",
                "speaker": "課長",
                "datetime": "2026/04/20(月) 10:35"
            }]
        })
        client = self._make_client_mock(response_json)
        messages = [
            {"datetime": "2026/04/20(月) 10:35", "sender": "課長",
             "text": "見積書を木曜までに提出してください"}
        ]
        result = line_tasks.extract_tasks_via_api(messages, client)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["content"], "見積書を提出する")
        self.assertEqual(result[0]["assignee"], "田中")

    def test_returns_empty_list_when_no_tasks(self):
        response_json = json.dumps({"tasks": []})
        client = self._make_client_mock(response_json)
        result = line_tasks.extract_tasks_via_api([], client)
        self.assertEqual(result, [])

    def test_handles_json_wrapped_in_markdown(self):
        response_text = '```json\n{"tasks": [{"content": "作業A", "assignee": "未定", "deadline": "未定", "priority": "中", "speaker": "田中", "datetime": "2026/04/20(月) 10:00"}]}\n```'
        client = self._make_client_mock(response_text)
        result = line_tasks.extract_tasks_via_api(
            [{"datetime": "2026/04/20(月) 10:00", "sender": "田中", "text": "作業Aをお願い"}],
            client
        )
        self.assertEqual(len(result), 1)
```

- [ ] **Step 2: テストを実行して FAIL を確認**

```bash
python -m pytest tests\test_line_tasks.py::TestExtractTasksViaApi -v
```

期待出力: 全テストが FAIL または ERROR

- [ ] **Step 3: extract_tasks_via_api を実装**

`line_tasks.py` の `extract_tasks_via_api` を置き換え：

```python
SYSTEM_PROMPT = """あなたはLINEのグループチャットを分析してタスクを抽出するアシスタントです。
会話の中からタスク・依頼・指示を抽出し、必ず以下のJSON形式のみを返してください。
余分な説明やmarkdownコードブロックは不要です。

{
  "tasks": [
    {
      "content": "タスクの内容（動詞で終わる形で）",
      "assignee": "担当者名（不明な場合は「未定」）",
      "deadline": "期限（不明な場合は「未定」）",
      "priority": "高・中・低のいずれか",
      "speaker": "指示した人の名前",
      "datetime": "発言の日時"
    }
  ]
}"""

def _messages_to_text(messages: list) -> str:
    lines = []
    for m in messages:
        lines.append(f"{m['datetime']}\t{m['sender']}\t{m['text']}")
    return "\n".join(lines)

def extract_tasks_via_api(messages: list, client) -> list:
    if not messages:
        return []

    chunk_text = _messages_to_text(messages)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"--- 会話ログ ---\n{chunk_text}"}],
    )

    raw = response.content[0].text.strip()
    # markdownコードブロックを除去
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    try:
        data = json.loads(raw)
        return data.get("tasks", [])
    except json.JSONDecodeError:
        return []
```

- [ ] **Step 4: テストを実行して PASS を確認**

```bash
python -m pytest tests\test_line_tasks.py::TestExtractTasksViaApi -v
```

期待出力: 全3テストが PASS

- [ ] **Step 5: コミット**

```bash
git add line_tasks.py tests\test_line_tasks.py
git commit -m "feat: add Claude API task extractor"
```

---

## Task 5: タスク重複排除

**Files:**
- Modify: `C:\Users\admin\.local\bin\line_tasks.py`
- Modify: `C:\Users\admin\.local\bin\tests\test_line_tasks.py`

複数チャンクから同じタスクが重複抽出された場合に除去する。

- [ ] **Step 1: 重複排除の失敗テストを書く**

`tests\test_line_tasks.py` に追加：

```python
class TestDeduplicateTasks(unittest.TestCase):

    def test_removes_exact_duplicates(self):
        task = {"content": "見積書を提出する", "assignee": "田中",
                "deadline": "4/28", "priority": "高",
                "speaker": "課長", "datetime": "2026/04/20(月) 10:35"}
        tasks = [task, task.copy()]
        result = line_tasks.deduplicate_tasks(tasks)
        self.assertEqual(len(result), 1)

    def test_keeps_different_tasks(self):
        tasks = [
            {"content": "見積書を提出する", "assignee": "田中",
             "deadline": "4/28", "priority": "高",
             "speaker": "課長", "datetime": "2026/04/20(月) 10:35"},
            {"content": "在庫チェックをする", "assignee": "鈴木",
             "deadline": "未定", "priority": "中",
             "speaker": "田中", "datetime": "2026/04/20(月) 11:00"},
        ]
        result = line_tasks.deduplicate_tasks(tasks)
        self.assertEqual(len(result), 2)

    def test_empty_list(self):
        self.assertEqual(line_tasks.deduplicate_tasks([]), [])
```

- [ ] **Step 2: テストを実行して FAIL を確認**

```bash
python -m pytest tests\test_line_tasks.py::TestDeduplicateTasks -v
```

- [ ] **Step 3: deduplicate_tasks を実装**

`line_tasks.py` の `deduplicate_tasks` を置き換え：

```python
def deduplicate_tasks(tasks: list) -> list:
    seen = set()
    result = []
    for task in tasks:
        key = task.get("content", "").strip()
        if key not in seen:
            seen.add(key)
            result.append(task)
    return result
```

- [ ] **Step 4: テストを実行して PASS を確認**

```bash
python -m pytest tests\test_line_tasks.py::TestDeduplicateTasks -v
```

期待出力: 全3テストが PASS

- [ ] **Step 5: コミット**

```bash
git add line_tasks.py tests\test_line_tasks.py
git commit -m "feat: add task deduplication"
```

---

## Task 6: HTML生成

**Files:**
- Modify: `C:\Users\admin\.local\bin\line_tasks.py`
- Modify: `C:\Users\admin\.local\bin\tests\test_line_tasks.py`

埋め込みCSS/JSを含む完全なHTMLを生成する。

- [ ] **Step 1: HTML生成の失敗テストを書く**

`tests\test_line_tasks.py` に追加：

```python
class TestGenerateHtml(unittest.TestCase):

    SAMPLE_TASKS = [
        {"content": "見積書を提出する", "assignee": "田中",
         "deadline": "4/28", "priority": "高",
         "speaker": "課長", "datetime": "2026/04/20(月) 10:35"},
        {"content": "在庫チェックをする", "assignee": "鈴木",
         "deadline": "未定", "priority": "中",
         "speaker": "田中", "datetime": "2026/04/20(月) 11:00"},
    ]
    SAMPLE_META = {
        "start_date": "2026/04/20",
        "end_date": "2026/04/20",
        "generated_at": "2026-04-26",
    }

    def test_returns_html_string(self):
        html = line_tasks.generate_html(self.SAMPLE_TASKS, self.SAMPLE_META)
        self.assertIsInstance(html, str)
        self.assertIn("<!DOCTYPE html>", html)

    def test_contains_task_content(self):
        html = line_tasks.generate_html(self.SAMPLE_TASKS, self.SAMPLE_META)
        self.assertIn("見積書を提出する", html)
        self.assertIn("在庫チェックをする", html)

    def test_contains_meta_info(self):
        html = line_tasks.generate_html(self.SAMPLE_TASKS, self.SAMPLE_META)
        self.assertIn("2026/04/20", html)
        self.assertIn("2026-04-26", html)

    def test_contains_javascript(self):
        html = line_tasks.generate_html(self.SAMPLE_TASKS, self.SAMPLE_META)
        self.assertIn("<script>", html)
        self.assertIn("localStorage", html)

    def test_priority_colors_present(self):
        html = line_tasks.generate_html(self.SAMPLE_TASKS, self.SAMPLE_META)
        self.assertIn("priority-high", html)
        self.assertIn("priority-mid", html)
```

- [ ] **Step 2: テストを実行して FAIL を確認**

```bash
python -m pytest tests\test_line_tasks.py::TestGenerateHtml -v
```

- [ ] **Step 3: generate_html を実装**

`line_tasks.py` の `generate_html` を置き換え：

```python
PRIORITY_MAP = {
    "高": ("priority-high", "高"),
    "中": ("priority-mid", "中"),
    "低": ("priority-low", "低"),
}

def _task_row_html(idx: int, task: dict) -> str:
    priority = task.get("priority", "中")
    css_class, label = PRIORITY_MAP.get(priority, ("priority-mid", priority))
    return f"""
    <tr id="row-{idx}" class="task-row active-row">
      <td>{idx}</td>
      <td class="task-content">{task.get('content', '')}</td>
      <td>{task.get('assignee', '未定')}</td>
      <td>{task.get('deadline', '未定')}</td>
      <td><span class="badge {css_class}">{label}</span></td>
      <td>
        <button class="status-btn" data-id="{idx}" onclick="cycleStatus({idx})">
          <span id="status-{idx}">未着手</span>
        </button>
      </td>
      <td>{task.get('speaker', '')}</td>
      <td>{task.get('datetime', '')}</td>
    </tr>"""

def generate_html(tasks: list, meta: dict) -> str:
    rows_html = "\n".join(_task_row_html(i + 1, t) for i, t in enumerate(tasks))
    total = len(tasks)
    assignees = sorted(set(t.get("assignee", "未定") for t in tasks))
    assignee_options = "\n".join(
        f'<option value="{a}">{a}</option>' for a in assignees
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LINEタスク一覧</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Hiragino Sans', 'Meiryo', sans-serif; background: #f5f7fa; color: #333; padding: 20px; }}
    .header {{ background: #fff; border-radius: 10px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
    .header h1 {{ font-size: 20px; color: #1a1a2e; margin-bottom: 8px; }}
    .header .meta {{ font-size: 13px; color: #888; display: flex; gap: 20px; flex-wrap: wrap; }}
    .controls {{ background: #fff; border-radius: 10px; padding: 14px 24px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }}
    .controls label {{ font-size: 13px; color: #555; }}
    .controls select {{ padding: 5px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }}
    .controls button {{ padding: 6px 16px; background: #4a90e2; color: #fff; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; }}
    .controls button:hover {{ background: #357abd; }}
    .section-title {{ font-size: 15px; font-weight: bold; color: #444; margin: 20px 0 10px; display: flex; align-items: center; gap: 8px; }}
    .table-wrap {{ background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    thead tr {{ background: #4a90e2; color: #fff; }}
    thead th {{ padding: 12px 14px; text-align: left; font-weight: 600; white-space: nowrap; }}
    tbody tr {{ border-bottom: 1px solid #f0f0f0; transition: background 0.2s; }}
    tbody tr:hover {{ background: #f9fbff; }}
    tbody td {{ padding: 10px 14px; vertical-align: middle; }}
    .priority-high {{ background: #ff4d4d; color: #fff; border-radius: 4px; padding: 2px 8px; font-size: 12px; font-weight: bold; }}
    .priority-mid  {{ background: #ffa500; color: #fff; border-radius: 4px; padding: 2px 8px; font-size: 12px; font-weight: bold; }}
    .priority-low  {{ background: #52c41a; color: #fff; border-radius: 4px; padding: 2px 8px; font-size: 12px; font-weight: bold; }}
    tr.priority-high-row {{ background: #fff0f0; }}
    tr.priority-mid-row  {{ background: #fffbe6; }}
    tr.priority-low-row  {{ background: #f0fff0; }}
    .status-btn {{ background: none; border: 1px solid #ccc; border-radius: 6px; padding: 4px 12px; font-size: 12px; cursor: pointer; transition: all 0.2s; white-space: nowrap; }}
    .status-btn.done {{ background: #52c41a; color: #fff; border-color: #52c41a; }}
    .status-btn.in-progress {{ background: #4a90e2; color: #fff; border-color: #4a90e2; }}
    .completed-section {{ margin-top: 24px; }}
    .completed-section summary {{ cursor: pointer; user-select: none; list-style: none; }}
    .completed-section summary::-webkit-details-marker {{ display: none; }}
    .completed-row td {{ color: #aaa; text-decoration: line-through; }}
    .completed-row .status-btn {{ background: #52c41a; color: #fff; border-color: #52c41a; }}
    .move-anim {{ animation: slideDown 0.3s ease; }}
    @keyframes slideDown {{ from {{ opacity: 0; transform: translateY(-10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @media print {{
      .controls {{ display: none; }}
      body {{ background: #fff; padding: 0; }}
      .table-wrap {{ box-shadow: none; }}
    }}
  </style>
</head>
<body>

<div class="header">
  <h1>📋 LINEタスク一覧</h1>
  <div class="meta">
    <span>生成日: {meta.get('generated_at', '')}</span>
    <span>会話期間: {meta.get('start_date', '')} 〜 {meta.get('end_date', '')}</span>
    <span>総タスク数: {total}件</span>
  </div>
</div>

<div class="controls">
  <label>担当者: <select id="filter-assignee" onchange="applyFilter()">
    <option value="">すべて</option>
    {assignee_options}
  </select></label>
  <label>優先度: <select id="filter-priority" onchange="applyFilter()">
    <option value="">すべて</option>
    <option value="高">高</option>
    <option value="中">中</option>
    <option value="低">低</option>
  </select></label>
  <button onclick="window.print()">🖨 印刷</button>
</div>

<div class="section-title">未完了タスク</div>
<div class="table-wrap">
  <table id="active-table">
    <thead>
      <tr>
        <th>#</th>
        <th>タスク内容</th>
        <th>担当者</th>
        <th>期限</th>
        <th>優先度</th>
        <th>進捗状況</th>
        <th>発言者</th>
        <th>発言日時</th>
      </tr>
    </thead>
    <tbody id="active-body">
      {rows_html}
    </tbody>
  </table>
</div>

<details class="completed-section" id="completed-section">
  <summary>
    <div class="section-title">✅ 完了済み <span id="done-count">(0件)</span></div>
  </summary>
  <div class="table-wrap" style="margin-top:8px">
    <table>
      <thead>
        <tr>
          <th>#</th><th>タスク内容</th><th>担当者</th><th>期限</th>
          <th>優先度</th><th>進捗状況</th><th>発言者</th><th>発言日時</th>
        </tr>
      </thead>
      <tbody id="done-body"></tbody>
    </table>
  </div>
</details>

<script>
  const STATUS_CYCLE = ['未着手', '進行中', '完了'];
  const STATUS_KEY = 'line_tasks_status_{meta.get('generated_at','')}_v1';

  function loadState() {{
    try {{ return JSON.parse(localStorage.getItem(STATUS_KEY) || '{{}}'); }}
    catch {{ return {{}}; }}
  }}

  function saveState(state) {{
    localStorage.setItem(STATUS_KEY, JSON.stringify(state));
  }}

  function cycleStatus(id) {{
    const state = loadState();
    const current = state[id] || '未着手';
    const nextIdx = (STATUS_CYCLE.indexOf(current) + 1) % STATUS_CYCLE.length;
    const next = STATUS_CYCLE[nextIdx];
    state[id] = next;
    saveState(state);
    applyStatusToRow(id, next);
  }}

  function applyStatusToRow(id, status) {{
    const row = document.getElementById('row-' + id);
    if (!row) return;
    const btn = row.querySelector('.status-btn');
    const span = document.getElementById('status-' + id);
    span.textContent = status;
    btn.className = 'status-btn' + (status === '完了' ? ' done' : status === '進行中' ? ' in-progress' : '');

    if (status === '完了') {{
      moveRowToDone(id, row);
    }} else {{
      moveRowToActive(id, row);
    }}
    updateDoneCount();
  }}

  function moveRowToDone(id, row) {{
    row.classList.add('completed-row', 'move-anim');
    row.classList.remove('active-row');
    document.getElementById('done-body').appendChild(row);
    document.getElementById('completed-section').open = true;
  }}

  function moveRowToActive(id, row) {{
    row.classList.remove('completed-row', 'move-anim');
    row.classList.add('active-row');
    document.getElementById('active-body').appendChild(row);
  }}

  function updateDoneCount() {{
    const n = document.getElementById('done-body').querySelectorAll('tr').length;
    document.getElementById('done-count').textContent = '(' + n + '件)';
  }}

  function applyFilter() {{
    const assignee = document.getElementById('filter-assignee').value;
    const priority = document.getElementById('filter-priority').value;
    document.querySelectorAll('#active-body tr, #done-body tr').forEach(row => {{
      const cells = row.querySelectorAll('td');
      if (cells.length < 5) return;
      const rowAssignee = cells[2].textContent.trim();
      const rowPriority = cells[4].textContent.trim();
      const show = (!assignee || rowAssignee === assignee) &&
                   (!priority || rowPriority === priority);
      row.style.display = show ? '' : 'none';
    }});
  }}

  // 起動時に保存済み状態を復元
  (function restoreState() {{
    const state = loadState();
    Object.entries(state).forEach(([id, status]) => applyStatusToRow(Number(id), status));
    updateDoneCount();
  }})();
</script>
</body>
</html>"""
```

- [ ] **Step 4: テストを実行して PASS を確認**

```bash
python -m pytest tests\test_line_tasks.py::TestGenerateHtml -v
```

期待出力: 全5テストが PASS

- [ ] **Step 5: コミット**

```bash
git add line_tasks.py tests\test_line_tasks.py
git commit -m "feat: add HTML generator with embedded CSS/JS"
```

---

## Task 7: CLIエントリーポイントと結合

**Files:**
- Modify: `C:\Users\admin\.local\bin\line_tasks.py`

- [ ] **Step 1: main 関数を実装**

`line_tasks.py` の `main` を置き換え：

```python
def main():
    parser = argparse.ArgumentParser(
        description="LINEのトーク履歴からタスクを抽出してHTMLを生成します"
    )
    parser.add_argument("logfile", help="LINEエクスポートの .txt ファイルパス")
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="出力HTMLファイル名（省略時: tasks_YYYYMMDD.html）"
    )
    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"エラー: ファイルが見つかりません: {args.logfile}", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("エラー: 環境変数 ANTHROPIC_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    print(f"📂 読み込み中: {args.logfile}")
    with open(args.logfile, encoding="utf-8") as f:
        raw_text = f.read()

    parsed = parse_line_log(raw_text)
    messages = parsed["messages"]
    print(f"✅ {len(messages)} 件のメッセージを解析しました")

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    chunks = split_into_chunks(messages)
    print(f"🔀 {len(chunks)} チャンクに分割してAPIに送ります")

    all_tasks = []
    for i, chunk in enumerate(chunks, 1):
        print(f"  → チャンク {i}/{len(chunks)} を処理中...")
        tasks = extract_tasks_via_api(chunk, client)
        all_tasks.extend(tasks)

    all_tasks = deduplicate_tasks(all_tasks)
    print(f"📝 {len(all_tasks)} 件のタスクを抽出しました")

    meta = {
        "start_date": parsed["start_date"],
        "end_date": parsed["end_date"],
        "generated_at": date.today().isoformat(),
    }
    html = generate_html(all_tasks, meta)

    output_path = args.output or f"tasks_{date.today().strftime('%Y%m%d')}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"🎉 完了! → {output_path}")
```

- [ ] **Step 2: サンプルログファイルを作成して動作確認**

`sample_log.txt` を作成：

```
[LINE] "テストグループ"のトーク履歴

保存日時：2026年4月26日 10:00

2026/04/20(月) 10:32	田中	見積書って今週中に出せますか？
2026/04/20(月) 10:35	課長	はい、木曜までに営業部へ提出してください
2026/04/20(月) 10:40	田中	わかりました
2026/04/20(月) 10:45	田中	[スタンプ]
2026/04/20(月) 11:00	鈴木	倉庫の在庫チェックをお願いします
2026/04/20(月) 11:05	課長	来週月曜日までにお願いします
2026/04/20(月) 11:10	鈴木	了解です
```

- [ ] **Step 3: 実際に実行してHTMLを確認**

```bash
cd C:\Users\admin\.local\bin
set ANTHROPIC_API_KEY=your_api_key_here
python line_tasks.py sample_log.txt
```

期待出力:
```
📂 読み込み中: sample_log.txt
✅ 6 件のメッセージを解析しました
🔀 1 チャンクに分割してAPIに送ります
  → チャンク 1/1 を処理中...
📝 2 件のタスクを抽出しました
🎉 完了! → tasks_20260426.html
```

- [ ] **Step 4: ブラウザで tasks_20260426.html を開いて動作確認**

確認項目:
- タスクが表に表示されている
- 優先度バッジの色が正しい（高=赤、中=オレンジ、低=緑）
- 進捗ボタンをクリックすると 未着手→進行中→完了 と切り替わる
- 「完了」にすると行が「✅ 完了済み」セクションに移動する
- ページを再読み込みしても状態が保持される（localStorage）
- 担当者・優先度フィルターが機能する
- 印刷ボタンが機能する（コントロール部分が印刷されない）

- [ ] **Step 5: 全テストを実行して PASS を確認**

```bash
python -m pytest tests\test_line_tasks.py -v
```

期待出力: 全テストが PASS

- [ ] **Step 6: コミット**

```bash
git add line_tasks.py sample_log.txt
git commit -m "feat: add CLI entry point and wire all components"
```

---

## Task 8: README 作成

**Files:**
- Create: `C:\Users\admin\.local\bin\README_line_tasks.md`

- [ ] **Step 1: README を作成**

`README_line_tasks.md` を以下の内容で作成：

```markdown
# LINE タスク抽出ツール

LINEのグループチャット履歴（.txtエクスポート）をClaude AIが分析し、タスク・依頼・指示を自動抽出してHTMLタスク表を生成します。

## セットアップ

### 1. Python インストール確認
\`\`\`bash
python --version  # 3.8以上が必要
\`\`\`

### 2. 依存パッケージをインストール
\`\`\`bash
pip install anthropic
\`\`\`

### 3. APIキーを設定
\`\`\`bash
# Windows（コマンドプロンプト）
set ANTHROPIC_API_KEY=sk-ant-...

# Windows（PowerShell）
$env:ANTHROPIC_API_KEY="sk-ant-..."
\`\`\`

## 使い方

\`\`\`bash
python line_tasks.py "トーク履歴.txt"
\`\`\`

→ `tasks_20260426.html` が生成されます。ブラウザで開いてください。

### オプション
\`\`\`bash
python line_tasks.py "トーク履歴.txt" --output 会議タスク.html
\`\`\`

## LINEのログエクスポート方法

1. LINEアプリでトーク画面を開く
2. 右上のメニュー → 「トーク履歴を送信」
3. 「テキスト形式」で保存
4. 保存した .txt ファイルを本ツールに渡す

## HTMLの使い方

| 操作 | 内容 |
|------|------|
| 進捗ボタンをクリック | 未着手→進行中→完了 と切り替わる |
| 完了にする | 「完了済み」セクションに自動移動 |
| 担当者/優先度フィルター | 絞り込み表示 |
| 印刷ボタン | 印刷用レイアウトで出力 |

状態はブラウザに自動保存されます（再読み込みしても維持）。
```

- [ ] **Step 2: コミット**

```bash
git add README_line_tasks.md
git commit -m "docs: add README for line_tasks tool"
```

---

## セルフレビュー結果

**スペックカバレッジ:**
- ✅ LINEエクスポート .txt の解析
- ✅ Claude API でタスク抽出（JSON形式）
- ✅ 長いログの自動分割
- ✅ HTML出力（タスク内容・担当者・期限・優先度・進捗・発言者・発言日時）
- ✅ 優先度色分け（高=赤、中=黄、低=緑）
- ✅ 進捗状況のクリック切り替え（localStorage永続化）
- ✅ 完了タスクの「完了済み」セクション移動（折りたたみ）
- ✅ フィルタリング（担当者・優先度）
- ✅ 印刷対応

**プレースホルダーなし:** 全ステップに実際のコードを記載済み

**型・関数名の一貫性:**
- `parse_line_log` → Task 2 定義、Task 7 使用 ✅
- `split_into_chunks` → Task 3 定義、Task 7 使用 ✅
- `extract_tasks_via_api` → Task 4 定義、Task 7 使用 ✅
- `deduplicate_tasks` → Task 5 定義、Task 7 使用 ✅
- `generate_html` → Task 6 定義、Task 7 使用 ✅
