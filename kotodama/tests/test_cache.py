import time

import pytest

import cache
from cache import (
    get_cached,
    get_cached_image,
    make_cache_key,
    set_cached,
    set_cached_image,
)


@pytest.fixture(autouse=True)
def clean_cache():
    """cache.py is an in-memory TTL cache (see module docstring: Render's free
    tier has an ephemeral filesystem, so the old file-based cache was replaced).
    Clear the module-level dicts between tests so keys don't leak across tests."""
    cache._FORTUNE_CACHE.clear()
    cache._IMAGE_CACHE.clear()
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


def test_cached_entry_expires_after_ttl():
    set_cached("expiring-key", {"score": 5}, ttl=0)
    time.sleep(0.01)
    assert get_cached("expiring-key") is None


def test_get_cached_image_miss_returns_none():
    assert get_cached_image("no-such-key") is None


def test_set_and_get_cached_image():
    png_bytes = b"\x89PNG\r\n\x1a\nfake"
    set_cached_image("img-key", png_bytes)
    result = get_cached_image("img-key")
    assert result == png_bytes


def test_cached_image_expires_after_ttl():
    set_cached_image("expiring-img", b"PNGDATA", ttl=0)
    time.sleep(0.01)
    assert get_cached_image("expiring-img") is None
