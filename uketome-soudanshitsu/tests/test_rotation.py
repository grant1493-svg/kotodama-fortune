import random

from rotation import eligible_genres, average_likes_by_genre, counts_by_genre, pick_genre


def _entry(genre, like_count=None, status="published"):
    return {"date": "2026-08-11", "status": status, "genre": genre, "like_count": like_count}


def test_eligible_genres_excludes_last_three():
    all_genres = ["love", "work", "relationship", "money", "selfesteem"]
    history = [_entry("love"), _entry("work"), _entry("relationship")]
    assert eligible_genres(all_genres, history, gap=3) == ["money", "selfesteem"]


def test_eligible_genres_falls_back_to_all_when_everything_recent():
    all_genres = ["love", "work"]
    history = [_entry("love"), _entry("work"), _entry("love")]
    assert eligible_genres(all_genres, history, gap=3) == ["love", "work"]


def test_eligible_genres_ignores_skipped_entries():
    all_genres = ["love", "work"]
    history = [_entry("love", status="skipped")]
    assert eligible_genres(all_genres, history, gap=3) == ["love", "work"]


def test_average_likes_by_genre_ignores_none_and_unpublished():
    history = [
        _entry("love", like_count=10),
        _entry("love", like_count=20),
        _entry("love", like_count=None),
        _entry("work", like_count=5, status="skipped"),
    ]
    assert average_likes_by_genre(history) == {"love": 15.0}


def test_counts_by_genre_counts_only_published_with_like_count():
    history = [
        _entry("love", like_count=10),
        _entry("love", like_count=None),
        _entry("work", like_count=3),
    ]
    assert counts_by_genre(history) == {"love": 1, "work": 1}


def test_pick_genre_uniform_returns_one_of_eligible():
    rng = random.Random(42)
    result = pick_genre(["love", "work"], {}, specialize=False, rng=rng)
    assert result in ["love", "work"]


def test_pick_genre_raises_when_no_eligible():
    rng = random.Random(1)
    try:
        pick_genre([], {}, specialize=False, rng=rng)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_pick_genre_weighted_favors_higher_average_likes():
    rng = random.Random(7)
    avg_likes = {"love": 100.0, "work": 1.0}
    results = [pick_genre(["love", "work"], avg_likes, specialize=True, rng=rng) for _ in range(200)]
    assert results.count("love") > results.count("work") * 5
