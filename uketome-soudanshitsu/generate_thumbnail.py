"""
うけとめ相談室 — note/X投稿用サムネイル生成
使い方: python generate_thumbnail.py
articles_config.py の ARTICLES を読み、thumbnails/ 配下に1200x630のPNGを出力する。
"""
import io
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from articles_config import ARTICLES

FONT_DIR = Path(__file__).parent / "static" / "fonts"
FONT_PATH = FONT_DIR / "NotoSansJP-Bold.otf"
_FONT_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf"

WIDTH, HEIGHT = 1200, 630
_WHITE = (255, 255, 255)
_GRAY = (235, 235, 240)
_BRAND = "うけとめ相談室"


def _ensure_font() -> Path:
    if not FONT_PATH.exists():
        FONT_DIR.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(_FONT_URL, FONT_PATH)
    return FONT_PATH


def _gradient_image(start: tuple, end: tuple) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        ratio = y / (HEIGHT - 1)
        r = int(start[0] + (end[0] - start[0]) * ratio)
        g = int(start[1] + (end[1] - start[1]) * ratio)
        b = int(start[2] + (end[2] - start[2]) * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
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


def generate_thumbnail(genre_label: str, title: str, color_start: tuple, color_end: tuple, output_path: Path):
    font_path = str(_ensure_font())
    f_genre = ImageFont.truetype(font_path, 30)
    f_title = ImageFont.truetype(font_path, 54)
    f_brand = ImageFont.truetype(font_path, 24)

    img = _gradient_image(color_start, color_end)
    draw = ImageDraw.Draw(img)

    # ジャンルタグ（アクセントバー＋テキスト）
    draw.rectangle([(60, 62), (66, 100)], fill=_WHITE)
    draw.text((82, 66), genre_label, font=f_genre, fill=_WHITE)

    # タイトル（折り返し）
    lines = _wrap_text(title, 15)[:4]
    y = 190
    for line in lines:
        draw.text((60, y), line, font=f_title, fill=_WHITE)
        y += 68

    # ブランド名
    draw.text((60, HEIGHT - 70), _BRAND, font=f_brand, fill=_GRAY)
    draw.text((WIDTH - 60, HEIGHT - 70), "精神科医×心理学者×脳科学者", font=f_brand, fill=_GRAY, anchor="ra")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG", optimize=True)
    return output_path


def main():
    out_dir = Path(__file__).parent / "thumbnails"
    for key, article in ARTICLES.items():
        if not article["thumbnail_title"]:
            continue
        out_path = out_dir / f"{key}.png"
        generate_thumbnail(
            genre_label=article["genre_label"],
            title=article["thumbnail_title"],
            color_start=article["color_start"],
            color_end=article["color_end"],
            output_path=out_path,
        )
        print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
