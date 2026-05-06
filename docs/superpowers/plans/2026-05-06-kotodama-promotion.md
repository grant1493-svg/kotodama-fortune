# ことだま占い 宣伝機能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add OGP social sharing tags, a Pillow-generated 1200×630px dark fortune card image, and 50 SEO name pages with sitemap to the existing kotodama Flask app.

**Architecture:** Three independent additions to `kotodama/`: (1) OGP meta tags wired through Jinja2 template blocks, (2) `image_generator.py` uses Pillow to render a dark card PNG served at `/fortune/image.png` and cached in `.fortune_cache/`, (3) `popular_names.py` + `/name/<mei>` route serving static name analysis pages with a fixed preview score to drive Claude-free SEO traffic.

**Tech Stack:** Python + Flask + Pillow==10.4.0, NotoSansJP-Bold.otf (auto-downloaded), existing cache.py, name_analyzer.py

---

## File Map

```
kotodama/
├── image_generator.py          NEW — Pillow image generation
├── popular_names.py             NEW — 50 popular name entries
├── cache.py                     MODIFY — add get/set_cached_image for PNG bytes
├── app.py                       MODIFY — 3 new routes + OGP vars in fortune route
├── requirements.txt             MODIFY — add Pillow==10.4.0
├── templates/
│   ├── base.html                MODIFY — add {% block ogp %}
│   ├── fortune.html             MODIFY — add 📸 save button
│   ├── name_page.html           NEW — SEO name page template
│   └── sitemap.xml              NEW — sitemap template
├── static/
│   └── fonts/
│       └── NotoSansJP-Bold.otf  NEW — auto-downloaded (not committed)
└── tests/
    ├── test_image_generator.py  NEW
    ├── test_cache.py            MODIFY — add image cache tests
    └── test_app.py              MODIFY — add route tests
```

---

## Task 1: Pillow Dependency + Font Setup

**Files:**
- Modify: `kotodama/requirements.txt`
- Create: `kotodama/static/fonts/` directory

- [ ] **Step 1: Add Pillow to requirements.txt**

Open `kotodama/requirements.txt` and add one line:
```
Pillow==10.4.0
```

- [ ] **Step 2: Install Pillow**

```bash
cd kotodama && pip install Pillow==10.4.0
```

Expected: `Successfully installed Pillow-10.4.0` (or already satisfied)

- [ ] **Step 3: Create fonts directory**

```bash
mkdir -p kotodama/static/fonts
```

- [ ] **Step 4: Add fonts directory to kotodama/.gitignore**

Open `kotodama/.gitignore` and add:
```
static/fonts/
```

- [ ] **Step 5: Download NotoSansJP-Bold.otf**

```bash
cd kotodama && python -c "
import urllib.request
from pathlib import Path
url = 'https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf'
out = Path('static/fonts/NotoSansJP-Bold.otf')
out.parent.mkdir(exist_ok=True)
print('Downloading NotoSansJP-Bold.otf ...')
urllib.request.urlretrieve(url, out)
print(f'Saved to {out} ({out.stat().st_size // 1024} KB)')
"
```

Expected: `Saved to static/fonts/NotoSansJP-Bold.otf (XXXX KB)`

- [ ] **Step 6: Commit**

```bash
cd C:/Users/admin/.local/bin
git add kotodama/requirements.txt kotodama/.gitignore
git commit -m "feat: add Pillow dependency and font gitignore"
```

---

## Task 2: Image Generator

**Files:**
- Create: `kotodama/image_generator.py`
- Create: `kotodama/tests/test_image_generator.py`

- [ ] **Step 1: Write failing tests**

Create `kotodama/tests/test_image_generator.py`:

