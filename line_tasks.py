#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import os
import re
import sys
from datetime import date


NON_TEXT_PATTERNS = re.compile(
    r'^\[(スタンプ|写真|動画|ファイル|ボイスメッセージ|GIF|連絡先|位置情報)\]$'
)
MESSAGE_PATTERN = re.compile(
    r'^(\d{4}/\d{2}/\d{2}\([月火水木金土日]\) \d{2}:\d{2})\t(.+?)\t(.+)$'
)

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
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    try:
        data = json.loads(raw)
        return data.get("tasks", [])
    except json.JSONDecodeError:
        return []


def deduplicate_tasks(tasks: list) -> list:
    seen = set()
    result = []
    for task in tasks:
        key = task.get("content", "").strip()
        if key not in seen:
            seen.add(key)
            result.append(task)
    return result


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
    generated_at = meta.get('generated_at', '')
    storage_key = f"line_tasks_status_{generated_at}_v1"

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
  <h1>LINEタスク一覧</h1>
  <div class="meta">
    <span>生成日: {generated_at}</span>
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
  <button onclick="window.print()">印刷</button>
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
    <div class="section-title">完了済み <span id="done-count">(0件)</span></div>
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
  const STATUS_KEY = '{storage_key}';

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

  (function restoreState() {{
    const state = loadState();
    Object.entries(state).forEach(([id, status]) => applyStatusToRow(Number(id), status));
    updateDoneCount();
  }})();
</script>
</body>
</html>"""


def main():
    pass


if __name__ == "__main__":
    main()
