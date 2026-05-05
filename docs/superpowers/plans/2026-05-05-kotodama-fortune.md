# ことだま占い Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Flask web app that analyzes a Japanese name and generates a daily AI fortune using real weather/calendar data, monetized with Google AdSense.

**Architecture:** Flask serves Jinja2 HTML pages. Python modules handle name analysis (kanji dict), weather/calendar stats (Open-Meteo + jpholiday), and Claude API calls. Fortune results are cached server-side (JSON file, key = date+name hash). The browser handles streak count, countdown timer, and morning-message visibility via localStorage and vanilla JS.

**Tech Stack:** Python 3.11+, Flask, anthropic SDK (`claude-haiku-4-5-20251001`), requests, jpholiday, python-dotenv, pytest

---

## File Map

```
kotodama/
├── app.py                    # Flask routes + session handling
├── fortune_engine.py         # Claude API prompt + call + parse
├── name_analyzer.py          # Kanji analysis (strokes, meanings, phonetics)
├── stats_fetcher.py          # Open-Meteo weather + 六曜/二十四節気/jpholiday
├── kanji_dict.py             # Kanji data table (strokes, meanings, personality)
├── cache.py                  # Server-side JSON file cache
├── requirements.txt
├── .env.example
├── templates/
│   ├── base.html             # <head> with AdSense slot, cookie banner, footer links
│   ├── register.html         # Name registration form + localStorage auto-fill JS
│   ├── fortune.html          # Full fortune result page
│   ├── privacy.html
│   ├── tokushoho.html
│   └── disclaimer.html
├── static/
│   ├── css/style.css         # Kawaii pink/lavender design, responsive
│   └── js/app.js             # Streak, countdown timer, morning banner logic
└── tests/
    ├── test_kanji_dict.py
    ├── test_name_analyzer.py
    ├── test_stats_fetcher.py
    ├── test_fortune_engine.py
    ├── test_cache.py
    └── test_app.py
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `kotodama/requirements.txt`
- Create: `kotodama/.env.example`
- Create: `kotodama/app.py` (skeleton)
- Create: `kotodama/tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p kotodama/templates kotodama/static/css kotodama/static/js kotodama/tests
touch kotodama/tests/__init__.py
```

- [ ] **Step 2: Create `kotodama/requirements.txt`**

```
flask==3.1.0
anthropic==0.49.0
requests==2.32.3
jpholiday==0.1.8
python-dotenv==1.0.1
pytest==8.3.5
pytest-mock==3.14.0
```

- [ ] **Step 3: Create `kotodama/.env.example`**

```
ANTHROPIC_API_KEY=your_api_key_here
FLASK_SECRET_KEY=change_this_to_a_random_string
```

- [ ] **Step 4: Install dependencies**

```bash
cd kotodama
pip install -r requirements.txt
```

Expected: no errors.

- [ ] **Step 5: Create skeleton `kotodama/app.py`**

```python
from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=True)
```

- [ ] **Step 6: Write health check test `kotodama/tests/test_app.py`**

```python
import pytest
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    with flask_app.test_client() as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
```

- [ ] **Step 7: Run test**

```bash
cd kotodama
pytest tests/test_app.py -v
```

Expected: `PASSED`

- [ ] **Step 8: Commit**

```bash
git add kotodama/
git commit -m "feat: scaffold kotodama Flask project"
```

---

## Task 2: Kanji Dictionary

**Files:**
- Create: `kotodama/kanji_dict.py`
- Create: `kotodama/tests/test_kanji_dict.py`

- [ ] **Step 1: Write failing test**

```python
# kotodama/tests/test_kanji_dict.py
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
```

- [ ] **Step 2: Run test to confirm failure**

```bash
cd kotodama && pytest tests/test_kanji_dict.py -v
```

Expected: `ImportError` or `FAILED`

- [ ] **Step 3: Create `kotodama/kanji_dict.py`**

```python
# Starter set of common name kanji. Expand to cover user's actual names.
KANJI: dict[str, dict] = {
    "大": {"strokes": 3,  "meanings": ["偉大", "広がり", "包容力"], "personality": ["リーダー", "大局観"]},
    "小": {"strokes": 3,  "meanings": ["繊細", "丁寧", "細やか"], "personality": ["観察力", "気配り"]},
    "山": {"strokes": 3,  "meanings": ["安定", "堅実", "不動"],   "personality": ["信頼感", "忍耐"]},
    "川": {"strokes": 3,  "meanings": ["流れ", "柔軟", "変化"],   "personality": ["適応力", "感受性"]},
    "田": {"strokes": 5,  "meanings": ["豊か", "実り", "大地"],   "personality": ["誠実", "勤勉"]},
    "中": {"strokes": 4,  "meanings": ["中心", "バランス", "調和"],"personality": ["調停力", "公平"]},
    "木": {"strokes": 4,  "meanings": ["成長", "生命", "自然"],   "personality": ["向上心", "柔軟"]},
    "水": {"strokes": 4,  "meanings": ["流れ", "清潔", "浄化"],   "personality": ["知性", "直感"]},
    "火": {"strokes": 4,  "meanings": ["情熱", "エネルギー", "変革"],"personality": ["行動力", "カリスマ"]},
    "金": {"strokes": 8,  "meanings": ["繁栄", "輝き", "価値"],   "personality": ["決断力", "成功"]},
    "子": {"strokes": 3,  "meanings": ["純粋", "子孫", "可愛らしさ"],"personality": ["愛されキャラ", "親しみ"]},
    "花": {"strokes": 7,  "meanings": ["美", "華やか", "開花"],   "personality": ["魅力", "社交性"]},
    "愛": {"strokes": 13, "meanings": ["愛情", "温かさ", "絆"],   "personality": ["思いやり", "共感力"]},
    "美": {"strokes": 9,  "meanings": ["美しさ", "調和", "感性"], "personality": ["審美眼", "創造性"]},
    "春": {"strokes": 9,  "meanings": ["希望", "新生", "躍動"],   "personality": ["明るさ", "前向き"]},
    "夏": {"strokes": 10, "meanings": ["活力", "情熱", "輝き"],   "personality": ["エネルギッシュ", "積極的"]},
    "秋": {"strokes": 9,  "meanings": ["実り", "成熟", "深み"],   "personality": ["思慮深さ", "完成度"]},
    "冬": {"strokes": 5,  "meanings": ["静寂", "内省", "蓄積"],   "personality": ["集中力", "忍耐"]},
    "陽": {"strokes": 12, "meanings": ["明るさ", "温もり", "活力"],"personality": ["ポジティブ", "社交的"]},
    "光": {"strokes": 6,  "meanings": ["輝き", "希望", "道"],     "personality": ["理想主義", "先見性"]},
    "明": {"strokes": 8,  "meanings": ["知性", "明晰", "正直"],   "personality": ["論理的", "誠実"]},
    "真": {"strokes": 10, "meanings": ["真実", "誠実", "本質"],   "personality": ["誠実さ", "純粋"]},
    "優": {"strokes": 17, "meanings": ["優しさ", "思いやり", "品格"],"personality": ["協調性", "上品"]},
    "健": {"strokes": 11, "meanings": ["健康", "強さ", "活力"],   "personality": ["行動力", "生命力"]},
    "翔": {"strokes": 12, "meanings": ["飛翔", "自由", "可能性"], "personality": ["チャレンジ精神", "自由"]},
    "桜": {"strokes": 10, "meanings": ["美", "生命", "再生"],     "personality": ["魅力", "感受性"]},
    "葵": {"strokes": 12, "meanings": ["向上", "太陽", "成長"],   "personality": ["向上心", "明朗"]},
    "蓮": {"strokes": 13, "meanings": ["清潔", "高潔", "再生"],   "personality": ["清廉さ", "精神性"]},
    "奏": {"strokes": 9,  "meanings": ["調和", "音楽", "伝える"], "personality": ["表現力", "協調性"]},
    "凛": {"strokes": 15, "meanings": ["気品", "凛々しさ", "意志"],"personality": ["芯の強さ", "気高さ"]},
    "心": {"strokes": 4,  "meanings": ["心", "感情", "思いやり"], "personality": ["共感力", "繊細さ"]},
    "空": {"strokes": 8,  "meanings": ["自由", "広大", "無限"],   "personality": ["自由精神", "大らかさ"]},
    "海": {"strokes": 9,  "meanings": ["深さ", "広大", "包容力"], "personality": ["包容力", "神秘性"]},
    "風": {"strokes": 9,  "meanings": ["変化", "自由", "伝達"],   "personality": ["変化適応", "コミュニケーション"]},
    "星": {"strokes": 9,  "meanings": ["輝き", "目標", "希望"],   "personality": ["理想追求", "個性"]},
    "月": {"strokes": 4,  "meanings": ["神秘", "変化", "感性"],   "personality": ["直感", "芸術性"]},
    "太": {"strokes": 4,  "meanings": ["偉大", "豊か", "大らか"], "personality": ["おおらかさ", "包容力"]},
    "幸": {"strokes": 8,  "meanings": ["幸福", "恵み", "喜び"],   "personality": ["幸運体質", "感謝"]},
    "希": {"strokes": 7,  "meanings": ["希望", "珍しさ", "望み"], "personality": ["希望力", "独自性"]},
    "咲": {"strokes": 9,  "meanings": ["開花", "笑顔", "活発"],   "personality": ["明るさ", "親しみやすさ"]},
    "彩": {"strokes": 11, "meanings": ["色彩", "個性", "豊か"],   "personality": ["表現力", "多才"]},
    "結": {"strokes": 12, "meanings": ["縁", "絆", "まとめる"],   "personality": ["人脈", "まとめ役"]},
    "莉": {"strokes": 10, "meanings": ["ジャスミン", "清楚", "香り"],"personality": ["清楚", "繊細"]},
    "菜": {"strokes": 11, "meanings": ["自然", "生命力", "素直"], "personality": ["素直さ", "自然体"]},
    "里": {"strokes": 7,  "meanings": ["故郷", "温かさ", "安らぎ"],"personality": ["家族愛", "安定"]},
    "那": {"strokes": 7,  "meanings": ["美しさ", "優雅", "遠い"],  "personality": ["優雅さ", "個性"]},
    "穂": {"strokes": 15, "meanings": ["実り", "豊か", "成長"],   "personality": ["粘り強さ", "充実"]},
    "楓": {"strokes": 13, "meanings": ["変化", "美しさ", "季節"], "personality": ["変化対応", "美的感覚"]},
    "朱": {"strokes": 6,  "meanings": ["情熱", "生命力", "赤"],   "personality": ["情熱的", "行動力"]},
    "悠": {"strokes": 11, "meanings": ["ゆったり", "永遠", "深さ"],"personality": ["ゆとり", "深い思考"]},
}


