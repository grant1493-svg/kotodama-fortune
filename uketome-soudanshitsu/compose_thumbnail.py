"""うけとめ相談室 — 背景写真 + ロゴオーバーレイ + 見出しの合成

ad-designerが生成した背景写真(またはgenerate_thumbnail.pyのグラデーション背景)に
logo_overlay.pngと当日の見出しを重ねて最終サムネイル(1280x670)を作る。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from generate_thumbnail import _ensure_font, _gradient_image, _wrap_text

WIDTH, HEIGHT = 1280, 670
_WHITE = (255, 255, 255)


def _load_background(background_path: Path | None, color_start: tuple, color_end: tuple) -> Image.Image:
    if background_path is not None and background_path.exists():
        img = Image.open(background_path).convert("RGB")
    else:
        img = _gradient_image(color_start, color_end)
    if img.size != (WIDTH, HEIGHT):
        img = img.resize((WIDTH, HEIGHT))
    return img


def compose_thumbnail(
    title: str,
    color_start: tuple,
    color_end: tuple,
    output_path: Path,
    background_path: Path | None = None,
    logo_overlay_path: Path | None = None,
) -> Path:
    background = _load_background(background_path, color_start, color_end).convert("RGBA")

    font_path = str(_ensure_font())
    f_title = ImageFont.truetype(font_path, 50)
    draw = ImageDraw.Draw(background)
    lines = _wrap_text(title, 15)[:3]
    y = 60
    for line in lines:
        draw.text((60, y), line, font=f_title, fill=_WHITE)
        y += 64

    if logo_overlay_path is not None and logo_overlay_path.exists():
        overlay = Image.open(logo_overlay_path).convert("RGBA")
        if overlay.size != background.size:
            overlay = overlay.resize(background.size)
        background = Image.alpha_composite(background, overlay)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    background.convert("RGB").save(output_path, format="PNG", optimize=True)
    return output_path
