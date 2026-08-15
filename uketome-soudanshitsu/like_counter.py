"""note.com公開ページからスキ数を取得する

note.comのページ構造(__NEXT_DATA__ JSON)は未検証のため、
likeCount/like_countキーを再帰探索する実装にして構造変化に耐性を持たせている。
"""
import json
import re

import requests

_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL
)
_LIKE_KEYS = {"likecount", "like_count"}


def extract_like_count(html: str) -> int | None:
    match = _NEXT_DATA_RE.search(html)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return _search_like_count(data)


def _search_like_count(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() in _LIKE_KEYS and isinstance(value, int):
                return value
        for value in node.values():
            found = _search_like_count(value)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _search_like_count(item)
            if found is not None:
                return found
    return None


def fetch_like_count(url: str, timeout: int = 10) -> int | None:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; uketome-soudanshitsu-bot/1.0)"}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except Exception:
        return None
    return extract_like_count(response.text)
