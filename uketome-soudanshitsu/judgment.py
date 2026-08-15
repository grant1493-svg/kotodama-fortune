"""うけとめ相談室 — 特化判定基準の評価と自己調整"""
from datetime import datetime


def phase_ready(published_count: int, first_date: str | None, today: str, policy: dict) -> bool:
    if published_count >= policy["min_articles_before_check"]:
        return True
    if first_date is None:
        return False
    days = (datetime.fromisoformat(today) - datetime.fromisoformat(first_date)).days
    return days >= policy["min_days_before_check"]


def should_specialize(avg_likes: dict[str, float], counts: dict[str, int], policy: dict) -> bool:
    if len(avg_likes) < 2:
        return False
    ranked = sorted(avg_likes.items(), key=lambda kv: kv[1], reverse=True)
    top_genre, top_avg = ranked[0]
    if counts.get(top_genre, 0) < policy["min_data_points"]:
        return False
    rest_avgs = [value for _, value in ranked[1:]]
    rest_avg = sum(rest_avgs) / len(rest_avgs)
    if rest_avg == 0:
        return top_avg > 0
    return (top_avg / rest_avg) >= policy["specialization_ratio_threshold"]


def clamp(value: float, bounds: tuple[float, float]) -> float:
    lo, hi = bounds
    return max(lo, min(hi, value))


def adjust_ratio_threshold(policy: dict, outcome_held: bool, step: float = 0.1) -> float:
    current = policy["specialization_ratio_threshold"]
    new_value = current - step if outcome_held else current + step
    bounds = tuple(policy["bounds"]["ratio_threshold"])
    return round(clamp(new_value, bounds), 2)


def articles_since(history: list[dict], since_date: str) -> int:
    return sum(
        1 for h in history if h.get("status") == "published" and h.get("date", "") > since_date
    )


def due_for_outcome_review(review_history: list[dict], history: list[dict], lag: int = 10) -> list[dict]:
    due = []
    for entry in review_history:
        if entry.get("outcome"):
            continue
        if articles_since(history, entry["date"]) >= lag:
            due.append(entry)
    return due
