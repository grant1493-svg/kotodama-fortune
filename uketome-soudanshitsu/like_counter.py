"""note.comのスキ数を取得する

note.com v3 APIを使用してスキ数を取得する。
HTMLスクレイピングではなく、公開APIエンドポイント https://note.com/api/v3/notes/{key} を使用。
"""
import json
import re

import requests

_NOTE_URL_RE = re.compile(r'note\.com/[\w-]+/n/([\w-]+)/?$')


def extract_note_key(url: str) -> str | None:
    """URLからnoteのキーを抽出する。

    例: https://note.com/soudan_labo/n/ned76d2659fb1 → ned76d2659fb1
    """
    match = _NOTE_URL_RE.search(url)
    if match:
        return match.group(1)
    return None


def fetch_like_count(url: str, timeout: int = 10) -> int | None:
    """note.comのスキ数をv3 APIから取得する。

    Args:
        url: note.comの記事URL
        timeout: リクエストタイムアウト秒数

    Returns:
        スキ数（整数）、またはエラー時はNone
    """
    key = extract_note_key(url)
    if not key:
        return None

    api_url = f"https://note.com/api/v3/notes/{key}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; uketome-soudanshitsu-bot/1.0)"}

    try:
        response = requests.get(api_url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except Exception:
        return None

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError:
        return None

    try:
        like_count = data["data"]["like_count"]
        if isinstance(like_count, int):
            return like_count
    except (KeyError, TypeError):
        pass

    return None