```python
import io
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

FONT_PATH = Path(__file__).parent.parent / "static" / "fonts" / "NotoSansJP-Bold.otf"
requires_font = pytest.mark.skipif(
    not FONT_PATH.exists(),
    reason="Font not present — run: cd kotodama && python -c \"from image_generator import _ensure_font; _ensure_font()\""
)

SAMPLE_STATS = {
    "date": "2026年05月06日", "date_iso": "2026-05-06",
    "weekday": "水曜日", "rokuyo": "大安", "sekki": "立夏",
    "is_holiday": False, "weather": "晴れ",
    "temperature": 22.5, "pressure": 1008.0, "humidity": 55,
}
SAMPLE_FORTUNE = {
    "kotodama_analysis": "花の言霊は美と開花を宿します。今日の大安は行動の日。",
    "today_message": "素晴らしい一日になりますように。",
    "morning_message": "朝の光が導きます。",
    "scores": {"overall": 4, "love": 3, "work": 5, "money": 3},
    "lucky": {"color": "ラベンダー", "time": "午後2時", "place": "カフェ", "number": 7},
}


@requires_font
def test_generate_fortune_image_returns_bytes():
    from image_generator import generate_fortune_image
    result = generate_fortune_image("田中", "花", SAMPLE_STATS, SAMPLE_FORTUNE)
    assert isinstance(result, bytes)
    assert len(result) > 1000


@requires_font
def test_generate_fortune_image_is_valid_png():
    from PIL import Image
    from image_generator import generate_fortune_image
    result = generate_fortune_image("田中", "花", SAMPLE_STATS, SAMPLE_FORTUNE)
    img = Image.open(io.BytesIO(result))
    assert img.format == "PNG"
    assert img.size == (1200, 630)


@requires_font
def test_generate_fortune_image_no_sekki():
    from image_generator import generate_fortune_image
    stats = dict(SAMPLE_STATS, sekki=None)
    result = generate_fortune_image("山田", "桜", stats, SAMPLE_FORTUNE)
    assert isinstance(result, bytes)
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd kotodama && python -m pytest tests/test_image_generator.py -v
```

Expected: 3 tests SKIPPED (font not yet downloaded) or ImportError

- [ ] **Step 3: Download font (if not done in Task 1)**

```bash
cd kotodama && python -c "
import urllib.request
from pathlib import Path
url = 'https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf'
out = Path('static/fonts/NotoSansJP-Bold.otf')
out.parent.mkdir(exist_ok=True)
urllib.request.urlretrieve(url, out)
print('Done:', out.stat().st_size // 1024, 'KB')
"
```

- [ ] **Step 4: Create `kotodama/image_generator.py`**

```python
import io
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path(__file__).parent / "static" / "fonts"
FONT_PATH = FONT_DIR / "NotoSansJP-Bold.otf"
_FONT_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf"

WIDTH, HEIGHT = 1200, 630
_BG_START = (26, 10, 46)    # #1a0a2e
_BG_END   = (45, 27, 78)    # #2d1b4e
_PINK     = (240, 98, 146)  # #f06292
_PURPLE   = (206, 147, 216) # #ce93d8
_WHITE    = (255, 255, 255)
_GRAY     = (160, 140, 180)
_DIMGRAY  = (100, 85, 120)


def _ensure_font() -> Path:
    """Auto-download font if not present."""
    if not FONT_PATH.exists():
        FONT_DIR.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(_FONT_URL, FONT_PATH)
    return FONT_PATH


def _gradient_image() -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    for x in range(WIDTH):
        ratio = x / (WIDTH - 1)
        r = int(_BG_START[0] + (_BG_END[0] - _BG_START[0]) * ratio)
        g = int(_BG_START[1] + (_BG_END[1] - _BG_START[1]) * ratio)
        b = int(_BG_START[2] + (_BG_END[2] - _BG_START[2]) * ratio)
        draw.line([(x, 0), (x, HEIGHT)], fill=(r, g, b))
    return img


def _wrap_text(text: str, max_chars: int) -> list[str]:
    lines, line = [], ""
    for ch in text:
        line += ch
        if len(line) >= max_chars:
            lines.append(line)
            line = ""
    if line:
        lines.append(line)
    return lines


def generate_fortune_image(sei: str, mei: str, stats: dict, fortune: dict) -> bytes:
    """Return 1200×630 PNG bytes of the dark fortune card."""
    font_path = str(_ensure_font())
    f_xs  = ImageFont.truetype(font_path, 20)
    f_sm  = ImageFont.truetype(font_path, 26)
    f_md  = ImageFont.truetype(font_path, 34)
    f_lg  = ImageFont.truetype(font_path, 50)

    img  = _gradient_image()
    draw = ImageDraw.Draw(img)

    # ── Top bar ──────────────────────────────────────────
    draw.text((60, 42), "ことだま占い", font=f_sm, fill=_PURPLE)
    date_str = f"{stats['date']}  {stats['rokuyo']}"
    if stats.get("sekki"):
        date_str += f"  {stats['sekki']}"
    draw.text((1140, 42), date_str, font=f_xs, fill=_GRAY, anchor="ra")

    # ── Name ─────────────────────────────────────────────
    draw.text((60, 105), f"{sei}{mei} さんの言霊", font=f_lg, fill=_WHITE)

    # ── Divider ──────────────────────────────────────────
    draw.line([(60, 178), (1140, 178)], fill=(80, 60, 100), width=1)

    # ── Scores ───────────────────────────────────────────
    score_items = [
        ("総合", "overall"), ("恋愛", "love"), ("仕事", "work"), ("金運", "money")
    ]
    for i, (label, key) in enumerate(score_items):
        x = 60 + i * 270
        score = fortune["scores"][key]
        draw.text((x, 195), label, font=f_xs, fill=_GRAY)
        stars = "★" * score + "☆" * (5 - score)
        draw.text((x, 220), stars, font=f_md, fill=_PURPLE)

    # ── Analysis accent bar + text ────────────────────────
    draw.rectangle([(60, 298), (66, 378)], fill=_PINK)
    analysis = fortune["kotodama_analysis"][:55]
    for i, line in enumerate(_wrap_text(analysis, 26)[:3]):
        draw.text((82, 302 + i * 34), line, font=f_sm, fill=(230, 210, 245))

    # ── Lucky strip ───────────────────────────────────────
    lucky = fortune["lucky"]
    lucky_text = (
        f"色: {lucky['color']}   "
        f"時間: {lucky['time']}   "
        f"場所: {lucky['place']}   "
        f"数字: {lucky['number']}"
    )
    draw.text((60, 415), lucky_text, font=f_sm, fill=_PURPLE)

    # ── URL ───────────────────────────────────────────────
    draw.text((1140, 592), "kotodama-fortune.com", font=f_xs, fill=_DIMGRAY, anchor="ra")

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
```