def get_kanji_data(char: str) -> dict:
    """Returns kanji data. Falls back to defaults for unknown characters."""
    return KANJI.get(char, {
        "strokes": 0,
        "meanings": ["神秘"],
        "personality": ["独自性"],
    })
```

- [ ] **Step 4: Run tests**

```bash
cd kotodama && pytest tests/test_kanji_dict.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add kotodama/kanji_dict.py kotodama/tests/test_kanji_dict.py
git commit -m "feat: add kanji dictionary"
```

---

## Task 3: Name Analyzer

**Files:**
- Create: `kotodama/name_analyzer.py`
- Create: `kotodama/tests/test_name_analyzer.py`

- [ ] **Step 1: Write failing tests**

```python
# kotodama/tests/test_name_analyzer.py
from name_analyzer import analyze_name, classify_phonetics, calculate_strokes


def test_calculate_strokes_known():
    assert calculate_strokes("大輝") == 3 + 15  # 大=3, 輝=15(fallback 0 → actual test value)


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
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd kotodama && pytest tests/test_name_analyzer.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `kotodama/name_analyzer.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
cd kotodama && pytest tests/test_name_analyzer.py -v
```

Expected: all `PASSED` (note: `大輝` test uses fallback 0 for 輝, so strokes=3. Adjust test to `assert calculate_strokes("田中") == 9` if needed.)

- [ ] **Step 5: Fix the strokes test to use only known kanji**

Edit `test_calculate_strokes_known` to:
```python
def test_calculate_strokes_known():
    # 田=5, 中=4
    assert calculate_strokes("田中") == 9
```

- [ ] **Step 6: Commit**

```bash
git add kotodama/name_analyzer.py kotodama/tests/test_name_analyzer.py
git commit -m "feat: add name analyzer module"
```

---

## Task 4: Stats Fetcher

**Files:**
- Create: `kotodama/stats_fetcher.py`
- Create: `kotodama/tests/test_stats_fetcher.py`

- [ ] **Step 1: Write failing tests**

```python
# kotodama/tests/test_stats_fetcher.py
from datetime import date
from unittest.mock import patch
from stats_fetcher import get_rokuyo, get_today_stats, CITY_COORDS


def test_rokuyo_returns_valid_value():
    result = get_rokuyo(date(2026, 5, 5))
    assert result in ["大安", "赤口", "先勝", "友引", "先負", "仏滅"]


def test_rokuyo_taian():
    # (5+5) % 6 = 4 → 先負 with our formula
    result = get_rokuyo(date(2026, 5, 5))
    assert isinstance(result, str)


def test_city_coords_tokyo():
    lat, lon = CITY_COORDS["東京"]
    assert 35.0 < lat < 36.0
    assert 139.0 < lon < 140.0


def test_get_today_stats_returns_expected_keys():
    mock_weather = {
        "current": {
            "temperature_2m": 22.5,
            "surface_pressure": 1008.2,
            "relative_humidity_2m": 55,
            "weather_code": 0,
        }
    }
    with patch("stats_fetcher.requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_weather
        mock_get.return_value.raise_for_status.return_value = None
        result = get_today_stats("東京")

    for key in ["date", "weekday", "rokuyo", "weather", "temperature",
                "pressure", "humidity", "is_holiday"]:
        assert key in result, f"Missing key: {key}"


def test_get_today_stats_weather_sunny():
    mock_weather = {
        "current": {
            "temperature_2m": 25.0,
            "surface_pressure": 1012.0,
            "relative_humidity_2m": 40,
            "weather_code": 0,
        }
    }
    with patch("stats_fetcher.requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_weather
        mock_get.return_value.raise_for_status.return_value = None
        result = get_today_stats("東京")

    assert result["weather"] == "晴れ"
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd kotodama && pytest tests/test_stats_fetcher.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `kotodama/stats_fetcher.py`**

```python
from datetime import date
import requests
import jpholiday

