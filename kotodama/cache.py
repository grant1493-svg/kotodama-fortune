"""
In-memory cache with TTL (replaces file-based cache).

Render free tier uses an ephemeral filesystem — files written to disk are
lost on every dyno restart (which happens on inactivity).  Keeping the cache
in process memory guarantees that repeated requests for the same name on the
same day avoid redundant Claude API calls within a single dyno lifetime.

TTL defaults to 24 hours so stale entries are eventually evicted even when
the dyno runs continuously.
"""
import hashlib
import threading
import time
from typing import Optional

_LOCK = threading.Lock()

# {key: (value, expire_at)}
_FORTUNE_CACHE: dict[str, tuple[dict, float]] = {}
_IMAGE_CACHE:   dict[str, tuple[bytes, float]] = {}

DEFAULT_TTL = 60 * 60 * 24  # 24 hours


def make_cache_key(sei: str, mei: str, date_iso: str) -> str:
    raw = f"{sei}{mei}{date_iso}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_cached(key: str) -> Optional[dict]:
    with _LOCK:
        entry = _FORTUNE_CACHE.get(key)
        if entry is None:
            return None
        value, expire_at = entry
        if time.time() > expire_at:
            del _FORTUNE_CACHE[key]
            return None
        return value


def set_cached(key: str, data: dict, ttl: int = DEFAULT_TTL) -> None:
    with _LOCK:
        _FORTUNE_CACHE[key] = (data, time.time() + ttl)


def get_cached_image(key: str) -> Optional[bytes]:
    with _LOCK:
        entry = _IMAGE_CACHE.get(key)
        if entry is None:
            return None
        value, expire_at = entry
        if time.time() > expire_at:
            del _IMAGE_CACHE[key]
            return None
        return value


def set_cached_image(key: str, data: bytes, ttl: int = DEFAULT_TTL) -> None:
    with _LOCK:
        _IMAGE_CACHE[key] = (data, time.time() + ttl)
