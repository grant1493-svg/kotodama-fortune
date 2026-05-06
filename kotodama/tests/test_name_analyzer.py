from name_analyzer import analyze_name, classify_phonetics, calculate_strokes


def test_calculate_strokes_uses_dict():
    # 大=3, 花=7
    assert calculate_strokes("大花") == 10


def test_classify_phonetics_open():
    # a/o/ha/ra/ma/ya/wa sounds → open
    assert classify_phonetics("さくら") == "open"


def test_classify_phonetics_inner():
    # i/u/ki/shi sounds → inner
    assert classify_phonetics("ゆき") == "inner"


def test_analyze_name_returns_expected_keys():
    result = analyze_name("田中", "花", "たなか はな")
    assert "sei" in result
    assert "mei" in result
    assert "total_strokes" in result
    assert "sei_meanings" in result
    assert "mei_meanings" in result
    assert "phonetic_type" in result
    assert "personality_keywords" in result


def test_analyze_name_total_strokes():
    # 田=5, 中=4, 花=7 → 16
    result = analyze_name("田中", "花", "たなか はな")
    assert result["total_strokes"] == 16


def test_analyze_name_meanings_include_kanji_meanings():
    result = analyze_name("田中", "花", "たなか はな")
    assert "美" in result["mei_meanings"]
