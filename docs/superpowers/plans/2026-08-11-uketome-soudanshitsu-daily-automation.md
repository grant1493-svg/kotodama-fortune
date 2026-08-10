# うけとめ相談室 日次自動投稿ルーティン Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** うけとめ相談室（note.com「うけとめ相談室」記事シリーズ）を、ジャンル選定・執筆品質・特化判定基準の3つの学習ループ付きで毎日1本、完全自動生成・投稿するパイプラインを実装する。

**Architecture:** 決定論的なロジック（ローテーション判定・特化判定・自己調整・画像合成・スキ数取得）はテスト可能なPythonモジュールとして実装する。ジャンル企画・執筆・編集チェック・実績分析はLLM判断が必要なため4つの新規サブエージェントとして実装する。両者を`daily_routine.md`というプレイブックが束ね、`/schedule`で毎日起動する。

**Tech Stack:** Python 3 / Pillow / requests / pytest / Claude Code サブエージェント / claude-in-chrome（note.com操作）/ `/schedule`（cron起動）

**参照設計書:** `docs/superpowers/specs/2026-08-11-uketome-soudanshitsu-daily-automation-design.md`

## Global Constraints

- サムネイル最終出力サイズは 1280×670px（既存のad-designer生成物・アップロード済み5記事と統一）
- ジャンルローテーションは直近3投稿で使用したジャンルを除外する（gap=3）
- チューニング可能なパラメータ（しきい値・ジャンル一覧・投稿時刻等）はすべてJSONファイルで管理し、コード変更なしで変更可能にする
- オーケストレーターは実行冒頭で必ず`routine_control.json`の`enabled`を確認し、`false`なら何もせず終了する
- 編集チェックのNG再修正は最大2回まで、2回ともNGなら当日はスキップする
- 毎日の実行結果（成功/スキップ問わず）はPush通知で要約する
- `uketome-soudanshitsu/.env`は`.gitignore`の`*.env`で除外済み。コミット時に絶対に含めない
- 既存の`articles_config.py` / `generate_thumbnail.py` / `x_post.py`は変更しない（既存動作を壊さない）
- テストは `uketome-soudanshitsu/tests/` に配置し、`tests/__init__.py`を置いてpytestのrootdir挿入で`from module import ...`のベアインポートを可能にする（`kotodama/tests/`と同じ規約）

---

## ファイル構成（新規作成分）

```
uketome-soudanshitsu/
  ├─ history_store.py             # publish_history.jsonの読み書き
  ├─ control.py                   # routine_control.jsonの読み書き（停止スイッチ）
  ├─ rotation.py                  # ジャンル選定ロジック
  ├─ judgment.py                  # 特化判定・自己調整ロジック
  ├─ like_counter.py              # note.com公開ページからスキ数取得
  ├─ generate_logo_overlay.py     # ロゴ/キャッチコピー透過PNG生成
  ├─ compose_thumbnail.py         # 背景+ロゴ+見出しの合成
  ├─ daily_routine.md             # 日次オーケストレーターのプレイブック
  ├─ routine_control.json         # 初期データ
  ├─ judgment_policy.json         # 初期データ
  ├─ genre_candidates.json        # 初期データ
  ├─ qa_feedback_log.json         # 初期データ
  ├─ publish_history.json         # 初期データ（既存5記事をバックフィル）
  ├─ articles/                    # 生成記事本文の保存先（.gitkeepのみ）
  ├─ static/
  │    └─ logo_overlay.png        # generate_logo_overlay.pyの出力
  └─ tests/
       ├─ __init__.py
       ├─ test_history_store.py
       ├─ test_control.py
       ├─ test_rotation.py
       ├─ test_judgment.py
       ├─ test_like_counter.py
       ├─ test_generate_logo_overlay.py
       ├─ test_compose_thumbnail.py
       └─ test_agent_definitions.py

C:\Users\admin\.claude\agents\   ← リポジトリ外（グローバル設定、git管理対象外）
  ├─ performance-analyst-soudan.md
  ├─ concept-planner-soudan.md
  ├─ writer-soudan.md
  └─ qa-reviewer-soudan.md
```

---

### Task 1: 状態管理ファイルの初期データ + history_store.py

**Files:**
- Create: `uketome-soudanshitsu/publish_history.json`
- Create: `uketome-soudanshitsu/routine_control.json`
- Create: `uketome-soudanshitsu/judgment_policy.json`
- Create: `uketome-soudanshitsu/genre_candidates.json`
- Create: `uketome-soudanshitsu/qa_feedback_log.json`
- Create: `uketome-soudanshitsu/history_store.py`
- Test: `uketome-soudanshitsu/tests/__init__.py`
- Test: `uketome-soudanshitsu/tests/test_history_store.py`

**Interfaces:**
- Produces: `load_history(path: Path) -> list[dict]`, `save_history(path: Path, history: list[dict]) -> None`, `append_entry(path: Path, entry: dict) -> list[dict]`, `already_recorded_today(history: list[dict], today: str) -> bool`

- [ ] **Step 1: 初期JSONファイルを作成する**

`uketome-soudanshitsu/publish_history.json`（既存5記事を`status: "published"`, `like_count: null`でバックフィル。実際のスキ数はTask 5実装後の初回実行時に取得・更新する）:

