"""publish_history.json の読み書きヘルパー"""
import json
from pathlib import Path


def load_history(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_history(path: Path, history: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def append_entry(path: Path, entry: dict) -> list[dict]:
    history = load_history(path)
    history.append(entry)
    save_history(path, history)
    return history


def already_recorded_today(history: list[dict], today: str) -> bool:
    return any(h.get("date") == today for h in history)
