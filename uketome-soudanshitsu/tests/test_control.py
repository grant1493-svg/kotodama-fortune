import json
from pathlib import Path

from control import is_enabled, set_enabled


def test_is_enabled_true_when_file_missing(tmp_path):
    path = tmp_path / "routine_control.json"
    assert is_enabled(path) is True


def test_is_enabled_reads_false_from_file(tmp_path):
    path = tmp_path / "routine_control.json"
    path.write_text(json.dumps({"enabled": False, "note": "検証中"}), encoding="utf-8")
    assert is_enabled(path) is False


def test_set_enabled_writes_file_with_note(tmp_path):
    path = tmp_path / "routine_control.json"
    set_enabled(path, False, note="旅行中のため停止")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {"enabled": False, "note": "旅行中のため停止"}


def test_set_enabled_round_trip(tmp_path):
    path = tmp_path / "routine_control.json"
    set_enabled(path, False, note="停止")
    assert is_enabled(path) is False
    set_enabled(path, True)
    assert is_enabled(path) is True