- [ ] **Step 5: Run tests**

```bash
cd kotodama && python -m pytest tests/test_image_generator.py -v
```

Expected: 3 PASSED (font is present)

- [ ] **Step 6: Commit**

```bash
git add kotodama/image_generator.py kotodama/tests/test_image_generator.py
git commit -m "feat: add Pillow fortune card image generator"
```

---

## Task 3: Image Cache (extend cache.py)

**Files:**
- Modify: `kotodama/cache.py`
- Modify: `kotodama/tests/test_cache.py`

- [ ] **Step 1: Write failing tests**

Append to `kotodama/tests/test_cache.py`:

```python
def test_get_cached_image_miss_returns_none():
    from cache import get_cached_image
    assert get_cached_image("no-such-key") is None


def test_set_and_get_cached_image(tmp_path, monkeypatch):
    monkeypatch.setattr("cache.CACHE_DIR", tmp_path)
    from cache import get_cached_image, set_cached_image
    png_bytes = b"\x89PNG\r\n\x1a\nfake"
    set_cached_image("img-key", png_bytes)
    result = get_cached_image("img-key")
    assert result == png_bytes


def test_cached_image_stored_as_png_file(tmp_path, monkeypatch):
    monkeypatch.setattr("cache.CACHE_DIR", tmp_path)
    from cache import set_cached_image
    set_cached_image("my-img", b"PNGDATA")
    files = list(tmp_path.glob("*.png"))
    assert len(files) == 1
    assert files[0].name == "my-img.png"
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd kotodama && python -m pytest tests/test_cache.py -v -k "image"
```

Expected: ImportError or FAILED

- [ ] **Step 3: Add image cache functions to `kotodama/cache.py`**

Append to the end of `kotodama/cache.py`:

```python
def get_cached_image(key: str) -> bytes | None:
    path = CACHE_DIR / f"{key}.png"
    if not path.exists():
        return None
    return path.read_bytes()


def set_cached_image(key: str, data: bytes) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    (CACHE_DIR / f"{key}.png").write_bytes(data)
```

- [ ] **Step 4: Run all cache tests**

```bash
cd kotodama && python -m pytest tests/test_cache.py -v
```

Expected: all PASSED (8 tests total)

- [ ] **Step 5: Commit**

