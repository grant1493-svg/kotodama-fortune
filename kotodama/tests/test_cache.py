import json
from pathlib import Path
import pytest
from cache import make_cache_key, get_cached, set_cached


@pytest.fixture(autouse=True)
def clean_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("cache.CACHE_DIR", tmp_path)
    yield


def test_make_cache_key_is_deterministic():
    k1 = make_cache_key("田中", "花", "2026-05-05")
    k2 = make_cache_key("田中", "花", "2026-05-05")
    assert k1 == k2


def test_make_cache_key_different_dates():
    k1 = make_cache_key("田中", "花", "2026-05-05")
    k2 = make_cache_key("田中", "花", "2026-05-06")
    assert k1 != k2


def test_get_cached_miss_returns_none():
    assert get_cached("nonexistent-key") is None


def test_set_and_get_cached():
    data = {"today_message": "今日も良い日です"}
    set_cached("test-key", data)
    result = get_cached("test-key")
    assert result == data


def test_cache_persists_as_json(tmp_path, monkeypatch):
    monkeypatch.setattr("cache.CACHE_DIR", tmp_path)
    set_cached("my-key", {"score": 5})
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    saved = json.loads(files[0].read_text(encoding="utf-8"))
    assert saved["score"] == 5
