from kanji_dict import get_kanji_data

# Vowel/open sounds in hiragana that indicate extroverted phonetics
_OPEN_SOUNDS = set("あおはらまやわかさたなは")
_OPEN_ENDINGS = ("a", "o", "ra", "na", "ma", "ha", "wa", "ya")


def calculate_strokes(text: str) -> int:
    """Sum stroke counts for all characters in text."""
    return sum(get_kanji_data(ch)["strokes"] for ch in text)


def classify_phonetics(yomi: str) -> str:
    """Return 'open' if name sounds are outward/bright, 'inner' if inward/calm."""
    clean = yomi.replace(" ", "").replace("　", "")
    open_count = sum(1 for ch in clean if ch in _OPEN_SOUNDS)
    return "open" if open_count >= len(clean) / 2 else "inner"


def analyze_name(sei: str, mei: str, yomi: str) -> dict:
    """Return full name analysis dict."""
    sei_meanings: list[str] = []
    for ch in sei:
        sei_meanings.extend(get_kanji_data(ch)["meanings"])

    mei_meanings: list[str] = []
    mei_personality: list[str] = []
    for ch in mei:
        data = get_kanji_data(ch)
        mei_meanings.extend(data["meanings"])
        mei_personality.extend(data["personality"])

    personality_keywords = list(dict.fromkeys(mei_personality))[:4]

    return {
        "sei": sei,
        "mei": mei,
        "yomi": yomi,
        "sei_strokes": calculate_strokes(sei),
        "mei_strokes": calculate_strokes(mei),
        "total_strokes": calculate_strokes(sei) + calculate_strokes(mei),
        "sei_meanings": list(dict.fromkeys(sei_meanings)),
        "mei_meanings": list(dict.fromkeys(mei_meanings)),
        "phonetic_type": classify_phonetics(yomi),
        "personality_keywords": personality_keywords,
    }
