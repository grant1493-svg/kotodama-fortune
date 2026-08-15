"""うけとめ相談室 — ジャンルローテーション選定ロジック"""
import random


def eligible_genres(all_genres: list[str], history: list[dict], gap: int = 3) -> list[str]:
    published = [h for h in history if h.get("status") == "published"]
    recent = [h["genre"] for h in published[-gap:]]
    eligible = [g for g in all_genres if g not in recent]
    return eligible if eligible else list(all_genres)


def average_likes_by_genre(history: list[dict]) -> dict[str, float]:
    totals: dict[str, list[int]] = {}
    for h in history:
        if h.get("status") != "published" or h.get("like_count") is None:
            continue
        totals.setdefault(h["genre"], []).append(h["like_count"])
    return {genre: sum(values) / len(values) for genre, values in totals.items()}


def counts_by_genre(history: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for h in history:
        if h.get("status") != "published" or h.get("like_count") is None:
            continue
        counts[h["genre"]] = counts.get(h["genre"], 0) + 1
    return counts


def pick_genre(eligible: list[str], avg_likes: dict[str, float], specialize: bool, rng: random.Random) -> str:
    if not eligible:
        raise ValueError("eligible genres is empty")
    if not specialize:
        return rng.choice(eligible)
    weights = [max(avg_likes.get(g, 0.0), 0.1) for g in eligible]
    return rng.choices(eligible, weights=weights, k=1)[0]