```bash
git add kotodama/cache.py kotodama/tests/test_cache.py
git commit -m "feat: add binary image cache to cache.py"
```

---

## Task 4: /fortune/image.png Route

**Files:**
- Modify: `kotodama/app.py`
- Modify: `kotodama/tests/test_app.py`

- [ ] **Step 1: Write failing tests**

Append to `kotodama/tests/test_app.py`:

```python
def test_fortune_image_without_session_returns_404(client):
    resp = client.get("/fortune/image.png")
    assert resp.status_code == 404


def test_fortune_image_with_session_returns_png(client):
    with client.session_transaction() as sess:
        sess["sei"] = "田中"
        sess["mei"] = "花"
        sess["yomi"] = "たなか はな"
        sess["region"] = "東京"

    fake_png = b"\x89PNG\r\n\x1a\nfakedata"

    with patch("app.get_cached_image", return_value=None), \
         patch("app.get_cached", return_value=SAMPLE_FORTUNE), \
         patch("app.get_today_stats", return_value=SAMPLE_STATS), \
         patch("app.generate_fortune_image", return_value=fake_png), \
         patch("app.set_cached_image", return_value=None):
        resp = client.get("/fortune/image.png")

    assert resp.status_code == 200
    assert resp.content_type == "image/png"
    assert resp.data == fake_png


def test_fortune_image_returns_cached_png(client):
    with client.session_transaction() as sess:
        sess["sei"] = "田中"
        sess["mei"] = "花"
        sess["yomi"] = "たなか はな"
        sess["region"] = "東京"

    cached_png = b"\x89PNG\r\n\x1a\ncacheddata"

    with patch("app.get_cached_image", return_value=cached_png), \
         patch("app.get_today_stats", return_value=SAMPLE_STATS):
        resp = client.get("/fortune/image.png")

    assert resp.status_code == 200
    assert resp.data == cached_png
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd kotodama && python -m pytest tests/test_app.py -v -k "image"
```

Expected: FAILED (route not defined)

- [ ] **Step 3: Add imports and route to `kotodama/app.py`**

Add to imports at top of `kotodama/app.py`:
```python
from flask import Flask, Response, abort, redirect, render_template, request, session, url_for
from cache import get_cached, get_cached_image, make_cache_key, set_cached, set_cached_image
from image_generator import generate_fortune_image
```

Add route before `if __name__ == "__main__":`:
```python
@app.route("/fortune/image.png")
def fortune_image():
    if "sei" not in session:
        abort(404)

    sei = session["sei"]
    mei = session["mei"]
    region = session.get("region", "東京")

    try:
        today_stats = get_today_stats(region)
    except Exception:
        today_stats = {
            "date": "本日", "date_iso": "2000-01-01", "weekday": "本日",
            "rokuyo": "大安", "sekki": None, "is_holiday": False,
            "weather": "不明", "temperature": 20.0, "pressure": 1013.0, "humidity": 60,
        }

    image_key = make_cache_key(sei, mei, today_stats["date_iso"]) + "-image"
    cached = get_cached_image(image_key)
    if cached:
        return Response(cached, mimetype="image/png")

    fortune_data = get_cached(make_cache_key(sei, mei, today_stats["date_iso"]))
    if fortune_data is None:
        abort(404)

    png_bytes = generate_fortune_image(sei, mei, today_stats, fortune_data)
    set_cached_image(image_key, png_bytes)
    return Response(png_bytes, mimetype="image/png")
```

- [ ] **Step 4: Run tests**

```bash
cd kotodama && python -m pytest tests/test_app.py -v
```

Expected: all PASSED

- [ ] **Step 5: Commit**

```bash
git add kotodama/app.py kotodama/tests/test_app.py
git commit -m "feat: add /fortune/image.png route with PNG cache"
```

---

## Task 5: OGP Meta Tags

**Files:**
- Modify: `kotodama/templates/base.html`
- Modify: `kotodama/app.py` (fortune route)
- Modify: `kotodama/tests/test_app.py`

- [ ] **Step 1: Write failing tests**

Append to `kotodama/tests/test_app.py`:

```python
def test_fortune_page_has_ogp_tags(client):
    with client.session_transaction() as sess:
        sess["sei"] = "田中"
        sess["mei"] = "花"
        sess["yomi"] = "たなか はな"
        sess["region"] = "東京"

    with patch("app.get_cached", return_value=SAMPLE_FORTUNE), \
         patch("app.get_today_stats", return_value=SAMPLE_STATS):
        resp = client.get("/fortune")

    html = resp.data.decode("utf-8")
    assert 'property="og:title"' in html
    assert 'name="twitter:card"' in html
    assert "summary_large_image" in html
    assert "/fortune/image.png" in html


def test_register_page_has_default_ogp(client):
    resp = client.get("/register")
    html = resp.data.decode("utf-8")
    assert 'property="og:title"' in html
    assert "ことだま占い" in html
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd kotodama && python -m pytest tests/test_app.py -v -k "ogp"
```

Expected: FAILED (no OGP tags in templates)

- [ ] **Step 3: Add OGP block to `kotodama/templates/base.html`**

Insert inside `<head>` after the existing `<link rel="stylesheet">` line:

```html
  {% block ogp %}
  <meta property="og:title" content="{{ og_title | default('ことだま占い') }}">
  <meta property="og:description" content="{{ og_description | default('AIとリアルデータが紡ぐ、今日のあなたへの言霊占い') }}">
  <meta property="og:image" content="{{ og_image_url | default('') }}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{{ og_title | default('ことだま占い') }}">
  <meta name="twitter:description" content="{{ og_description | default('AIとリアルデータが紡ぐ、今日のあなたへの言霊占い') }}">
  <meta name="twitter:image" content="{{ og_image_url | default('') }}">
  {% endblock %}
```

- [ ] **Step 4: Update `fortune()` route in `kotodama/app.py` to pass OGP vars**

In the `fortune()` function, replace the final `return render_template(...)` call with:

```python
    base_url = request.url_root.rstrip("/")
    return render_template(
        "fortune.html",
        sei=sei,
        mei=mei,
        stats=today_stats,
        fortune=fortune_data,
        og_title=f"{sei}{mei}さんの今日の言霊 | ことだま占い",
        og_description=fortune_data["kotodama_analysis"][:80],
        og_image_url=f"{base_url}/fortune/image.png",
    )
```

- [ ] **Step 5: Run all tests**

```bash
cd kotodama && python -m pytest tests/test_app.py -v
```

Expected: all PASSED

- [ ] **Step 6: Commit**

```bash
git add kotodama/templates/base.html kotodama/app.py kotodama/tests/test_app.py
git commit -m "feat: add OGP/Twitter card meta tags"
```

---

## Task 6: Popular Names Data

**Files:**
- Create: `kotodama/popular_names.py`
- Create: `kotodama/tests/test_popular_names.py`

- [ ] **Step 1: Write failing tests**

Create `kotodama/tests/test_popular_names.py`:

```python
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd kotodama && python -m pytest tests/test_popular_names.py -v
```

Expected: ImportError

- [ ] **Step 3: Create `kotodama/popular_names.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
cd kotodama && python -m pytest tests/test_popular_names.py -v
```

Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
git add kotodama/popular_names.py kotodama/tests/test_popular_names.py
git commit -m "feat: add popular_names with 50 entries"
```

---

## Task 7: /name/<mei> Route + name_page.html Template

**Files:**
- Modify: `kotodama/app.py`
- Create: `kotodama/templates/name_page.html`
- Modify: `kotodama/tests/test_app.py`

- [ ] **Step 1: Write failing tests**

Append to `kotodama/tests/test_app.py`:

```python
def test_name_page_known_name_returns_200(client):
    resp = client.get("/name/さくら")
    assert resp.status_code == 200
    body = resp.data.decode("utf-8")
    assert "桜" in body
    assert "今すぐ" in body


def test_name_page_unknown_name_returns_404(client):
    resp = client.get("/name/ぞんざい")
    assert resp.status_code == 404


def test_name_page_has_ogp_title(client):
    resp = client.get("/name/さくら")
    html = resp.data.decode("utf-8")
    assert "言霊占い" in html
    assert 'property="og:title"' in html


