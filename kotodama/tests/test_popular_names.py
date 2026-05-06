from popular_names import POPULAR_NAMES, get_name_entry, get_related_names


def test_popular_names_has_50_entries():
    assert len(POPULAR_NAMES) == 50


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


def test_get_related_names_returns_5():
    related = get_related_names("さくら")
    assert len(related) == 5
    assert all(e["mei"] != "さくら" for e in related)
