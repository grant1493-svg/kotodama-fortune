from judgment import (
    phase_ready,
    should_specialize,
    clamp,
    adjust_ratio_threshold,
    articles_since,
    due_for_outcome_review,
)

POLICY = {
    "min_articles_before_check": 20,
    "min_days_before_check": 30,
    "specialization_ratio_threshold": 1.5,
    "min_data_points": 3,
    "bounds": {"ratio_threshold": [1.2, 2.0], "min_articles": [10, 40]},
}


def test_phase_ready_true_when_count_reached():
    assert phase_ready(20, None, "2026-08-11", POLICY) is True


def test_phase_ready_true_when_days_reached():
    assert phase_ready(5, "2026-07-01", "2026-08-11", POLICY) is True


def test_phase_ready_false_when_neither_reached():
    assert phase_ready(5, "2026-08-01", "2026-08-11", POLICY) is False


def test_should_specialize_true_when_ratio_and_data_points_met():
    avg_likes = {"love": 30.0, "work": 10.0, "money": 8.0}
    counts = {"love": 5, "work": 5, "money": 5}
    assert should_specialize(avg_likes, counts, POLICY) is True


def test_should_specialize_false_when_top_lacks_data_points():
    avg_likes = {"love": 30.0, "work": 10.0}
    counts = {"love": 2, "work": 10}
    assert should_specialize(avg_likes, counts, POLICY) is False


def test_should_specialize_false_when_ratio_below_threshold():
    avg_likes = {"love": 12.0, "work": 10.0}
    counts = {"love": 5, "work": 5}
    assert should_specialize(avg_likes, counts, POLICY) is False


def test_should_specialize_false_with_single_genre():
    assert should_specialize({"love": 30.0}, {"love": 5}, POLICY) is False


def test_clamp_stays_within_bounds():
    assert clamp(1.6, (1.2, 2.0)) == 1.6


def test_clamp_caps_at_upper_bound():
    assert clamp(2.5, (1.2, 2.0)) == 2.0


def test_clamp_caps_at_lower_bound():
    assert clamp(0.5, (1.2, 2.0)) == 1.2


def test_adjust_ratio_threshold_decreases_when_decision_held():
    new_value = adjust_ratio_threshold(POLICY, outcome_held=True, step=0.1)
    assert new_value == 1.4


def test_adjust_ratio_threshold_increases_when_decision_reversed():
    new_value = adjust_ratio_threshold(POLICY, outcome_held=False, step=0.1)
    assert new_value == 1.6


def test_adjust_ratio_threshold_respects_lower_bound():
    policy = dict(POLICY, specialization_ratio_threshold=1.25)
    new_value = adjust_ratio_threshold(policy, outcome_held=True, step=0.1)
    assert new_value == 1.2


def test_articles_since_counts_only_published_after_date():
    history = [
        {"date": "2026-08-01", "status": "published"},
        {"date": "2026-08-05", "status": "published"},
        {"date": "2026-08-06", "status": "skipped"},
    ]
    assert articles_since(history, "2026-08-01") == 1


def test_due_for_outcome_review_returns_entries_past_lag():
    review_history = [{"date": "2026-08-01", "decision": "specialize_love"}]
    history = [{"date": f"2026-08-{d:02d}", "status": "published"} for d in range(2, 13)]
    due = due_for_outcome_review(review_history, history, lag=10)
    assert due == review_history


def test_due_for_outcome_review_skips_entries_with_outcome():
    review_history = [{"date": "2026-08-01", "decision": "specialize_love", "outcome": "維持"}]
    history = [{"date": f"2026-08-{d:02d}", "status": "published"} for d in range(2, 13)]
    assert due_for_outcome_review(review_history, history, lag=10) == []