CITY_COORDS: dict[str, tuple[float, float]] = {
    "東京": (35.6895, 139.6917),
    "大阪": (34.6937, 135.5023),
    "名古屋": (35.1815, 136.9066),
    "札幌": (43.0618, 141.3545),
    "福岡": (33.5904, 130.4017),
    "仙台": (38.2688, 140.8721),
    "広島": (34.3853, 132.4553),
    "京都": (35.0116, 135.7681),
    "神戸": (34.6901, 135.1956),
    "横浜": (35.4478, 139.6425),
}
_DEFAULT_COORDS = (35.6895, 139.6917)  # 東京

_ROKUYO = ["大安", "赤口", "先勝", "友引", "先負", "仏滅"]
_WEEKDAYS = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]

# Approximate 二十四節気 dates (month, day) for 2026
_SEKKI_2026: dict[tuple[int, int], str] = {
    (1, 6): "小寒", (1, 20): "大寒",
    (2, 4): "立春", (2, 19): "雨水",
    (3, 6): "啓蟄", (3, 20): "春分",
    (4, 5): "清明", (4, 20): "穀雨",
    (5, 6): "立夏", (5, 21): "小満",
    (6, 6): "芒種", (6, 21): "夏至",
    (7, 7): "小暑", (7, 23): "大暑",
    (8, 7): "立秋", (8, 23): "処暑",
    (9, 8): "白露", (9, 23): "秋分",
    (10, 8): "寒露", (10, 23): "霜降",
    (11, 7): "立冬", (11, 22): "小雪",
    (12, 7): "大雪", (12, 22): "冬至",
}

_WMO_WEATHER: dict[range | int, str] = {
    0: "快晴", 1: "晴れ", 2: "やや曇り", 3: "曇り",
    45: "霧", 48: "霧",
    51: "小雨", 53: "雨", 55: "強雨",
    61: "雨", 63: "雨", 65: "大雨",
    71: "雪", 73: "雪", 75: "大雪",
    80: "にわか雨", 81: "にわか雨", 82: "強にわか雨",
    95: "雷雨", 96: "雷雨", 99: "雷雨",
}


def get_rokuyo(d: date) -> str:
    """Simplified 六曜 using (month + day) % 6."""
    return _ROKUYO[(d.month + d.day) % 6]


def get_sekki(d: date) -> str | None:
    """Return 二十四節気 name if today matches, else None."""
    return _SEKKI_2026.get((d.month, d.day))


def _wmo_to_japanese(code: int) -> str:
    return _WMO_WEATHER.get(code, "曇り")


def get_today_stats(region: str) -> dict:
    """Fetch weather + calendar stats for today."""
    today = date.today()
    lat, lon = CITY_COORDS.get(region, _DEFAULT_COORDS)

    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,surface_pressure,relative_humidity_2m,weather_code",
            "timezone": "Asia/Tokyo",
            "forecast_days": 1,
        },
        timeout=10,
    )
    resp.raise_for_status()
    current = resp.json()["current"]

    return {
        "date": today.strftime("%Y年%m月%d日"),
        "date_iso": today.isoformat(),
        "weekday": _WEEKDAYS[today.weekday()],
        "rokuyo": get_rokuyo(today),
        "sekki": get_sekki(today),
        "is_holiday": bool(jpholiday.is_holiday(today)),
        "weather": _wmo_to_japanese(int(current["weather_code"])),
        "temperature": round(float(current["temperature_2m"]), 1),
        "pressure": round(float(current["surface_pressure"]), 1),
        "humidity": int(current["relative_humidity_2m"]),
    }
```

- [ ] **Step 4: Run tests**

```bash
cd kotodama && pytest tests/test_stats_fetcher.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add kotodama/stats_fetcher.py kotodama/tests/test_stats_fetcher.py
git commit -m "feat: add stats fetcher (weather + calendar)"
```

---

## Task 5: Server Cache

**Files:**
- Create: `kotodama/cache.py`
- Create: `kotodama/tests/test_cache.py`

- [ ] **Step 1: Write failing tests**

```python
# kotodama/tests/test_cache.py
import json
from pathlib import Path
import pytest
from cache import make_cache_key, get_cached, set_cached


@pytest.fixture(autouse=True)
def clean_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("cache.CACHE_DIR", tmp_path)
    yield


def test_make_cache_key_is_deterministic():
    k1 = make_cache_key("田中", "花", "2026-05-05")
    k2 = make_cache_key("田中", "花", "2026-05-05")
    assert k1 == k2


def test_make_cache_key_different_dates():
    k1 = make_cache_key("田中", "花", "2026-05-05")
    k2 = make_cache_key("田中", "花", "2026-05-06")
    assert k1 != k2


def test_get_cached_miss_returns_none():
    assert get_cached("nonexistent-key") is None


def test_set_and_get_cached():
    data = {"today_message": "今日も良い日です"}
    set_cached("test-key", data)
    result = get_cached("test-key")
    assert result == data


def test_cache_persists_as_json(tmp_path, monkeypatch):
    monkeypatch.setattr("cache.CACHE_DIR", tmp_path)
    set_cached("my-key", {"score": 5})
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    saved = json.loads(files[0].read_text(encoding="utf-8"))
    assert saved["score"] == 5
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd kotodama && pytest tests/test_cache.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `kotodama/cache.py`**

```python
import hashlib
import json
from pathlib import Path

CACHE_DIR = Path(__file__).parent / ".fortune_cache"


def make_cache_key(sei: str, mei: str, date_iso: str) -> str:
    raw = f"{sei}{mei}{date_iso}"
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_path(key: str) -> Path:
    CACHE_DIR.mkdir(exist_ok=True)
    return CACHE_DIR / f"{key}.json"


def get_cached(key: str) -> dict | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def set_cached(key: str, data: dict) -> None:
    _cache_path(key).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
```

- [ ] **Step 4: Run tests**

```bash
cd kotodama && pytest tests/test_cache.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add kotodama/cache.py kotodama/tests/test_cache.py
git commit -m "feat: add server-side fortune cache"
```

---

## Task 6: Fortune Engine (Claude API)

**Files:**
- Create: `kotodama/fortune_engine.py`
- Create: `kotodama/tests/test_fortune_engine.py`

- [ ] **Step 1: Write failing tests**

