from pathlib import Path

import pytest
from PIL import Image

from generate_thumbnail import FONT_PATH

requires_font = pytest.mark.skipif(
    not FONT_PATH.exists(),
    reason="Font not present — run: cd uketome-soudanshitsu && python -c \"from generate_thumbnail import _ensure_font; _ensure_font()\"",
)


@requires_font
def test_compose_thumbnail_without_background_uses_gradient_fallback(tmp_path):
    from compose_thumbnail import compose_thumbnail

    output_path = tmp_path / "out.png"
    compose_thumbnail(
        title="なぜ恋愛は苦しいのか",
        color_start=(240, 98, 146),
        color_end=(123, 31, 162),
        output_path=output_path,
        background_path=None,
        logo_overlay_path=None,
    )
    img = Image.open(output_path)
    assert img.format == "PNG"
    assert img.size == (1280, 670)


@requires_font
def test_compose_thumbnail_resizes_mismatched_background(tmp_path):
    from compose_thumbnail import compose_thumbnail

    bg_path = tmp_path / "bg.png"
    Image.new("RGB", (800, 400), (10, 20, 30)).save(bg_path)

    output_path = tmp_path / "out.png"
    compose_thumbnail(
        title="お金の不安、聞いてから解決",
        color_start=(255, 179, 0),
        color_end=(230, 81, 0),
        output_path=output_path,
        background_path=bg_path,
        logo_overlay_path=None,
    )
    img = Image.open(output_path)
    assert img.size == (1280, 670)


@requires_font
def test_compose_thumbnail_applies_logo_overlay(tmp_path):
    from compose_thumbnail import compose_thumbnail

    overlay_path = tmp_path / "overlay.png"
    overlay = Image.new("RGBA", (1280, 670), (0, 0, 0, 0))
    for x in range(50):
        for y in range(50):
            overlay.putpixel((x, y), (1, 2, 3, 255))
    overlay.save(overlay_path)

    output_path = tmp_path / "out.png"
    compose_thumbnail(
        title="自分を好きになれない理由",
        color_start=(126, 87, 194),
        color_end=(69, 39, 160),
        output_path=output_path,
        background_path=None,
        logo_overlay_path=overlay_path,
    )
    img = Image.open(output_path).convert("RGB")
    assert img.getpixel((10, 10)) == (1, 2, 3)