def test_name_page_has_cta_link(client):
    resp = client.get("/name/さくら")
    html = resp.data.decode("utf-8")
    assert url_for_register := "/register" in html
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd kotodama && python -m pytest tests/test_app.py -v -k "name_page"
```

Expected: FAILED

- [ ] **Step 3: Add name_page route to `kotodama/app.py`**

Add import at top of app.py:
```python
from popular_names import get_name_entry, get_related_names
from name_analyzer import analyze_name
```

Add route before `if __name__ == "__main__":`:
```python
@app.route("/name/<mei>")
def name_page(mei: str):
    entry = get_name_entry(mei)
    if entry is None:
        abort(404)

    analysis = analyze_name("", entry["kanji"], mei)
    related  = get_related_names(mei, count=5)
    base_url = request.url_root.rstrip("/")

    mei_meanings_str = "・".join(analysis["mei_meanings"][:3])
    og_desc = f"{mei_meanings_str} の意味を持つ「{entry['kanji']}」。言霊キーワードと今日の運勢を無料でチェック。"

    return render_template(
        "name_page.html",
        name=entry,
        analysis=analysis,
        related=related,
        og_title=f"「{entry['kanji']}」の言霊占い — 名前に宿る意味と今日の運勢 | ことだま占い",
        og_description=og_desc,
        og_image_url="",
    )
```

- [ ] **Step 4: Create `kotodama/templates/name_page.html`**

```html
{% extends "base.html" %}
{% block title %}「{{ name.kanji }}」の言霊占い — 名前に宿る意味と今日の運勢 | ことだま占い{% endblock %}
{% block ogp %}
<meta property="og:title" content="{{ og_title }}">
<meta property="og:description" content="{{ og_description }}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{{ og_title }}">
<meta name="twitter:description" content="{{ og_description }}">
{% endblock %}
{% block content %}
<div class="container">

  <!-- Hero -->
  <div class="app-header">
    <div class="app-logo">🔮</div>
    <div class="app-name">「{{ name.kanji }}」の言霊</div>
    <div class="app-tagline">{{ name.mei }}（{{ name.kanji }}）— 名前に宿る意味と言霊</div>
  </div>

  <!-- Kanji analysis -->
  <div class="card">
    <div class="card-title">🌸 言霊分析</div>
    <div style="font-size:36px;font-weight:bold;color:#c2185b;margin-bottom:6px">{{ name.kanji }}</div>
    <div style="font-size:13px;color:#888;margin-bottom:10px">総画数: {{ analysis.total_strokes }}画</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">
      {% for kw in analysis.personality_keywords %}
      <span class="data-chip">{{ kw }}</span>
      {% endfor %}
    </div>
    <div style="font-size:13px;color:#555;line-height:1.9">
      {% for meaning in analysis.mei_meanings %}
      <span>{{ meaning }}</span>{% if not loop.last %} ・ {% endif %}
      {% endfor %}
    </div>
  </div>

  <!-- Score preview (static 3 stars) -->
  <div class="card">
    <div class="card-title">📊 今日の運勢プレビュー</div>
    <div class="stars-row">
      {% for label in ["総合", "恋愛", "仕事", "金運"] %}
      <div class="star-item">
        <div class="label">{{ label }}</div>
        <div class="stars">⭐⭐⭐</div>
      </div>
      {% endfor %}
    </div>
    <p style="text-align:center;font-size:11px;color:#aaa;margin-top:10px">
      ※ 名前を入力すると今日の正確な運勢が出ます
    </p>
  </div>

  <!-- CTA -->
  <a href="{{ url_for('register') }}" style="text-decoration:none">
    <button class="btn-primary">✨ 今すぐ「{{ name.kanji }}」の言霊を占う →</button>
  </a>

  <!-- Related names -->
  <div class="card" style="margin-top:14px">
    <div class="card-title">🔮 他の名前の言霊も見る</div>
    <div style="display:flex;flex-wrap:wrap;gap:8px">
      {% for rel in related %}
      <a href="{{ url_for('name_page', mei=rel.mei) }}"
         style="text-decoration:none">
        <span class="data-chip" style="font-size:12px;padding:5px 12px;cursor:pointer">
          {{ rel.kanji }}
        </span>
      </a>
      {% endfor %}
    </div>
  </div>

  <div class="footer">
    <div>
      <a href="{{ url_for('privacy') }}">プライバシーポリシー</a>
      <a href="{{ url_for('disclaimer') }}">免責事項</a>
    </div>
    <div style="margin-top:8px">© 2026 ことだま占い — AIによる娯楽コンテンツです</div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Run all tests**