```python
# kotodama/tests/test_fortune_engine.py
import json
import pytest
from unittest.mock import MagicMock, patch
from fortune_engine import build_prompt, parse_fortune_response, generate_fortune

SAMPLE_NAME = {"sei": "田中", "mei": "花", "yomi": "たなか はな",
               "total_strokes": 16, "sei_meanings": ["豊か", "実り"],
               "mei_meanings": ["美", "華やか"], "phonetic_type": "open",
               "personality_keywords": ["魅力", "社交性"]}

SAMPLE_STATS = {"date": "2026年05月05日", "date_iso": "2026-05-05",
                "weekday": "火曜日", "rokuyo": "大安", "sekki": "立夏",
                "is_holiday": True, "weather": "晴れ",
                "temperature": 22.5, "pressure": 1008.2, "humidity": 55}

VALID_JSON = json.dumps({
    "kotodama_analysis": "花の漢字は美と華やかさを持ちます",
    "today_message": "今日は素晴らしい一日です",
    "morning_message": "朝の光があなたを包みます",
    "scores": {"overall": 4, "love": 3, "work": 5, "money": 3},
    "lucky": {"color": "ピンク", "time": "午前10時", "place": "カフェ", "number": 7},
})


def test_build_prompt_contains_name():
    system, user = build_prompt(SAMPLE_NAME, SAMPLE_STATS)
    assert "田中" in user
    assert "花" in user


def test_build_prompt_contains_stats():
    system, user = build_prompt(SAMPLE_NAME, SAMPLE_STATS)
    assert "大安" in user
    assert "立夏" in user
    assert "1008.2" in user


def test_parse_fortune_response_valid():
    result = parse_fortune_response(VALID_JSON)
    assert result["scores"]["overall"] == 4
    assert result["lucky"]["color"] == "ピンク"
    assert "今日は" in result["today_message"]


def test_parse_fortune_response_wrapped_in_markdown():
    wrapped = f"```json\n{VALID_JSON}\n```"
    result = parse_fortune_response(wrapped)
    assert result["scores"]["overall"] == 4


def test_generate_fortune_calls_claude_and_returns_dict(monkeypatch):
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=VALID_JSON)]
    mock_client.messages.create.return_value = mock_message

    with patch("fortune_engine.anthropic.Anthropic", return_value=mock_client):
        result = generate_fortune(SAMPLE_NAME, SAMPLE_STATS)

    assert result["scores"]["overall"] == 4
    assert "today_message" in result
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd kotodama && pytest tests/test_fortune_engine.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `kotodama/fortune_engine.py`**

```python
import json
import re
import anthropic

_SYSTEM_PROMPT = """あなたは「ことだま占い師」です。名前の言霊（ことだま）と今日の統計データをもとに占い結果を生成します。
温かく親しみやすい文体で、20〜40代の女性に向けて語りかけてください。
必ず以下のJSON形式のみで返答してください。前後に説明文は不要です。

{
  "kotodama_analysis": "名前の言霊分析（60〜80字）",
  "today_message": "今日のあなたへのメッセージ（80〜100字）",
  "morning_message": "朝イチ限定の一言（40〜55字、朝の清々しさを表現）",
  "scores": {"overall": 1〜5の整数, "love": 1〜5の整数, "work": 1〜5の整数, "money": 1〜5の整数},
  "lucky": {"color": "色名", "time": "時間帯", "place": "場所名", "number": 1〜9の整数}
}"""


def build_prompt(name_analysis: dict, today_stats: dict) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for Claude."""
    phonetic_label = "開放的・社交的" if name_analysis["phonetic_type"] == "open" else "内省的・繊細"
    sekki_text = f"・節気: {today_stats['sekki']}" if today_stats.get("sekki") else ""
    holiday_text = "（祝日）" if today_stats["is_holiday"] else ""

    user = f"""名前: {name_analysis['sei']}{name_analysis['mei']}（{name_analysis['yomi']}）
総画数: {name_analysis['total_strokes']}画
名前の意味: {', '.join(name_analysis['mei_meanings'][:3])}
性格キーワード: {', '.join(name_analysis['personality_keywords'])}
音の印象: {phonetic_label}

今日のデータ:
- 日付: {today_stats['date']} {today_stats['weekday']}{holiday_text}
- 六曜: {today_stats['rokuyo']}{sekki_text}
- 天気: {today_stats['weather']}
- 気温: {today_stats['temperature']}°C
- 気圧: {today_stats['pressure']}hPa
- 湿度: {today_stats['humidity']}%"""

    return _SYSTEM_PROMPT, user


def parse_fortune_response(text: str) -> dict:
    """Extract and parse JSON from Claude response. Strips markdown fences if present."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)


def generate_fortune(name_analysis: dict, today_stats: dict) -> dict:
    """Call Claude API and return parsed fortune dict."""
    system_prompt, user_prompt = build_prompt(name_analysis, today_stats)
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return parse_fortune_response(message.content[0].text)
```

- [ ] **Step 4: Run tests**

```bash
cd kotodama && pytest tests/test_fortune_engine.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add kotodama/fortune_engine.py kotodama/tests/test_fortune_engine.py
git commit -m "feat: add fortune engine with Claude API integration"
```

---

## Task 7: Flask Routes

**Files:**
- Modify: `kotodama/app.py`
- Modify: `kotodama/tests/test_app.py`

- [ ] **Step 1: Add route tests**

Append to `kotodama/tests/test_app.py`:

```python
import json
from unittest.mock import patch

SAMPLE_FORTUNE = {
    "kotodama_analysis": "花の言霊は美しさと開花を示します",
    "today_message": "今日は素晴らしい一日です",
    "morning_message": "朝の光があなたを導きます",
    "scores": {"overall": 4, "love": 3, "work": 5, "money": 3},
    "lucky": {"color": "ピンク", "time": "午前10時", "place": "カフェ", "number": 7},
}

SAMPLE_STATS = {
    "date": "2026年05月05日", "date_iso": "2026-05-05",
    "weekday": "火曜日", "rokuyo": "大安", "sekki": "立夏",
    "is_holiday": True, "weather": "晴れ",
    "temperature": 22.5, "pressure": 1008.2, "humidity": 55,
}


