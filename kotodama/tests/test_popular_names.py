from popular_names import POPULAR_NAMES, get_name_entry, get_related_names


def test_popular_names_has_many_unique_entries():
    # The list is an SEO asset (one page per name) and has grown well past the
    # original 50 entries. Pin a floor rather than an exact count so it keeps
    # growing without breaking this test, and guard against duplicate "mei"
    # keys silently colliding in _NAME_INDEX.
    assert len(POPULAR_NAMES) >= 400
    meis = [e["mei"] for e in POPULAR_NAMES]
    assert len(meis) == len(set(meis)), "duplicate 'mei' values found in POPULAR_NAMES"


def test_each_entry_has_required_keys():
    for entry in POPULAR_NAMES:
        assert "mei" in entry, f"Missing 'mei' in {entry}"
        assert "kanji" in entry, f"Missing 'kanji' in {entry}"
        assert isinstance(entry["mei"], str) and entry["mei"]
        assert isinstance(entry["kanji"], str) and entry["kanji"]


def test_get_name_entry_found():
    result = get_name_entry("さくら")
    assert result is not None
    assert result["kanji"] == "桜"


def test_get_name_entry_not_found():
    assert get_name_entry("ぞんざい") is None


def test_get_related_names_returns_default_count():
    related = get_related_names("さくら")
    assert len(related) == 6  # get_related_names' default `count`
    assert all(e["mei"] != "さくら" for e in related)


def test_get_related_names_respects_explicit_count():
    related = get_related_names("さくら", count=3)
    assert len(related) == 3
    assert all(e["mei"] != "さくら" for e in related)
