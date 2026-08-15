"""うけとめ相談室 — ロゴ/キャッチコピーの透過オーバーレイ生成

背景写真や記事見出しとは独立して管理する。ブランド表記を変えたいときは
このスクリプトの再実行だけで済み、背景写真の再生成は不要。
使い方: python generate_logo_overlay.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from generate_thumbnail import _ensure_font

WIDTH, HEIGHT = 1280, 670
_BRAND = "うけとめ相談室"
_CATCHPHRASE = "精神科医×心理学者×脳科学者"
_PANEL = (20, 20, 30, 160)
_WHITE = (255, 255, 255, 255)


def generate_logo_overlay(output_path: Path) -> Path:
    font_path = str(_ensure_font())
    f_brand = ImageFont.truetype(font_path, 30)
    f_catch = ImageFont.truetype(font_path, 20)

    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pill_x, pill_y = 40, HEIGHT - 110
    draw.rounded_rectangle([pill_x, pill_y, pill_x + 260, pill_y + 46], radius=23, fill=_PANEL)
    draw.text((pill_x + 20, pill_y + 8), _BRAND, font=f_brand, fill=_WHITE)

    catch_y = pill_y + 54
    draw.rounded_rectangle([pill_x, catch_y, pill_x + 330, catch_y + 34], radius=17, fill=_PANEL)
    draw.text((pill_x + 16, catch_y + 6), _CATCHPHRASE, font=f_catch, fill=_WHITE)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, format="PNG")
    return output_path


def main():
    out_path = Path(__file__).parent / "static" / "logo_overlay.png"
    generate_logo_overlay(out_path)
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