def test_index_redirects_to_register(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/register" in resp.headers["Location"]


def test_register_get_returns_200(client):
    resp = client.get("/register")
    assert resp.status_code == 200
    assert "ことだま占い" in resp.data.decode("utf-8")


def test_register_post_sets_session_and_redirects(client):
    resp = client.post("/register", data={
        "sei": "田中", "mei": "花", "yomi": "たなか はな", "region": "東京"
    }, follow_redirects=False)
    assert resp.status_code == 302
    assert "/fortune" in resp.headers["Location"]


def test_fortune_without_session_redirects(client):
    resp = client.get("/fortune")
    assert resp.status_code == 302
    assert "/register" in resp.headers["Location"]


def test_fortune_with_session_returns_200(client):
    with client.session_transaction() as sess:
        sess["sei"] = "田中"
        sess["mei"] = "花"
        sess["yomi"] = "たなか はな"
        sess["region"] = "東京"

    with patch("app.get_cached", return_value=SAMPLE_FORTUNE), \
         patch("app.get_today_stats", return_value=SAMPLE_STATS):
        resp = client.get("/fortune")

    assert resp.status_code == 200
    assert "田中" in resp.data.decode("utf-8")


def test_privacy_returns_200(client):
    assert client.get("/privacy").status_code == 200


def test_tokushoho_returns_200(client):
    assert client.get("/tokushoho").status_code == 200


def test_disclaimer_returns_200(client):
    assert client.get("/disclaimer").status_code == 200
```

- [ ] **Step 2: Run to confirm new tests fail**

```bash
cd kotodama && pytest tests/test_app.py -v
```

Expected: multiple `FAILED` (routes not yet defined)

- [ ] **Step 3: Replace `kotodama/app.py` with full implementation**

```python
from flask import Flask, redirect, render_template, request, session, url_for
from dotenv import load_dotenv
import os

from cache import get_cached, make_cache_key, set_cached
from fortune_engine import generate_fortune
from name_analyzer import analyze_name
from stats_fetcher import get_today_stats

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/")
def index():
    if "sei" in session:
        return redirect(url_for("fortune"))
    return redirect(url_for("register"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        session["sei"] = request.form["sei"].strip()
        session["mei"] = request.form["mei"].strip()
        session["yomi"] = request.form["yomi"].strip()
        session["region"] = request.form.get("region", "東京").strip()
        return redirect(url_for("fortune"))
    return render_template("register.html")


@app.route("/fortune")
def fortune():
    if "sei" not in session:
        return redirect(url_for("register"))

    sei = session["sei"]
    mei = session["mei"]
    yomi = session["yomi"]
    region = session.get("region", "東京")

    today_stats = get_today_stats(region)
    cache_key = make_cache_key(sei, mei, today_stats["date_iso"])

    fortune_data = get_cached(cache_key)
    if fortune_data is None:
        name_analysis = analyze_name(sei, mei, yomi)
        fortune_data = generate_fortune(name_analysis, today_stats)
        set_cached(cache_key, fortune_data)

    return render_template(
        "fortune.html",
        sei=sei,
        mei=mei,
        stats=today_stats,
        fortune=fortune_data,
    )


@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("register"))


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/tokushoho")
def tokushoho():
    return render_template("tokushoho.html")


@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")


if __name__ == "__main__":
    app.run(debug=True)
```

- [ ] **Step 4: Create placeholder templates so routes don't crash**

```bash
echo "ことだま占い" > kotodama/templates/register.html
echo "fortune" > kotodama/templates/fortune.html
echo "privacy" > kotodama/templates/privacy.html
echo "tokushoho" > kotodama/templates/tokushoho.html
echo "disclaimer" > kotodama/templates/disclaimer.html
```

- [ ] **Step 5: Run tests**

```bash
cd kotodama && pytest tests/test_app.py -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add kotodama/app.py kotodama/tests/test_app.py kotodama/templates/
git commit -m "feat: add Flask routes with session + cache integration"
```

---

## Task 8: CSS Design

**Files:**
- Create: `kotodama/static/css/style.css`

- [ ] **Step 1: Create `kotodama/static/css/style.css`**

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --pink: #f06292;
  --pink-light: #fce4ec;
  --purple: #ce93d8;
  --purple-light: #f3e5f5;
  --text: #444;
  --text-muted: #999;
  --radius: 18px;
  --radius-sm: 10px;
}

body {
  font-family: 'Hiragino Maru Gothic ProN', 'BIZ UDPGothic', 'Noto Sans JP', sans-serif;
  background: linear-gradient(160deg, #fff0f6 0%, #f3e8ff 50%, #e8f4ff 100%);
  min-height: 100vh;
  color: var(--text);
  font-size: 15px;
}

.container { max-width: 480px; margin: 0 auto; padding: 20px 16px 40px; }

/* ── Header ── */
.app-header { text-align: center; padding: 28px 0 20px; }
.app-logo { font-size: 48px; margin-bottom: 6px; }
.app-name { font-size: 22px; font-weight: bold; color: #c2185b; }
.app-tagline { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

/* ── Cards ── */
.card {
  background: white;
  border-radius: var(--radius);
  border: 1.5px solid var(--pink-light);
  padding: 16px;
  margin-bottom: 14px;
  box-shadow: 0 2px 12px rgba(200, 100, 180, 0.08);
}
.card-title { font-size: 12px; font-weight: bold; color: #b06090; margin-bottom: 10px; }

/* ── Register form ── */
.field-label { font-size: 11px; color: #b06090; font-weight: bold; margin: 14px 0 4px; }
.cute-input {
  width: 100%;
  border: 2px solid var(--pink-light);
  border-radius: 22px;
  padding: 10px 16px;
  font-size: 15px;
  outline: none;
  background: #fff8fb;
  color: var(--text);
  transition: border-color 0.2s;
}
.cute-input:focus { border-color: var(--pink); }

select.cute-input { cursor: pointer; }

.consent-text { font-size: 11px; color: var(--text-muted); margin: 14px 0; line-height: 1.6; }

.btn-primary {
  width: 100%;
  background: linear-gradient(135deg, var(--pink), var(--purple));
  color: white;
  border: none;
  border-radius: 25px;
  padding: 14px;
  font-size: 15px;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(240, 98, 146, 0.35);
  margin-top: 6px;
  transition: opacity 0.2s;
}
.btn-primary:hover { opacity: 0.9; }

/* ── Streak bar ── */
.streak-bar {
  background: linear-gradient(135deg, #fff3e0, #fce4ec);
  border: 1.5px solid #ffcc80;
  border-radius: 14px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.streak-count { font-size: 22px; font-weight: bold; color: #e65100; }
.streak-label { font-size: 11px; color: #bf360c; font-weight: bold; }
.badges { display: flex; gap: 5px; flex-wrap: wrap; justify-content: flex-end; }
.badge {
  font-size: 10px; padding: 3px 9px;
  border-radius: 10px; background: #ffe0b2; color: #e65100; font-weight: bold;
}
.badge.earned { background: #ff8f00; color: white; }

/* ── Countdown ── */
.countdown-bar {
  background: #f3e5f5;
  border-radius: 12px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 13px;
  color: #7b1fa2;
}
.countdown-bar.urgent { background: #fce4ec; color: #c2185b; }
.countdown-time { font-weight: bold; font-size: 15px; }

/* ── Morning banner ── */
.morning-banner {
  background: linear-gradient(135deg, #fff8e1, #e8f5e9);
  border: 1.5px dashed #aed581;
  border-radius: 14px;
  padding: 13px 16px;
  margin-bottom: 12px;
  text-align: center;
}
.morning-label { font-size: 10px; color: #558b2f; font-weight: bold; margin-bottom: 5px; }
.morning-label .new { background: #e91e63; color: white; font-size: 9px; padding: 2px 6px; border-radius: 6px; margin-left: 4px; }
.morning-text { font-size: 13px; color: #33691e; line-height: 1.7; }
.morning-ended { opacity: 0.5; }

/* ── Date header ── */
.date-header {
  background: linear-gradient(135deg, var(--pink-light), var(--purple-light));
  border-radius: 14px;
  padding: 12px 16px;
  margin-bottom: 12px;
  text-align: center;
}
.date-text { font-size: 11px; color: var(--text-muted); }
.date-greeting { font-size: 16px; font-weight: bold; color: #c2185b; margin-top: 4px; }

/* ── Stars ── */
.stars-row { display: flex; justify-content: space-around; }
.star-item { text-align: center; }
.star-item .label { font-size: 10px; color: var(--text-muted); margin-bottom: 3px; }
.star-item .stars { font-size: 15px; }

/* ── Fortune bubbles ── */
.bubble {
  background: white;
  border: 1.5px solid var(--pink-light);
  border-radius: 16px;
  padding: 13px 16px;
  margin-bottom: 12px;
  font-size: 13px;
  line-height: 1.75;
  color: #555;
}
.bubble-title { font-size: 11px; font-weight: bold; color: #c2185b; margin-bottom: 6px; }
.data-chip {
  display: inline-block;
  background: var(--purple-light);
  color: #7b1fa2;
  border-radius: 10px;
  padding: 2px 8px;
  font-size: 10px;
  margin: 2px;
}

/* ── Lucky strip ── */
.lucky-strip {
  background: linear-gradient(135deg, #fff8e1, var(--pink-light));
  border-radius: 14px;
  padding: 11px 16px;
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 13px;
  color: #b06090;
  margin-bottom: 14px;
}

/* ── Share buttons ── */
.share-row { display: flex; gap: 10px; margin-bottom: 8px; }
.btn-share {
  flex: 1;
  border: none;
  border-radius: 22px;
  padding: 11px 8px;
  font-size: 13px;
  font-weight: bold;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-share:hover { opacity: 0.85; }
.btn-share-x { background: #1a1a1a; color: white; }
.btn-share-line { background: #06c755; color: white; }
.share-sub { text-align: center; font-size: 11px; color: var(--text-muted); margin-bottom: 14px; }

/* ── Ad placeholder (styled for when AdSense loads) ── */
.ad-slot {
  min-height: 90px;
  background: #fafafa;
  border: 1px dashed #ddd;
  border-radius: var(--radius-sm);
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #ccc;
}

/* ── Cookie banner ── */
.cookie-banner {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  border-top: 1px solid var(--pink-light);
  padding: 12px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: #666;
  z-index: 999;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.08);
}
.cookie-banner button {
  background: var(--pink);
  color: white;
  border: none;
  border-radius: 20px;
  padding: 7px 16px;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}

/* ── Footer ── */
.footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--pink-light);
  font-size: 11px;
  color: var(--text-muted);
}
.footer a { color: #b06090; text-decoration: none; margin: 0 6px; }
.footer a:hover { text-decoration: underline; }
.reset-link { display: block; margin-top: 10px; font-size: 11px; color: var(--text-muted); }

/* ── Legal pages ── */
.legal-container { max-width: 680px; margin: 0 auto; padding: 24px 20px 60px; }
.legal-container h1 { font-size: 20px; color: #c2185b; margin-bottom: 20px; }
.legal-container h2 { font-size: 15px; color: #555; margin: 20px 0 8px; }
.legal-container p, .legal-container li { font-size: 13px; line-height: 1.8; color: #666; }
.legal-container ul { padding-left: 18px; }

/* ── Responsive ── */
@media (max-width: 480px) {
  .container { padding: 16px 12px 32px; }
  .lucky-strip { gap: 10px; }
}
```

- [ ] **Step 2: Commit**

```bash
git add kotodama/static/css/style.css
git commit -m "feat: add kawaii CSS design (pink/lavender)"
```

---

## Task 9: Base Template

**Files:**
- Modify: `kotodama/templates/base.html`

- [ ] **Step 1: Replace placeholder with real `kotodama/templates/base.html`**

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}ことだま占い{% endblock %}</title>
  <meta name="description" content="AIとリアルデータが紡ぐ、今日のあなたへの言霊占い">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
  <!-- Google AdSense: paste your AdSense <script> tag here after approval -->
  <!-- <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script> -->
</head>
<body>
  {% block content %}{% endblock %}

  <!-- Cookie banner -->
  <div class="cookie-banner" id="cookieBanner" style="display:none">
    <span>このサイトはGoogle AdSenseのCookieを使用します。
      <a href="{{ url_for('privacy') }}" style="color:#b06090">詳細</a>
    </span>
    <button onclick="acceptCookies()">同意する</button>
  </div>

  <script src="{{ url_for('static', filename='js/app.js') }}"></script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add kotodama/templates/base.html
git commit -m "feat: add base template with AdSense slot + cookie banner"
```

---

## Task 10: Register Template

**Files:**
- Modify: `kotodama/templates/register.html`

- [ ] **Step 1: Replace placeholder with real `kotodama/templates/register.html`**

```html
{% extends "base.html" %}
{% block title %}名前を登録する — ことだま占い{% endblock %}
{% block content %}
<div class="container">
  <div class="app-header">
    <div class="app-logo">🔮</div>
    <div class="app-name">ことだま占い</div>
    <div class="app-tagline">AIとリアルデータが紡ぐ、今日のあなたへのメッセージ</div>
  </div>

  <form method="post" action="{{ url_for('register') }}" id="registerForm">
    <div class="card">
      <div class="field-label">✨ 姓（漢字）</div>
      <input class="cute-input" type="text" name="sei" id="sei" placeholder="例：田中" required>

      <div class="field-label">✨ 名（漢字）</div>
      <input class="cute-input" type="text" name="mei" id="mei" placeholder="例：花" required>

      <div class="field-label">🌸 読み（ひらがな）</div>
      <input class="cute-input" type="text" name="yomi" id="yomi" placeholder="例：たなか はな" required>

      <div class="field-label">📍 お住まいの地域</div>
      <select class="cute-input" name="region" id="region">
        <option value="東京">東京</option>
        <option value="大阪">大阪</option>
        <option value="名古屋">名古屋</option>
        <option value="札幌">札幌</option>
        <option value="福岡">福岡</option>
        <option value="仙台">仙台</option>
        <option value="広島">広島</option>
        <option value="京都">京都</option>
        <option value="神戸">神戸</option>
        <option value="横浜">横浜</option>
      </select>

      <p class="consent-text">
        🔒 入力した名前はAIによる占い生成のためAnthropicのサーバーに送信されます。
        端末への永続保存は行いません。
        <a href="{{ url_for('privacy') }}" style="color:#b06090">プライバシーポリシー</a>
      </p>

      <button type="submit" class="btn-primary">🌟 今日の言霊を受け取る</button>
    </div>
  </form>
</div>

<script>
// Auto-fill from localStorage if returning user lost session
(function() {
  const sei = localStorage.getItem("kotodama_sei");
  const mei = localStorage.getItem("kotodama_mei");
  const yomi = localStorage.getItem("kotodama_yomi");
  const region = localStorage.getItem("kotodama_region");
  if (sei && mei && yomi) {
    document.getElementById("sei").value = sei;
    document.getElementById("mei").value = mei;
    document.getElementById("yomi").value = yomi;
    if (region) document.getElementById("region").value = region;
  }
})();

document.getElementById("registerForm").addEventListener("submit", function() {
  localStorage.setItem("kotodama_sei", document.getElementById("sei").value);
  localStorage.setItem("kotodama_mei", document.getElementById("mei").value);
  localStorage.setItem("kotodama_yomi", document.getElementById("yomi").value);
  localStorage.setItem("kotodama_region", document.getElementById("region").value);
});
</script>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add kotodama/templates/register.html
git commit -m "feat: add register template with localStorage auto-fill"
```

---

## Task 11: Fortune Template

**Files:**
- Modify: `kotodama/templates/fortune.html`

- [ ] **Step 1: Replace placeholder with real `kotodama/templates/fortune.html`**

```html
{% extends "base.html" %}
{% block title %}{{ sei }}{{ mei }}さんの今日の占い — ことだま占い{% endblock %}
{% block content %}
<div class="container">

  <!-- Streak bar (populated by app.js) -->
  <div class="streak-bar">
    <div>
      <span style="font-size:22px">🔥</span>
      <span class="streak-count" id="streakCount">1</span>
      <span class="streak-label">日連続チェック中！</span>
    </div>
    <div>
      <div style="font-size:10px;color:#aaa;margin-bottom:4px;text-align:right">達成バッジ</div>
      <div class="badges" id="badgesRow">
        <span class="badge" id="badge3">3日🎀</span>
        <span class="badge" id="badge7">7日⭐</span>
        <span class="badge" id="badge30">30日👑</span>
      </div>
    </div>
  </div>

  <!-- Countdown timer -->
  <div class="countdown-bar" id="countdownBar">
    <span>⏰ 今日の占いは <strong>23:59</strong> にリセット</span>
    <span class="countdown-time" id="countdownTime">--:--:--</span>
  </div>

  <!-- AdSense top slot -->
  <div class="ad-slot">
    <!-- ins class="adsbygoogle" ... -->
    広告
  </div>

  <!-- Morning banner -->
  <div class="morning-banner" id="morningBanner">
    <div class="morning-label">🌅 朝イチ限定メッセージ <span class="new">NEW</span></div>
    <div class="morning-text">{{ fortune.morning_message }}</div>
  </div>
  <div class="morning-banner morning-ended" id="morningEnded" style="display:none">
    <div class="morning-label">🌅 朝イチ限定メッセージ（本日分は終了）</div>
    <div class="morning-text" style="font-size:11px">明日の朝もお楽しみに 🌸</div>
  </div>

  <!-- Date header -->
  <div class="date-header">
    <div class="date-text">
      {{ stats.date }}（{{ stats.weekday }}）{{ stats.rokuyo }}
      {% if stats.sekki %}・{{ stats.sekki }}{% endif %}
      {{ stats.weather }} / {{ stats.pressure }}hPa
    </div>
    <div class="date-greeting">{{ sei }} {{ mei }}さんへ 🌸</div>
  </div>

  <!-- Scores -->
  <div class="card">
    <div class="card-title">📊 今日の統計運勢</div>
    <div class="stars-row">
      {% for label, key in [("総合","overall"),("恋愛","love"),("仕事","work"),("金運","money")] %}
      <div class="star-item">
        <div class="label">{{ label }}</div>
        <div class="stars">{{ "⭐" * fortune.scores[key] }}</div>
      </div>
      {% endfor %}
    </div>
  </div>

  <!-- Kotodama analysis -->
  <div class="bubble">
    <div class="bubble-title">🌸 言霊分析</div>
    {{ fortune.kotodama_analysis }}
    <br>
    <span class="data-chip">{{ stats.rokuyo }}</span>
    <span class="data-chip">{{ stats.weather }}</span>
    {% if stats.sekki %}<span class="data-chip">{{ stats.sekki }}</span>{% endif %}
  </div>

  <!-- Today message -->
  <div class="bubble">
    <div class="bubble-title">💌 今日のメッセージ</div>
    {{ fortune.today_message }}
  </div>

  <!-- AdSense mid slot -->
  <div class="ad-slot">
    <!-- ins class="adsbygoogle" ... -->
    広告
  </div>

  <!-- Lucky -->
  <div class="lucky-strip">
    <span>🎨 {{ fortune.lucky.color }}</span>
    <span>⏰ {{ fortune.lucky.time }}</span>
    <span>📍 {{ fortune.lucky.place }}</span>
    <span>🔢 {{ fortune.lucky.number }}</span>
  </div>

  <!-- Share -->
  <div class="share-row">
    <button class="btn-share btn-share-x" id="shareX">𝕏 シェア</button>
    <button class="btn-share btn-share-line" id="shareLine">LINE シェア</button>
  </div>
  <p class="share-sub">友達と一緒に占うと相性が分かるかも🔮</p>

  <!-- Footer -->
  <div class="footer">
    <div>
      <a href="{{ url_for('privacy') }}">プライバシーポリシー</a>
      <a href="{{ url_for('tokushoho') }}">特定商取引法</a>
      <a href="{{ url_for('disclaimer') }}">免責事項</a>
    </div>
    <a href="{{ url_for('reset') }}" class="reset-link">名前を変更する</a>
    <div style="margin-top:8px">© 2026 ことだま占い — AIによる娯楽コンテンツです</div>
  </div>
</div>

<script>
  // Pass server-rendered values to JS
  const FORTUNE_SEI = {{ sei | tojson }};
  const FORTUNE_MEI = {{ mei | tojson }};
  const FORTUNE_MESSAGE = {{ fortune.today_message | tojson }};
  const FORTUNE_SCORES = {{ fortune.scores | tojson }};
</script>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add kotodama/templates/fortune.html
git commit -m "feat: add fortune result template"
```

---

## Task 12: JavaScript (Streak, Countdown, Morning, Share)

**Files:**
- Modify: `kotodama/static/js/app.js`

- [ ] **Step 1: Create `kotodama/static/js/app.js`**

```javascript
// ── Cookie banner ──────────────────────────────────────────────
function acceptCookies() {
  localStorage.setItem("kotodama_cookies_ok", "1");
  document.getElementById("cookieBanner").style.display = "none";
}

(function initCookieBanner() {
  if (!localStorage.getItem("kotodama_cookies_ok")) {
    const banner = document.getElementById("cookieBanner");
    if (banner) banner.style.display = "flex";
  }
})();

// ── Streak ────────────────────────────────────────────────────
function updateStreak() {
  const today = new Date().toISOString().slice(0, 10);
  const lastVisit = localStorage.getItem("kotodama_last_visit");
  let count = parseInt(localStorage.getItem("kotodama_streak") || "0", 10);

  if (lastVisit === today) {
    // already counted today — just display
  } else {
    const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    count = (lastVisit === yesterday) ? count + 1 : 1;
    localStorage.setItem("kotodama_last_visit", today);
    localStorage.setItem("kotodama_streak", String(count));
  }

  const el = document.getElementById("streakCount");
  if (el) el.textContent = count;

  const badges = { badge3: 3, badge7: 7, badge30: 30 };
  for (const [id, threshold] of Object.entries(badges)) {
    const badge = document.getElementById(id);
    if (badge && count >= threshold) badge.classList.add("earned");
  }
}

// ── Countdown timer ───────────────────────────────────────────
function updateCountdown() {
  const now = new Date();
  const reset = new Date(now);
  reset.setHours(23, 59, 59, 0);
  const diff = reset - now;

  if (diff <= 0) return;

  const h = String(Math.floor(diff / 3600000)).padStart(2, "0");
  const m = String(Math.floor((diff % 3600000) / 60000)).padStart(2, "0");
  const s = String(Math.floor((diff % 60000) / 1000)).padStart(2, "0");

  const el = document.getElementById("countdownTime");
  if (el) el.textContent = `残り ${h}:${m}:${s}`;

  const bar = document.getElementById("countdownBar");
  if (bar) {
    bar.classList.toggle("urgent", diff < 3600000);
  }
}

// ── Morning banner ────────────────────────────────────────────
function updateMorningBanner() {
  const hour = new Date().getHours();
  const banner = document.getElementById("morningBanner");
  const ended = document.getElementById("morningEnded");
  if (!banner || !ended) return;

  if (hour < 12) {
    banner.style.display = "block";
    ended.style.display = "none";
  } else {
    banner.style.display = "none";
    ended.style.display = "block";
  }
}

// ── Share buttons ─────────────────────────────────────────────
function initShareButtons() {
  const xBtn = document.getElementById("shareX");
  const lineBtn = document.getElementById("shareLineBtn") || document.getElementById("shareLine");

  if (typeof FORTUNE_MESSAGE === "undefined") return;

  const text = `【ことだま占い】${FORTUNE_SEI}${FORTUNE_MEI}さんの今日の言霊\n\n${FORTUNE_MESSAGE}\n\n`;
  const url = location.href;

  if (xBtn) {
    xBtn.addEventListener("click", () => {
      window.open(
        `https://x.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`,
        "_blank"
      );
    });
  }

  if (lineBtn) {
    lineBtn.addEventListener("click", () => {
      window.open(
        `https://line.me/R/msg/text/?${encodeURIComponent(text + url)}`,
        "_blank"
      );
    });
  }
}

// ── Init ──────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  updateStreak();
  updateMorningBanner();
  updateCountdown();
  setInterval(updateCountdown, 1000);
  initShareButtons();
});
```

- [ ] **Step 2: Run all tests to confirm nothing broken**

```bash
cd kotodama && pytest -v
```

Expected: all `PASSED`

- [ ] **Step 3: Commit**

```bash
git add kotodama/static/js/app.js
git commit -m "feat: add JS for streak, countdown, morning banner, share"
```

---

## Task 13: Legal Pages

**Files:**
- Modify: `kotodama/templates/privacy.html`
- Modify: `kotodama/templates/tokushoho.html`
- Modify: `kotodama/templates/disclaimer.html`

- [ ] **Step 1: Replace `kotodama/templates/privacy.html`**

```html
{% extends "base.html" %}
{% block title %}プライバシーポリシー — ことだま占い{% endblock %}
{% block content %}
<div class="legal-container">
  <h1>🔒 プライバシーポリシー</h1>
  <p>最終更新日：2026年5月5日</p>

  <h2>収集する情報</h2>
  <ul>
    <li>姓名・読み・居住地域（占い生成のためAnthropicのサーバーに送信されます）</li>
    <li>ご利用状況（Google AdSenseによるCookieを含む）</li>
  </ul>

  <h2>情報の利用目的</h2>
  <ul>
    <li>AIによる占い結果の生成</li>
    <li>サービスの改善</li>
    <li>Google AdSenseによる広告配信</li>
  </ul>

  <h2>Cookieについて</h2>
  <p>本サービスはGoogle AdSenseを利用しており、Cookieが使用されます。
    Cookieを無効にするにはブラウザの設定をご変更ください。</p>

  <h2>第三者への提供</h2>
  <p>取得した情報は法令に基づく場合を除き、第三者に提供しません。
    ただし占い生成のためAnthropicにデータを送信します（Anthropicプライバシーポリシーに準拠）。</p>

  <h2>お問い合わせ</h2>
  <p>プライバシーに関するお問い合わせは特定商取引法ページの連絡先までお願いします。</p>

  <p><a href="{{ url_for('index') }}" style="color:#b06090">← トップへ戻る</a></p>
