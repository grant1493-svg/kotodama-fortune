import hashlib
import json
from pathlib import Path

CACHE_DIR = Path(__file__).parent / ".fortune_cache"


def make_cache_key(sei: str, mei: str, date_iso: str) -> str:
    raw = f"{sei}{mei}{date_iso}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_path(key: str) -> Path:
    CACHE_DIR.mkdir(exist_ok=True)
    return CACHE_DIR / f"{key}.json"


def get_cached(key: str) -> dict | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def set_cached(key: str, data: dict) -> None:
    _cache_path(key).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
