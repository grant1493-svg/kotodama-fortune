from kanji_dict import KANJI, get_kanji_data


def test_known_kanji_has_strokes():
    data = get_kanji_data("大")
    assert data["strokes"] == 3


def test_known_kanji_has_meanings():
    data = get_kanji_data("花")
    assert "美" in data["meanings"]


def test_unknown_kanji_returns_defaults():
    data = get_kanji_data("龍")
    assert data["strokes"] == 0
    assert data["meanings"] == ["神秘"]
    assert data["personality"] == ["独自性"]