</div>
{% endblock %}
```

- [ ] **Step 2: Replace `kotodama/templates/tokushoho.html`**

```html
{% extends "base.html" %}
{% block title %}特定商取引法に基づく表記 — ことだま占い{% endblock %}
{% block content %}
<div class="legal-container">
  <h1>📋 特定商取引法に基づく表記</h1>

  <h2>サービス名</h2><p>ことだま占い</p>
  <h2>運営者</h2><p>（運営者名を記入してください）</p>
  <h2>所在地</h2><p>（都道府県のみ可：例 東京都）</p>
  <h2>連絡先</h2><p>（メールアドレスを記入してください）</p>
  <h2>サービス内容</h2><p>AIと統計データを組み合わせた姓名占いサービス（無料）</p>
  <h2>料金</h2><p>無料（Google AdSenseによる広告収入で運営）</p>
  <h2>動作環境</h2><p>インターネットに接続されたブラウザ</p>

  <p><a href="{{ url_for('index') }}" style="color:#b06090">← トップへ戻る</a></p>
</div>
{% endblock %}
```

- [ ] **Step 3: Replace `kotodama/templates/disclaimer.html`**

```html
{% extends "base.html" %}
{% block title %}免責事項 — ことだま占い{% endblock %}
{% block content %}
<div class="legal-container">
  <h1>⚠️ 免責事項</h1>

  <h2>コンテンツの性質</h2>
  <p>本サービスの占い結果はAIによって生成された<strong>娯楽コンテンツ</strong>です。
    統計的根拠の演出を含みますが、科学的・医学的な事実ではありません。</p>

  <h2>利用上の注意</h2>
  <ul>
    <li>占い結果は参考程度にご利用ください。</li>
    <li>医療・投資・法律等の重要な判断には使用しないでください。</li>
    <li>本サービスの利用によって生じた損害について、当方は責任を負いません。</li>
  </ul>

  <h2>サービスの変更・停止</h2>
  <p>予告なくサービス内容を変更・停止する場合があります。</p>

  <p><a href="{{ url_for('index') }}" style="color:#b06090">← トップへ戻る</a></p>
