import json
from pathlib import Path

from history_store import load_history, save_history, append_entry, already_recorded_today


def test_load_history_returns_empty_list_when_file_missing(tmp_path):
    path = tmp_path / "publish_history.json"
    assert load_history(path) == []


def test_load_history_reads_existing_json(tmp_path):
    path = tmp_path / "publish_history.json"
    path.write_text(json.dumps([{"date": "2026-08-09", "genre": "love"}]), encoding="utf-8")
    result = load_history(path)
    assert result == [{"date": "2026-08-09", "genre": "love"}]


def test_save_history_writes_readable_json(tmp_path):
    path = tmp_path / "publish_history.json"
    save_history(path, [{"date": "2026-08-11", "genre": "work"}])
    assert json.loads(path.read_text(encoding="utf-8")) == [{"date": "2026-08-11", "genre": "work"}]


def test_append_entry_adds_to_existing_history(tmp_path):
    path = tmp_path / "publish_history.json"
    save_history(path, [{"date": "2026-08-09", "genre": "love"}])
    result = append_entry(path, {"date": "2026-08-11", "genre": "work"})
    assert len(result) == 2
    assert json.loads(path.read_text(encoding="utf-8"))[-1]["genre"] == "work"


def test_already_recorded_today_true_when_date_present():
    history = [{"date": "2026-08-11", "genre": "love"}]
    assert already_recorded_today(history, "2026-08-11") is True


def test_already_recorded_today_false_when_date_absent():
    history = [{"date": "2026-08-10", "genre": "love"}]
    assert already_recorded_today(history, "2026-08-11") is False