```bash
cd kotodama && python -m pytest tests/test_app.py -v
```

Expected: all PASSED

- [ ] **Step 6: Commit**

```bash
git add kotodama/app.py kotodama/templates/name_page.html kotodama/tests/test_app.py
git commit -m "feat: add /name/<mei> SEO name pages"
```

---

## Task 8: /sitemap.xml Route

**Files:**
- Modify: `kotodama/app.py`
- Create: `kotodama/templates/sitemap.xml`
- Modify: `kotodama/tests/test_app.py`

- [ ] **Step 1: Write failing tests**

Append to `kotodama/tests/test_app.py`:

```python
def test_sitemap_returns_xml(client):
    resp = client.get("/sitemap.xml")
    assert resp.status_code == 200
    assert "xml" in resp.content_type
    body = resp.data.decode("utf-8")
    assert "<urlset" in body
    assert "/name/" in body


def test_sitemap_contains_all_50_names(client):
    resp = client.get("/sitemap.xml")
    body = resp.data.decode("utf-8")
    assert body.count("<loc>") >= 51  # 1 root + 50 name pages
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd kotodama && python -m pytest tests/test_app.py -v -k "sitemap"
```

Expected: FAILED

- [ ] **Step 3: Add sitemap route to `kotodama/app.py`**

Add import at top (if not already present):
```python
from flask import Flask, Response, abort, redirect, render_template, request, session, url_for
```

Add route:
```python
@app.route("/sitemap.xml")
def sitemap():
    from popular_names import POPULAR_NAMES
    base_url = request.url_root.rstrip("/")
    xml = render_template("sitemap.xml", base_url=base_url, names=POPULAR_NAMES)
    return Response(xml, mimetype="application/xml")
```

- [ ] **Step 4: Create `kotodama/templates/sitemap.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{{ base_url }}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  {% for name in names %}
  <url>
    <loc>{{ base_url }}/name/{{ name.mei }}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  {% endfor %}
</urlset>
```

- [ ] **Step 5: Run all tests**

```bash
cd kotodama && python -m pytest tests/test_app.py -v
```

Expected: all PASSED

- [ ] **Step 6: Commit**

```bash
git add kotodama/app.py kotodama/templates/sitemap.xml kotodama/tests/test_app.py
git commit -m "feat: add /sitemap.xml with all name pages"
```

---

## Task 9: fortune.html 画像保存ボタン + Final Test Run

**Files:**
- Modify: `kotodama/templates/fortune.html`

- [ ] **Step 1: Add 📸 image save button to `kotodama/templates/fortune.html`**

Find the share-row div (lines around `<div class="share-row">`). Add a third button:

Replace:
```html
  <!-- Share -->
  <div class="share-row">
    <button class="btn-share btn-share-x" id="shareX">𝕏 シェア</button>
    <button class="btn-share btn-share-line" id="shareLine">LINE シェア</button>
  </div>
```

With:
```html
  <!-- Share -->
  <div class="share-row">
    <button class="btn-share btn-share-x" id="shareX">𝕏 シェア</button>
    <button class="btn-share btn-share-line" id="shareLine">LINE シェア</button>
  </div>
  <a href="{{ url_for('fortune_image') }}" download="kotodama-fortune.png"
     style="text-decoration:none;display:block;margin-bottom:8px">
    <button class="btn-share" style="width:100%;background:linear-gradient(135deg,#7b1fa2,#1565c0);color:white">
      📸 画像を保存する（インスタ・X用）
    </button>
  </a>
```

- [ ] **Step 2: Run the full test suite**

```bash
cd kotodama && python -m pytest -v
```

Expected: all PASSED (40+ tests)

- [ ] **Step 3: Commit**

```bash
git add kotodama/templates/fortune.html
git commit -m "feat: add image save button to fortune page"
```

---

## Post-Deploy Checklist

- [ ] Submit `https://your-domain.com/sitemap.xml` to Google Search Console
- [ ] Share `/name/さくら` on X to verify Twitter Card preview
- [ ] Check `/fortune/image.png` URL in the Twitter Card Validator (`cards-dev.twitter.com/validator`)
- [ ] Verify OGP tags with [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)
