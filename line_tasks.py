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


def generate_html(tasks: list, meta: dict) -> str:
    pass


def main():
    pass


if __name__ == "__main__":
    main()