```json
[
  { "date": "2026-08-09", "status": "published", "genre": "love", "angle": "初回投稿(既存記事)", "note_url": "https://note.com/soudan_labo/n/ned76d2659fb1", "like_count": null, "like_count_checked_at": null, "qa_retry_count": 0 },
  { "date": "2026-08-09", "status": "published", "genre": "work", "angle": "初回投稿(既存記事)", "note_url": "https://note.com/soudan_labo/n/n0d0899ffd973", "like_count": null, "like_count_checked_at": null, "qa_retry_count": 0 },
  { "date": "2026-08-09", "status": "published", "genre": "relationship", "angle": "初回投稿(既存記事)", "note_url": "https://note.com/soudan_labo/n/n8c8fcc6b9de5", "like_count": null, "like_count_checked_at": null, "qa_retry_count": 0 },
  { "date": "2026-08-09", "status": "published", "genre": "money", "angle": "初回投稿(既存記事)", "note_url": "https://note.com/soudan_labo/n/n787ebd1723a3", "like_count": null, "like_count_checked_at": null, "qa_retry_count": 0 },
  { "date": "2026-08-09", "status": "published", "genre": "selfesteem", "angle": "初回投稿(既存記事)", "note_url": "https://note.com/soudan_labo/n/n51cd8a6629bc", "like_count": null, "like_count_checked_at": null, "qa_retry_count": 0 }
]
```

`uketome-soudanshitsu/routine_control.json`:

```json
{ "enabled": true, "note": "" }
```

`uketome-soudanshitsu/judgment_policy.json`:

```json
{
  "min_articles_before_check": 20,
  "min_days_before_check": 30,
  "specialization_ratio_threshold": 1.5,
  "min_data_points": 3,
  "bounds": {
    "ratio_threshold": [1.2, 2.0],
    "min_articles": [10, 40]
  },
  "review_history": []
}
```

`uketome-soudanshitsu/genre_candidates.json`（既存5ジャンルを`active`として登録）:

```json
[
  { "key": "love", "name": "恋愛の悩み", "status": "active", "discovered_date": "2026-08-09" },
  { "key": "work", "name": "仕事の悩み", "status": "active", "discovered_date": "2026-08-09" },
  { "key": "relationship", "name": "人間関係の悩み", "status": "active", "discovered_date": "2026-08-09" },
  { "key": "money", "name": "お金の悩み", "status": "active", "discovered_date": "2026-08-09" },
  { "key": "selfesteem", "name": "自己肯定感の悩み", "status": "active", "discovered_date": "2026-08-09" }
]
```

`uketome-soudanshitsu/qa_feedback_log.json`:

```json
[]
```

- [ ] **Step 2: `tests/__init__.py`を空ファイルで作成する**

`kotodama/tests/__init__.py`と同じ規約。中身は空でよい。

- [ ] **Step 3: 失敗するテストを書く**

`uketome-soudanshitsu/tests/test_history_store.py`:

```python
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
```

- [ ] **Step 4: テストを実行して失敗を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_history_store.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'history_store'`

- [ ] **Step 5: `history_store.py`を実装する**

```python
"""publish_history.json の読み書きヘルパー"""
import json
from pathlib import Path


