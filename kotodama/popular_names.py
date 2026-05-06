POPULAR_NAMES: list[dict] = [
    # ── 女性名 25件 ──────────────────────────────────────
    {"mei": "さくら",   "kanji": "桜"},
    {"mei": "ひな",     "kanji": "陽菜"},
    {"mei": "みお",     "kanji": "美桜"},
    {"mei": "あかり",   "kanji": "灯"},
    {"mei": "ゆい",     "kanji": "結衣"},
    {"mei": "えま",     "kanji": "恵麻"},
    {"mei": "りん",     "kanji": "凛"},
    {"mei": "はな",     "kanji": "花"},
    {"mei": "あおい",   "kanji": "葵"},
    {"mei": "れな",     "kanji": "麗奈"},
    {"mei": "ゆうか",   "kanji": "優花"},
    {"mei": "みなみ",   "kanji": "南"},
    {"mei": "ひより",   "kanji": "陽和"},
    {"mei": "なつ",     "kanji": "夏"},
    {"mei": "まい",     "kanji": "舞"},
    {"mei": "あい",     "kanji": "愛"},
    {"mei": "はるか",   "kanji": "遥"},
    {"mei": "かの",     "kanji": "佳乃"},
    {"mei": "しおり",   "kanji": "詩織"},
    {"mei": "かほ",     "kanji": "果穂"},
    {"mei": "ことの",   "kanji": "琴乃"},
    {"mei": "みき",     "kanji": "美季"},
    {"mei": "りか",     "kanji": "里香"},
    {"mei": "のあ",     "kanji": "望愛"},
    {"mei": "ここ",     "kanji": "心々"},
    # ── 男性名 25件 ──────────────────────────────────────
    {"mei": "はると",   "kanji": "陽翔"},
    {"mei": "ゆうと",   "kanji": "勇人"},
    {"mei": "りく",     "kanji": "陸"},
    {"mei": "そら",     "kanji": "空"},
    {"mei": "かいと",   "kanji": "海斗"},
    {"mei": "たいよう", "kanji": "太陽"},
    {"mei": "しょうた", "kanji": "翔太"},
    {"mei": "だいき",   "kanji": "大輝"},
    {"mei": "ゆうき",   "kanji": "勇気"},
    {"mei": "けん",     "kanji": "健"},
    {"mei": "たくみ",   "kanji": "匠"},
    {"mei": "あきら",   "kanji": "明"},
    {"mei": "はやと",   "kanji": "隼人"},
    {"mei": "りょう",   "kanji": "遼"},
    {"mei": "だいち",   "kanji": "大地"},
    {"mei": "こうき",   "kanji": "光輝"},
    {"mei": "しゅん",   "kanji": "俊"},
    {"mei": "なおと",   "kanji": "直人"},
    {"mei": "まさき",   "kanji": "雅樹"},
    {"mei": "たつき",   "kanji": "達樹"},
    {"mei": "けいと",   "kanji": "圭斗"},
    {"mei": "ともや",   "kanji": "友也"},
    {"mei": "ひろ",     "kanji": "広"},
    {"mei": "けいすけ", "kanji": "圭介"},
    {"mei": "さとし",   "kanji": "聡"},
]

_NAME_INDEX: dict[str, dict] = {e["mei"]: e for e in POPULAR_NAMES}


def get_name_entry(mei: str) -> dict | None:
    """Return name entry by mei (reading), or None if not found."""
    return _NAME_INDEX.get(mei)


def get_related_names(mei: str, count: int = 5) -> list[dict]:
    """Return `count` other names, excluding the given mei."""
    others = [e for e in POPULAR_NAMES if e["mei"] != mei]
    return others[:count]
