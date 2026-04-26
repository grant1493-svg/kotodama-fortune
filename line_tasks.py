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