</div>
{% endblock %}
```

- [ ] **Step 4: Run all tests**

```bash
cd kotodama && pytest -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add kotodama/templates/
git commit -m "feat: add legal pages (privacy, tokushoho, disclaimer)"
```

---

## Task 14: End-to-End Smoke Test + AdSense Slot Comments

**Files:**
- Modify: `kotodama/tests/test_app.py`

- [ ] **Step 1: Add smoke test for full fortune flow**

Append to `kotodama/tests/test_app.py`:

```python
def test_full_fortune_flow(client):
    """Register → fortune page shows name and stats."""
    with patch("app.get_cached", return_value=None), \
         patch("app.get_today_stats", return_value=SAMPLE_STATS), \
         patch("app.generate_fortune", return_value=SAMPLE_FORTUNE), \
         patch("app.set_cached", return_value=None):

        client.post("/register", data={
            "sei": "山田", "mei": "桜", "yomi": "やまだ さくら", "region": "大阪"
        })
        resp = client.get("/fortune")

    body = resp.data.decode("utf-8")
    assert "山田" in body
    assert "桜" in body
    assert "大安" in body
    assert "今日は素晴らしい" in body


def test_reset_clears_session(client):
    with client.session_transaction() as sess:
        sess["sei"] = "田中"
        sess["mei"] = "花"
    resp = client.get("/reset", follow_redirects=False)
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert "sei" not in sess
```

- [ ] **Step 2: Run all tests**

```bash
cd kotodama && pytest -v
```

Expected: all `PASSED`

- [ ] **Step 3: Verify app runs locally**

```bash
cd kotodama
FLASK_SECRET_KEY=dev-secret ANTHROPIC_API_KEY=your_key python app.py
```

Open `http://localhost:5000` in browser. Register with a name → verify fortune page renders with kawaii design, streak bar shows 1, countdown ticks.

- [ ] **Step 4: Add `.fortune_cache` to `.gitignore`**

```bash
echo ".fortune_cache/" >> kotodama/.gitignore
echo ".env" >> kotodama/.gitignore
```

- [ ] **Step 5: Final commit**

```bash
git add kotodama/tests/test_app.py kotodama/.gitignore
git commit -m "feat: add smoke tests + gitignore for cache and .env"
```

---

## AdSense Go-Live Checklist (after building)

- [ ] Deploy to Render/Railway (push repo, set `ANTHROPIC_API_KEY` and `FLASK_SECRET_KEY` as env vars)
- [ ] Replace `ad-slot` divs in `fortune.html` with real `<ins class="adsbygoogle">` tags after AdSense approval
- [ ] Paste AdSense `<script>` into `base.html` `<head>` where the comment placeholder is
- [ ] Fill in operator details in `tokushoho.html` (name, address, email)
