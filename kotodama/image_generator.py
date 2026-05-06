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
    """Return 1200x630 PNG bytes of the dark fortune card."""
    font_path = str(_ensure_font())
    f_xs  = ImageFont.truetype(font_path, 20)
    f_sm  = ImageFont.truetype(font_path, 26)
    f_md  = ImageFont.truetype(font_path, 34)
    f_lg  = ImageFont.truetype(font_path, 50)

    img  = _gradient_image()
    draw = ImageDraw.Draw(img)

    # Top bar
    draw.text((60, 42), "ことだま占い", font=f_sm, fill=_PURPLE)
    date_str = f"{stats['date']}  {stats['rokuyo']}"
    if stats.get("sekki"):
        date_str += f"  {stats['sekki']}"
    draw.text((1140, 42), date_str, font=f_xs, fill=_GRAY, anchor="ra")

    # Name
    draw.text((60, 105), f"{sei}{mei} さんの言霊", font=f_lg, fill=_WHITE)

    # Divider
    draw.line([(60, 178), (1140, 178)], fill=(80, 60, 100), width=1)

    # Scores
    score_items = [
        ("総合", "overall"), ("恋愛", "love"), ("仕事", "work"), ("金運", "money")
    ]
    for i, (label, key) in enumerate(score_items):
        x = 60 + i * 270
        score = fortune["scores"][key]
        draw.text((x, 195), label, font=f_xs, fill=_GRAY)
        stars = "★" * score + "☆" * (5 - score)
        draw.text((x, 220), stars, font=f_md, fill=_PURPLE)

    # Analysis accent bar + text
    draw.rectangle([(60, 298), (66, 378)], fill=_PINK)
    analysis = fortune["kotodama_analysis"][:55]
    for i, line in enumerate(_wrap_text(analysis, 26)[:3]):
        draw.text((82, 302 + i * 34), line, font=f_sm, fill=(230, 210, 245))

    # Lucky strip
    lucky = fortune["lucky"]
    lucky_text = (
        f"色: {lucky['color']}   "
        f"時間: {lucky['time']}   "
        f"場所: {lucky['place']}   "
        f"数字: {lucky['number']}"
    )
    draw.text((60, 415), lucky_text, font=f_sm, fill=_PURPLE)

    # URL
    draw.text((1140, 592), "kotodama-fortune.com", font=f_xs, fill=_DIMGRAY, anchor="ra")

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
