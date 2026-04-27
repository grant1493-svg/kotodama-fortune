#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import html as html_module
import json
import os
import re
import sys
from datetime import date, timedelta


NON_TEXT_PATTERNS = re.compile(
    r'^\[(スタンプ|写真|動画|ファイル|ボイスメッセージ|GIF|連絡先|位置情報)\]$'
)
# 旧形式: YYYY/MM/DD(曜日) HH:MM\t送信者\t本文
MESSAGE_PATTERN_OLD = re.compile(
    r'^(\d{4}/\d{1,2}/\d{1,2}\([月火水木金土日]\) \d{2}:\d{2})\t(.+?)\t(.+)$'
)
# 新形式: 日付行 + HH:MM\t送信者\t本文
DATE_LINE_PATTERN = re.compile(r'^(\d{4}/\d{1,2}/\d{1,2})\([月火水木金土日]\)$')
MESSAGE_PATTERN_NEW = re.compile(r'^(\d{2}:\d{2})\t(.+?)\t(.+)$')

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


def _parse_date_str(date_str: str):
    """YYYY/M/D または YYYY/MM/DD を date オブジェクトに変換"""
    try:
        parts = date_str.split("/")
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        return None


def _cutoff_date(months: int = 2) -> date:
    """今日からN ヶ月前の日付を返す"""
    today = date.today()
    # 月をまたぐ計算: 単純に60日/61日で近似せず月単位で計算
    month = today.month - months
    year = today.year
    while month <= 0:
        month += 12
        year -= 1
    try:
        return date(year, month, today.day)
    except ValueError:
        # 月末日の調整（例: 3/31 - 1ヶ月 → 2/28）
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, last_day)


def parse_line_log(text: str, max_months: int = 2) -> dict:
    messages = []
    dates = []
    current_date = ""
    cutoff = _cutoff_date(max_months)
    current_date_obj = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # 旧形式を試す
        m = MESSAGE_PATTERN_OLD.match(line)
        if m:
            dt, sender, body = m.group(1), m.group(2), m.group(3)
            date_part = dt[:10]  # YYYY/MM/DD
            d_obj = _parse_date_str(date_part)
            if d_obj and d_obj >= cutoff and not NON_TEXT_PATTERNS.match(body.strip()):
                messages.append({"datetime": dt, "sender": sender, "text": body})
                dates.append(date_part)
            continue

        # 日付行を検出（新形式）
        d = DATE_LINE_PATTERN.match(line)
        if d:
            current_date = d.group(1)
            current_date_obj = _parse_date_str(current_date)
            continue

        # 新形式のメッセージ行
        if current_date and current_date_obj and current_date_obj >= cutoff:
            m2 = MESSAGE_PATTERN_NEW.match(line)
            if m2:
                time, sender, body = m2.group(1), m2.group(2), m2.group(3)
                if not NON_TEXT_PATTERNS.match(body.strip()):
                    dt = f"{current_date} {time}"
                    messages.append({"datetime": dt, "sender": sender, "text": body})
                    dates.append(current_date)

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
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"--- 会話ログ ---\n{chunk_text}"}],
        )
    except Exception as e:
        print(f"  警告: API呼び出しに失敗しました ({e})。このチャンクをスキップします。", file=sys.stderr)
        return []

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
    e = html_module.escape
    return f"""
    <tr id="row-{idx}" class="task-row active-row">
      <td>{idx}</td>
      <td class="task-content">{e(task.get('content', ''))}</td>
      <td>{e(task.get('assignee', '未定'))}</td>
      <td>{e(task.get('deadline', '未定'))}</td>
      <td><span class="badge {css_class}">{label}</span></td>
      <td>
        <button class="status-btn" data-id="{idx}" onclick="cycleStatus({idx})">
          <span id="status-{idx}">未着手</span>
        </button>
      </td>
      <td>{e(task.get('speaker', ''))}</td>
      <td>{e(task.get('datetime', ''))}</td>
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
    parser = argparse.ArgumentParser(
        description="LINEのトーク履歴からタスクを抽出してHTMLを生成します"
    )
    parser.add_argument("logfile", help="LINEエクスポートの .txt ファイルパス")
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="出力HTMLファイル名（省略時: tasks_YYYYMMDD.html）"
    )
    parser.add_argument(
        "--months", "-m",
        type=int,
        default=2,
        help="直近何ヶ月分を対象にするか（デフォルト: 2）"
    )
    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"エラー: ファイルが見つかりません: {args.logfile}", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("エラー: 環境変数 ANTHROPIC_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    print(f"読み込み中: {args.logfile}")
    with open(args.logfile, encoding="utf-8") as f:
        raw_text = f.read()

    parsed = parse_line_log(raw_text, max_months=args.months)
    messages = parsed["messages"]
    print(f"{len(messages)} 件のメッセージを解析しました（直近{args.months}ヶ月分）")

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    chunks = split_into_chunks(messages)
    print(f"{len(chunks)} チャンクに分割してAPIに送ります")

    all_tasks = []
    for i, chunk in enumerate(chunks, 1):
        print(f"  チャンク {i}/{len(chunks)} を処理中...")
        tasks = extract_tasks_via_api(chunk, client)
        all_tasks.extend(tasks)

    all_tasks = deduplicate_tasks(all_tasks)
    print(f"{len(all_tasks)} 件のタスクを抽出しました")

    meta = {
        "start_date": parsed["start_date"],
        "end_date": parsed["end_date"],
        "generated_at": date.today().isoformat(),
    }
    html = generate_html(all_tasks, meta)

    output_path = args.output or f"tasks_{date.today().strftime('%Y%m%d')}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"完了! → {output_path}")


if __name__ == "__main__":
    main()