def load_history(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_history(path: Path, history: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def append_entry(path: Path, entry: dict) -> list[dict]:
    history = load_history(path)
    history.append(entry)
    save_history(path, history)
    return history


def already_recorded_today(history: list[dict], today: str) -> bool:
    return any(h.get("date") == today for h in history)
```

- [ ] **Step 6: テストを実行して成功を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_history_store.py -v`
Expected: 6 passed

- [ ] **Step 7: コミット**

```bash
git add uketome-soudanshitsu/publish_history.json uketome-soudanshitsu/routine_control.json uketome-soudanshitsu/judgment_policy.json uketome-soudanshitsu/genre_candidates.json uketome-soudanshitsu/qa_feedback_log.json uketome-soudanshitsu/history_store.py uketome-soudanshitsu/tests/__init__.py uketome-soudanshitsu/tests/test_history_store.py
git commit -m "うけとめ相談室: 状態管理ファイルの初期データとhistory_store.pyを追加"
```

---

### Task 2: control.py（一時停止スイッチ）

**Files:**
- Create: `uketome-soudanshitsu/control.py`
- Test: `uketome-soudanshitsu/tests/test_control.py`

**Interfaces:**
- Produces: `is_enabled(path: Path) -> bool`, `set_enabled(path: Path, enabled: bool, note: str = "") -> None`

- [ ] **Step 1: 失敗するテストを書く**

```python
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
```

- [ ] **Step 2: テストを実行して失敗を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_control.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'control'`

- [ ] **Step 3: `control.py`を実装する**

```python
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
```

- [ ] **Step 4: テストを実行して成功を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_control.py -v`
Expected: 4 passed

- [ ] **Step 5: コミット**

```bash
git add uketome-soudanshitsu/control.py uketome-soudanshitsu/tests/test_control.py
git commit -m "うけとめ相談室: 緊急停止スイッチcontrol.pyを追加"
```

---

### Task 3: rotation.py（ジャンル選定ロジック）

**Files:**
- Create: `uketome-soudanshitsu/rotation.py`
- Test: `uketome-soudanshitsu/tests/test_rotation.py`

**Interfaces:**
- Consumes: `history: list[dict]`（Task 1の`publish_history.json`形式、各要素は`date`, `status`, `genre`, `like_count`キーを持つ）
- Produces: `eligible_genres(all_genres: list[str], history: list[dict], gap: int = 3) -> list[str]`, `average_likes_by_genre(history: list[dict]) -> dict[str, float]`, `counts_by_genre(history: list[dict]) -> dict[str, int]`, `pick_genre(eligible: list[str], avg_likes: dict[str, float], specialize: bool, rng: random.Random) -> str`

- [ ] **Step 1: 失敗するテストを書く**

```python
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
```

- [ ] **Step 2: テストを実行して失敗を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_rotation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'rotation'`

- [ ] **Step 3: `rotation.py`を実装する**

```python
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
```

- [ ] **Step 4: テストを実行して成功を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_rotation.py -v`
Expected: 8 passed

- [ ] **Step 5: コミット**

```bash
git add uketome-soudanshitsu/rotation.py uketome-soudanshitsu/tests/test_rotation.py
git commit -m "うけとめ相談室: ジャンルローテーション選定ロジックrotation.pyを追加"
```

---

### Task 4: judgment.py（特化判定・自己調整ロジック）

**Files:**
- Create: `uketome-soudanshitsu/judgment.py`
- Test: `uketome-soudanshitsu/tests/test_judgment.py`

**Interfaces:**
- Consumes: `rotation.average_likes_by_genre`と`rotation.counts_by_genre`の戻り値、Task 1の`judgment_policy.json`形式
- Produces: `phase_ready(published_count: int, first_date: str | None, today: str, policy: dict) -> bool`, `should_specialize(avg_likes: dict[str, float], counts: dict[str, int], policy: dict) -> bool`, `clamp(value: float, bounds: tuple[float, float]) -> float`, `adjust_ratio_threshold(policy: dict, outcome_held: bool, step: float = 0.1) -> float`, `articles_since(history: list[dict], since_date: str) -> int`, `due_for_outcome_review(review_history: list[dict], history: list[dict], lag: int = 10) -> list[dict]`

- [ ] **Step 1: 失敗するテストを書く**

```python
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
```

- [ ] **Step 2: テストを実行して失敗を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_judgment.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'judgment'`

- [ ] **Step 3: `judgment.py`を実装する**

```python
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
```

- [ ] **Step 4: テストを実行して成功を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_judgment.py -v`
Expected: 16 passed

- [ ] **Step 5: コミット**

```bash
git add uketome-soudanshitsu/judgment.py uketome-soudanshitsu/tests/test_judgment.py
git commit -m "うけとめ相談室: 特化判定・自己調整ロジックjudgment.pyを追加"
```

---

### Task 5: like_counter.py（note.comのスキ数取得）

**Files:**
- Create: `uketome-soudanshitsu/like_counter.py`
- Test: `uketome-soudanshitsu/tests/test_like_counter.py`

**Interfaces:**
- Produces: `extract_like_count(html: str) -> int | None`, `fetch_like_count(url: str, timeout: int = 10) -> int | None`

**注意（既知の未検証リスク）:** note.comのページ内`__NEXT_DATA__`のJSON構造は未確認。`likeCount`/`like_count`キーを再帰探索する実装にして構造変化に強くしているが、Step 6で実URLに対して手動検証すること。もし見つからない場合はブラウザのDevToolsで実際のキー名を確認し、`_LIKE_KEYS`に追加する。

- [ ] **Step 1: 失敗するテストを書く**

```python
import json
from unittest.mock import patch, MagicMock

from like_counter import extract_like_count, fetch_like_count


def _html_with_next_data(payload: dict) -> str:
    return (
        "<html><body>"
        f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script>'
        "</body></html>"
    )


def test_extract_like_count_finds_top_level_key():
    html = _html_with_next_data({"props": {"pageProps": {"likeCount": 42}}})
    assert extract_like_count(html) == 42


def test_extract_like_count_finds_snake_case_key():
    html = _html_with_next_data({"data": {"article": {"like_count": 7}}})
    assert extract_like_count(html) == 7


def test_extract_like_count_returns_none_when_no_next_data():
    assert extract_like_count("<html><body>no data here</body></html>") is None


def test_extract_like_count_returns_none_on_invalid_json():
    html = '<script id="__NEXT_DATA__" type="application/json">{not valid json}</script>'
    assert extract_like_count(html) is None


def test_extract_like_count_returns_none_when_key_absent():
    html = _html_with_next_data({"props": {"pageProps": {"title": "記事タイトル"}}})
    assert extract_like_count(html) is None


def test_fetch_like_count_returns_none_on_network_error():
    with patch("like_counter.requests.get", side_effect=Exception("network down")):
        assert fetch_like_count("https://note.com/soudan_labo/n/xxxx") is None


def test_fetch_like_count_parses_successful_response():
    html = _html_with_next_data({"likeCount": 15})
    mock_response = MagicMock()
    mock_response.text = html
    mock_response.raise_for_status = MagicMock()
    with patch("like_counter.requests.get", return_value=mock_response):
        assert fetch_like_count("https://note.com/soudan_labo/n/xxxx") == 15
```

- [ ] **Step 2: テストを実行して失敗を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_like_counter.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'like_counter'`

- [ ] **Step 3: `like_counter.py`を実装する**

```python
"""note.com公開ページからスキ数を取得する

note.comのページ構造(__NEXT_DATA__ JSON)は未検証のため、
likeCount/like_countキーを再帰探索する実装にして構造変化に耐性を持たせている。
"""
import json
import re

import requests

_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL
)
_LIKE_KEYS = {"likecount", "like_count"}


def extract_like_count(html: str) -> int | None:
    match = _NEXT_DATA_RE.search(html)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return _search_like_count(data)


def _search_like_count(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() in _LIKE_KEYS and isinstance(value, int):
                return value
        for value in node.values():
            found = _search_like_count(value)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _search_like_count(item)
            if found is not None:
                return found
    return None


def fetch_like_count(url: str, timeout: int = 10) -> int | None:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; uketome-soudanshitsu-bot/1.0)"}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except Exception:
        return None
    return extract_like_count(response.text)
```

- [ ] **Step 4: テストを実行して成功を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_like_counter.py -v`
Expected: 7 passed

- [ ] **Step 5: コミット**

```bash
git add uketome-soudanshitsu/like_counter.py uketome-soudanshitsu/tests/test_like_counter.py
git commit -m "うけとめ相談室: note.comスキ数取得like_counter.pyを追加"
```

- [ ] **Step 6: 実URLで手動検証する（重要）**

```bash
cd uketome-soudanshitsu && python -c "from like_counter import fetch_like_count; print(fetch_like_count('https://note.com/soudan_labo/n/ned76d2659fb1'))"
```

- 整数が返れば成功。`None`が返る場合は、ブラウザでこのURLを開きDevTools > Elements で`__NEXT_DATA__`のJSONを検索し、実際のスキ数を保持しているキー名を確認して`_LIKE_KEYS`に追加する
- この手動検証はコミット不要（コードは既に正しい設計になっているため、必要ならキー名追加の1行修正のみ行い、修正した場合のみ追加コミットする）

---

### Task 6: generate_logo_overlay.py（ロゴ/キャッチコピーの独立管理）

**Files:**
- Create: `uketome-soudanshitsu/generate_logo_overlay.py`
- Test: `uketome-soudanshitsu/tests/test_generate_logo_overlay.py`

**Interfaces:**
- Consumes: `generate_thumbnail._ensure_font() -> Path`（既存関数を再利用、フォントダウンロードロジックの重複を避ける）
- Produces: `generate_logo_overlay(output_path: Path) -> Path`

- [ ] **Step 1: 失敗するテストを書く**

```python
from pathlib import Path

import pytest
from PIL import Image

from generate_thumbnail import FONT_PATH

requires_font = pytest.mark.skipif(
    not FONT_PATH.exists(),
    reason="Font not present — run: cd uketome-soudanshitsu && python -c \"from generate_thumbnail import _ensure_font; _ensure_font()\"",
)


@requires_font
def test_generate_logo_overlay_creates_rgba_png_with_correct_size(tmp_path):
    from generate_logo_overlay import generate_logo_overlay

    output_path = tmp_path / "logo_overlay.png"
    generate_logo_overlay(output_path)
    img = Image.open(output_path)
    assert img.format == "PNG"
    assert img.mode == "RGBA"
    assert img.size == (1280, 670)


@requires_font
def test_generate_logo_overlay_top_right_corner_is_transparent(tmp_path):
    from generate_logo_overlay import generate_logo_overlay

    output_path = tmp_path / "logo_overlay.png"
    generate_logo_overlay(output_path)
    img = Image.open(output_path)
    r, g, b, a = img.getpixel((10, 10))
    assert a == 0
```

- [ ] **Step 2: テストを実行して失敗を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_generate_logo_overlay.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'generate_logo_overlay'`

- [ ] **Step 3: `generate_logo_overlay.py`を実装する**

```python
"""うけとめ相談室 — ロゴ/キャッチコピーの透過オーバーレイ生成

背景写真や記事見出しとは独立して管理する。ブランド表記を変えたいときは
このスクリプトの再実行だけで済み、背景写真の再生成は不要。
使い方: python generate_logo_overlay.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from generate_thumbnail import _ensure_font

WIDTH, HEIGHT = 1280, 670
_BRAND = "うけとめ相談室"
_CATCHPHRASE = "精神科医×心理学者×脳科学者"
_PANEL = (20, 20, 30, 160)
_WHITE = (255, 255, 255, 255)


def generate_logo_overlay(output_path: Path) -> Path:
    font_path = str(_ensure_font())
    f_brand = ImageFont.truetype(font_path, 30)
    f_catch = ImageFont.truetype(font_path, 20)

    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pill_x, pill_y = 40, HEIGHT - 110
    draw.rounded_rectangle([pill_x, pill_y, pill_x + 260, pill_y + 46], radius=23, fill=_PANEL)
    draw.text((pill_x + 20, pill_y + 8), _BRAND, font=f_brand, fill=_WHITE)

    catch_y = pill_y + 54
    draw.rounded_rectangle([pill_x, catch_y, pill_x + 330, catch_y + 34], radius=17, fill=_PANEL)
    draw.text((pill_x + 16, catch_y + 6), _CATCHPHRASE, font=f_catch, fill=_WHITE)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG")
    return output_path


def main():
    out_path = Path(__file__).parent / "static" / "logo_overlay.png"
    generate_logo_overlay(out_path)
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: テストを実行して成功を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_generate_logo_overlay.py -v`
Expected: 2 passed（フォント未取得環境ではskip、正常）

- [ ] **Step 5: 実際にロゴオーバーレイを生成する**

```bash
cd uketome-soudanshitsu && python generate_logo_overlay.py
```

- [ ] **Step 6: コミット**

```bash
git add uketome-soudanshitsu/generate_logo_overlay.py uketome-soudanshitsu/tests/test_generate_logo_overlay.py uketome-soudanshitsu/static/logo_overlay.png
git commit -m "うけとめ相談室: ロゴ/キャッチコピー独立生成generate_logo_overlay.pyを追加"
```

---

### Task 7: compose_thumbnail.py（背景+ロゴ+見出しの合成）

**Files:**
- Create: `uketome-soudanshitsu/compose_thumbnail.py`
- Test: `uketome-soudanshitsu/tests/test_compose_thumbnail.py`

**Interfaces:**
- Consumes: `generate_thumbnail._ensure_font`, `generate_thumbnail._gradient_image`, `generate_thumbnail._wrap_text`（既存関数を再利用）
- Produces: `compose_thumbnail(title: str, color_start: tuple, color_end: tuple, output_path: Path, background_path: Path | None = None, logo_overlay_path: Path | None = None) -> Path`

- [ ] **Step 1: 失敗するテストを書く**

```python
from pathlib import Path

import pytest
from PIL import Image

from generate_thumbnail import FONT_PATH

requires_font = pytest.mark.skipif(
    not FONT_PATH.exists(),
    reason="Font not present — run: cd uketome-soudanshitsu && python -c \"from generate_thumbnail import _ensure_font; _ensure_font()\"",
)


@requires_font
def test_compose_thumbnail_without_background_uses_gradient_fallback(tmp_path):
    from compose_thumbnail import compose_thumbnail

    output_path = tmp_path / "out.png"
    compose_thumbnail(
        title="なぜ恋愛は苦しいのか",
        color_start=(240, 98, 146),
        color_end=(123, 31, 162),
        output_path=output_path,
        background_path=None,
        logo_overlay_path=None,
    )
    img = Image.open(output_path)
    assert img.format == "PNG"
    assert img.size == (1280, 670)


@requires_font
def test_compose_thumbnail_resizes_mismatched_background(tmp_path):
    from compose_thumbnail import compose_thumbnail

    bg_path = tmp_path / "bg.png"
    Image.new("RGB", (800, 400), (10, 20, 30)).save(bg_path)

    output_path = tmp_path / "out.png"
    compose_thumbnail(
        title="お金の不安、聞いてから解決",
        color_start=(255, 179, 0),
        color_end=(230, 81, 0),
        output_path=output_path,
        background_path=bg_path,
        logo_overlay_path=None,
    )
    img = Image.open(output_path)
    assert img.size == (1280, 670)


@requires_font
def test_compose_thumbnail_applies_logo_overlay(tmp_path):
    from compose_thumbnail import compose_thumbnail

    overlay_path = tmp_path / "overlay.png"
    overlay = Image.new("RGBA", (1280, 670), (0, 0, 0, 0))
    for x in range(50):
        for y in range(50):
            overlay.putpixel((x, y), (1, 2, 3, 255))
    overlay.save(overlay_path)

    output_path = tmp_path / "out.png"
    compose_thumbnail(
        title="自分を好きになれない理由",
        color_start=(126, 87, 194),
        color_end=(69, 39, 160),
        output_path=output_path,
        background_path=None,
        logo_overlay_path=overlay_path,
    )
    img = Image.open(output_path).convert("RGB")
    assert img.getpixel((10, 10)) == (1, 2, 3)
```

- [ ] **Step 2: テストを実行して失敗を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_compose_thumbnail.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'compose_thumbnail'`

- [ ] **Step 3: `compose_thumbnail.py`を実装する**

```python
"""うけとめ相談室 — 背景写真 + ロゴオーバーレイ + 見出しの合成

ad-designerが生成した背景写真(またはgenerate_thumbnail.pyのグラデーション背景)に
logo_overlay.pngと当日の見出しを重ねて最終サムネイル(1280x670)を作る。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from generate_thumbnail import _ensure_font, _gradient_image, _wrap_text

WIDTH, HEIGHT = 1280, 670
_WHITE = (255, 255, 255)


def _load_background(background_path: Path | None, color_start: tuple, color_end: tuple) -> Image.Image:
    if background_path is not None and background_path.exists():
        img = Image.open(background_path).convert("RGB")
    else:
        img = _gradient_image(color_start, color_end)
    if img.size != (WIDTH, HEIGHT):
        img = img.resize((WIDTH, HEIGHT))
    return img


def compose_thumbnail(
    title: str,
    color_start: tuple,
    color_end: tuple,
    output_path: Path,
    background_path: Path | None = None,
    logo_overlay_path: Path | None = None,
) -> Path:
    background = _load_background(background_path, color_start, color_end).convert("RGBA")

    font_path = str(_ensure_font())
    f_title = ImageFont.truetype(font_path, 50)
    draw = ImageDraw.Draw(background)
    lines = _wrap_text(title, 15)[:3]
    y = 60
    for line in lines:
        draw.text((60, y), line, font=f_title, fill=_WHITE)
        y += 64

    if logo_overlay_path is not None and logo_overlay_path.exists():
        overlay = Image.open(logo_overlay_path).convert("RGBA")
        if overlay.size != background.size:
            overlay = overlay.resize(background.size)
        background = Image.alpha_composite(background, overlay)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    background.convert("RGB").save(output_path, format="PNG", optimize=True)
    return output_path
```

- [ ] **Step 4: テストを実行して成功を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_compose_thumbnail.py -v`
Expected: 3 passed

- [ ] **Step 5: コミット**

```bash
git add uketome-soudanshitsu/compose_thumbnail.py uketome-soudanshitsu/tests/test_compose_thumbnail.py
git commit -m "うけとめ相談室: 背景+ロゴ+見出し合成compose_thumbnail.pyを追加"
```

---

### Task 8: サブエージェント4種の作成

**Files:**
- Create: `C:\Users\admin\.claude\agents\performance-analyst-soudan.md`
- Create: `C:\Users\admin\.claude\agents\concept-planner-soudan.md`
- Create: `C:\Users\admin\.claude\agents\writer-soudan.md`
- Create: `C:\Users\admin\.claude\agents\qa-reviewer-soudan.md`
- Test: `uketome-soudanshitsu/tests/test_agent_definitions.py`

**注意:** これら4ファイルは`C:\Users\admin\.claude\agents\`（ユーザーのグローバル設定）に置く。`C:\Users\admin\.local\bin`のgitリポジトリ外なので、このリポジトリへのコミット対象にはならない。

**Interfaces:**
- Produces: 4つのサブエージェント定義（`name`, `description`, `tools`, `model`のfrontmatterを持つMarkdownファイル）

- [ ] **Step 1: 失敗するテストを書く**

```python
from pathlib import Path

AGENTS_DIR = Path.home() / ".claude" / "agents"
EXPECTED_AGENTS = {
    "performance-analyst-soudan": {"Read", "Write", "Glob"},
    "concept-planner-soudan": {"Read", "Write", "WebSearch"},
    "writer-soudan": {"Read", "Write"},
    "qa-reviewer-soudan": {"Read", "Write"},
}


def _parse_frontmatter(text: str) -> dict:
    assert text.startswith("---"), "frontmatter missing"
    end = text.index("---", 3)
    block = text[3:end].strip()
    result = {}
    for line in block.splitlines():
        key, _, value = line.partition(":")
        result[key.strip()] = value.strip()
    return result


def test_all_four_agent_files_exist():
    for name in EXPECTED_AGENTS:
        assert (AGENTS_DIR / f"{name}.md").exists(), f"{name}.md not found"


def test_each_agent_frontmatter_has_required_fields():
    for name in EXPECTED_AGENTS:
        text = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")
        meta = _parse_frontmatter(text)
        assert meta["name"] == name
        assert meta["description"]
        assert meta["tools"]
        assert meta["model"] == "sonnet"


def test_each_agent_declares_expected_tools():
    for name, required_tools in EXPECTED_AGENTS.items():
        text = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")
        meta = _parse_frontmatter(text)
        declared = {t.strip() for t in meta["tools"].split(",")}
        assert required_tools.issubset(declared), f"{name} missing tools {required_tools - declared}"
```

- [ ] **Step 2: テストを実行して失敗を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_agent_definitions.py -v`
Expected: FAIL（`test_all_four_agent_files_exist`が失敗）

- [ ] **Step 3: `performance-analyst-soudan.md`を作成する**

```markdown
---
name: performance-analyst-soudan
description: うけとめ相談室の過去投稿実績(スキ数)を分析し、ジャンル選定・特化判定のブリーフを作る。日次オーケストレーターの最初に実行する。
tools: Read, Write, Glob
model: sonnet
---

あなたはうけとめ相談室（note.comの悩み相談メソッド記事シリーズ）の分析担当です。

## 入力
- `uketome-soudanshitsu/publish_history.json`（投稿実績ログ）
- `uketome-soudanshitsu/judgment_policy.json`（特化判定パラメータ+自己調整履歴）
- `uketome-soudanshitsu/qa_feedback_log.json`（編集チェックNG理由の蓄積）
- `uketome-soudanshitsu/genre_candidates.json`（ジャンル候補一覧）

## 作業
1. `rotation.py`の`average_likes_by_genre`・`counts_by_genre`相当のロジックで、ジャンル別の平均スキ数とデータ点数を把握する（実際にはBashで`python -c`を使い、これらの関数を呼んで結果を確認してよい）
2. `judgment.py`の`phase_ready`・`should_specialize`を使い、特化フェーズに入るべきかを判定する
3. `judgment.py`の`due_for_outcome_review`で振り返りが必要な過去の特化判定があれば、その判定が正しかったか（優位が継続したか）を評価し、`judgment_policy.json`の`review_history`に振り返り結果と調整後の閾値を追記する（`adjust_ratio_threshold`を使用）
4. `qa_feedback_log.json`の直近10件を読み、頻出する指摘を要約する
5. 直近3投稿のジャンルを確認する

## 出力
以下を含む分析ブリーフをテキストで返す（ファイル保存は不要、次工程に直接渡す）:
- ジャンル別平均スキ数・データ点数の一覧
- 特化フェーズに入るべきか(true/false)とその理由
- 特化フェーズの場合、優先すべきジャンル
- 直近3投稿のジャンル(除外リスト)
- 過去の指摘リスト(直近10件の要約)
- `judgment_policy.json`を更新した場合はその旨と変更内容
```

- [ ] **Step 4: `concept-planner-soudan.md`を作成する**

```markdown
---
name: concept-planner-soudan
description: うけとめ相談室の分析ブリーフを受け取り、本日のジャンル・切り口・記事構成案を決定する。数回に1回、新ジャンル候補の軽いリサーチも行う。
tools: Read, Write, WebSearch
model: sonnet
---

あなたはうけとめ相談室（note.comの悩み相談メソッド記事シリーズ）の企画会議担当です。

## 入力
- performance-analyst-soudanからの分析ブリーフ（ジャンル別平均スキ数・特化判定・直近3投稿ジャンル・過去の指摘リスト）
- `uketome-soudanshitsu/genre_candidates.json`（ジャンル候補一覧）
- `uketome-soudanshitsu/articles_config.py`（既存ジャンルの基本情報）
- `uketome-soudanshitsu/articles/`配下の過去記事（同じジャンルの過去の切り口を確認するため）

## 作業
1. 分析ブリーフの「直近3投稿のジャンル」を除外した候補から、特化判定に従って本日のジャンルを選ぶ（特化フェーズなら優位ジャンルを優先しつつ完全に切り捨てない）
2. 選んだジャンルについて、`articles/`内の過去記事と重複しない新しい切り口(angle)を考える
3. 5回に1回程度の頻度で、WebSearchを使って「需要はあるが供給が少ない」悩みジャンルの候補を軽くリサーチし、良さそうなものがあれば`genre_candidates.json`に`status: "candidate"`で追加する（じっくりではなくざっくりでよい）
4. 分析ブリーフの「過去の指摘リスト」を踏まえ、構成案に注意点として反映する
5. うけとめ相談室の型（承認→見極め→メカニズム解説→出し分けアプローチ→統合メソッド）に沿った構成案を作る

## 出力
以下を含む構成案をテキストで返す（次工程に直接渡す）:
- 本日のジャンル(key)・ジャンル名
- 切り口(angle)
- 各STEPの要点(承認/見極め/メカニズム/アプローチ/統合メソッド)
- 執筆時に気をつけるべき注意点リスト（過去の指摘の反映）
- タイトル案（サムネイル見出し用、15文字×3行程度に収まる長さ）
```

- [ ] **Step 5: `writer-soudan.md`を作成する**

```markdown
---
name: writer-soudan
description: うけとめ相談室の構成案どおりに記事本文を執筆する。編集チェックでNGが出た場合は、指摘理由と過去の指摘リストを踏まえて修正する。
tools: Read, Write
model: sonnet
---

あなたはうけとめ相談室（note.comの悩み相談メソッド記事シリーズ）の執筆担当です。

## 入力
- concept-planner-soudanからの構成案（ジャンル・切り口・各STEPの要点・注意点リスト）
- 修正依頼の場合: qa-reviewer-soudanからのNG理由リスト

## 執筆ルール
- 型: STEP0 承認 → STEP1 見極め(精神科医・心理学者・脳科学者の視点) → メカニズム解説 → アプローチ提示(話したいだけ/本質的な問題で出し分け) → 統合メソッド
- 実在の専門家個人の発言として引用しない。一般的な視点として記述する
- 末尾に「医療行為ではない」旨の免責文を明記する
- 「絶対に治る」等の断定表現は禁止
- 構成案の「注意点リスト」に挙げられた過去の指摘（同じ指摘を繰り返さない）を必ず反映する
- NG理由リストを渡された場合は、その指摘に直接対応する形で該当箇所を書き直す

## 出力
`uketome-soudanshitsu/articles/<date>_<genre>.md`に記事本文を保存する（日付は実行日、genreは構成案のジャンルkey）。
タイトルも冒頭に明記する（`# タイトル`形式）。
```

- [ ] **Step 6: `qa-reviewer-soudan.md`を作成する**

```markdown
---
name: qa-reviewer-soudan
description: うけとめ相談室の記事本文を投稿前にチェックし、GO/NG判定と具体的なNG理由を出す。NG理由は箇条書きで構造化し、執筆担当が直接修正に使える形にする。
tools: Read, Write
model: sonnet
---

あなたはうけとめ相談室（note.comの悩み相談メソッド記事シリーズ）の編集チェック担当です。

## 入力
writer-soudanが作成した`uketome-soudanshitsu/articles/<date>_<genre>.md`

## チェック項目
- 型（承認→見極め→メカニズム解説→出し分けアプローチ→統合メソッド）の各STEPが揃っているか
- 実在の専門家個人の発言として引用していないか
- 免責文が末尾にあるか
- 「絶対に治る」等の断定的な表現がないか
- 過去記事・過去の切り口と内容が重複しすぎていないか
- 誤字脱字、文章として不自然な箇所がないか

## 出力
以下の形式でテキストを返す（次工程に直接渡す。ファイル保存は不要）:

```
## 判定: GO / NG

## チェック結果
- 型の完全性: 
- 表現の適切性: 
- 重複チェック: 
- 文章品質: 

## NG理由リスト(NGの場合のみ、箇条書きで具体的に)
- 
```

NG理由は執筆担当がそのまま修正指示として使える具体性を持たせること（例:「STEP0の承認が弱い」ではなく「STEP0で『そう感じるのは自然』という前置きが抜けている」のように書く）。
```

- [ ] **Step 7: テストを実行して成功を確認する**

Run: `cd uketome-soudanshitsu && python -m pytest tests/test_agent_definitions.py -v`
Expected: 3 passed

- [ ] **Step 8: テストファイルのみコミット（エージェント定義はリポジトリ外）**

```bash
git add uketome-soudanshitsu/tests/test_agent_definitions.py
git commit -m "うけとめ相談室: 4サブエージェント定義の存在検証テストを追加"
```

---

### Task 9: daily_routine.md（日次オーケストレーターのプレイブック）

**Files:**
- Create: `uketome-soudanshitsu/daily_routine.md`

**Interfaces:**
- Consumes: Task 1〜8で作成した全モジュール・サブエージェント・JSONファイル
- Produces: `/schedule`から呼び出されるプレイブック本体

- [ ] **Step 1: `daily_routine.md`を作成する**

```markdown
# うけとめ相談室 日次オーケストレーター

毎日1回、このプレイブックに従って実行する。設計書: `docs/superpowers/specs/2026-08-11-uketome-soudanshitsu-daily-automation-design.md`

## 0. 事前チェック

1. `cd uketome-soudanshitsu && python -c "from control import is_enabled; from pathlib import Path; print(is_enabled(Path('routine_control.json')))"` を実行する
   - `False`なら、Push通知で「うけとめ相談室: 停止中のため本日はスキップ」を送って終了する
2. `cd uketome-soudanshitsu && python -c "from history_store import load_history, already_recorded_today; from pathlib import Path; from datetime import date; h = load_history(Path('publish_history.json')); print(already_recorded_today(h, date.today().isoformat()))"` を実行する
   - `True`なら、二重実行なので何もせず終了する

## 1. 分析（performance-analyst-soudan）

Agentツールで`performance-analyst-soudan`を起動し、分析ブリーフを取得する。

## 2. 企画会議（concept-planner-soudan）

Agentツールで`concept-planner-soudan`を起動し、分析ブリーフを渡して本日の構成案を取得する。

## 3. 執筆〜編集チェックのループ（最大2回リトライ）

1. Agentツールで`writer-soudan`を起動し、構成案から記事本文を書かせる
2. Agentツールで`qa-reviewer-soudan`を起動し、GO/NG判定を取得する
3. GOなら4へ進む
4. NGなら、NG理由を`qa_feedback_log.json`に追記し（`history_store.py`と同じ書き込みパターンでJSON配列にappendする）、`writer-soudan`にNG理由を渡して再執筆させる。これを最大2回まで繰り返す
5. 2回ともNGなら、`publish_history.json`に`{"date": 今日, "status": "skipped", "reason": "qa_ng_max_retry"}`を追記し、Push通知を送って終了する

## 4. 画像生成

1. Agentツールで`ad-designer`を起動し、本日のジャンルのシーン設定から背景写真を生成させる（保存先: `uketome-soudanshitsu/thumbnails/<date>_<genre>_bg.png`）
2. 生成に失敗した場合、`cd uketome-soudanshitsu && python generate_thumbnail.py`相当のグラデーション背景をフォールバックとして使う（`compose_thumbnail.py`の`background_path=None`で自動的にフォールバックされる）

## 5. 画像合成

```bash
cd uketome-soudanshitsu && python -c "
from pathlib import Path
from compose_thumbnail import compose_thumbnail
compose_thumbnail(
    title='<本日のタイトル案>',
    color_start=(<articles_config.pyの該当ジャンルcolor_start>),
    color_end=(<同color_end>),
    output_path=Path('thumbnails/<date>_<genre>.png'),
    background_path=Path('thumbnails/<date>_<genre>_bg.png'),
    logo_overlay_path=Path('static/logo_overlay.png'),
)
"
```

## 6. note投稿（claude-in-chrome）

1. note.comの新規記事作成画面を開く
2. タイトルを入力 → 必ずTabキーで本文欄へ移動
3. スクリーンショットでタイトルが見出しスタイルで本文と分離されていることを確認してから本文を流し込む
4. `mcp__claude-in-chrome__file_upload`でアイキャッチ画像(`thumbnails/<date>_<genre>.png`)のアップロードを試みる
   - 失敗した場合: 画像なしのまま次へ進む（`image_upload_failed`として後でログに記録）
5. 公開し、発行後のURLを取得する
6. 投稿自体が失敗した場合は1回だけリトライする。それでも失敗したら`publish_history.json`に`status: "skipped", "reason": "post_failed"`を記録してPush通知を送り終了する

## 7. ログ記録

`uketome-soudanshitsu/publish_history.json`に本日のエントリをappendする（`history_store.append_entry`と同じ形式）:

```json
{
  "date": "<今日の日付>",
  "status": "published",
  "genre": "<ジャンルkey>",
  "angle": "<切り口>",
  "note_url": "<取得したURL>",
  "like_count": null,
  "like_count_checked_at": null,
  "qa_retry_count": <0,1,2のいずれか>
}
```

画像アップロードが失敗していた場合は`"image_upload_failed": true`も追加する。

## 8. 過去記事のスキ数更新

`publish_history.json`の`status: "published"`かつ`note_url`があるすべてのエントリについて、`like_counter.fetch_like_count`でスキ数を再取得し、`like_count`と`like_count_checked_at`を更新する。

## 9. Push通知

以下を要約してPush通知を送る:
- 選んだジャンル・切り口
- note URL（成功時）／スキップ理由（スキップ時）
- QA再試行回数
- 画像アップロードが手動対応必要な場合はその旨
```

- [ ] **Step 2: コミット**

```bash
git add uketome-soudanshitsu/daily_routine.md
git commit -m "うけとめ相談室: 日次オーケストレーターのプレイブックdaily_routine.mdを追加"
```

---

### Task 10: /schedule登録 + 監督下でのドライラン

**Files:**
- なし（`/schedule`の設定と、実際に1回実行して確認する運用タスク）

- [ ] **Step 1: 監督下でドライランを1回実行する**

Task 1〜9を実装した状態で、`daily_routine.md`の内容を1回だけ手動でこのセッション内で実行する（`/schedule`登録前に、実際にnote.comへ1記事投稿されるところまで人が見ながら確認する）。

**確認ポイント:**
- 分析→企画→執筆→QA→画像→投稿→ログ記録の各ステップが順番に動くか
- note投稿でタイトルと本文が混在する事故が起きていないか（スクリーンショットで確認）
- `publish_history.json`に正しい形式でエントリが追記されているか
- Push通知が届くか

問題があれば該当タスクのコードまたは`daily_routine.md`を修正し、再度Task該当ステップからやり直す。

- [ ] **Step 2: ドライランの結果をコミットする**

```bash
git add uketome-soudanshitsu/publish_history.json uketome-soudanshitsu/articles/ uketome-soudanshitsu/thumbnails/
git commit -m "うけとめ相談室: 日次自動投稿の初回ドライラン結果を記録"
```

- [ ] **Step 3: `/schedule`で日次cronを登録する**

`schedule`スキルを使い、毎日9:00 JSTに`uketome-soudanshitsu/daily_routine.md`を実行するcronエントリを作成する（希望時刻が異なる場合はユーザーに確認する）。

- [ ] **Step 4: ユーザーに運用開始を報告する**

以下を伝える:
- `/schedule`登録が完了し、明日から自動実行されること
- 停止したい場合は`routine_control.json`の`enabled`を`false`にすればよいこと
- 閾値やジャンルを変えたい場合は該当JSONファイルを編集すればよいこと
```

