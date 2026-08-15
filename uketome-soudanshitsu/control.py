"""routine_control.json の読み書きヘルパー(緊急停止スイッチ)"""
import json
from pathlib import Path


def is_enabled(path: Path) -> bool:
    if not path.exists():
        return True
    data = json.loads(path.read_text(encoding="utf-8"))
    return bool(data.get("enabled", True))


def set_enabled(path: Path, enabled: bool, note: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"enabled": enabled, "note": note}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
