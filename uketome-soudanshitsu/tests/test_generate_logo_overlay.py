from pathlib import Path

import pytest
from PIL import Image

from generate_thumbnail import FONT_PATH

requires_font = pytest.mark.skipif(
    not FONT_PATH.exists(),
    reason="Font not present — run: cd uketome-soudanshitsu && python -c \"from generate_thumbnail import _ensure_font; _ensure_font()\"",
)


@requires_font
def test_generate_logo_overlay_creates_rgba_png_with_correct_size(tmp_path):
    from generate_logo_overlay import generate_logo_overlay

    output_path = tmp_path / "logo_overlay.png"
    generate_logo_overlay(output_path)
    img = Image.open(output_path)
    assert img.format == "PNG"
    assert img.mode == "RGBA"
    assert img.size == (1280, 670)


@requires_font
def test_generate_logo_overlay_top_right_corner_is_transparent(tmp_path):
    from generate_logo_overlay import generate_logo_overlay

    output_path = tmp_path / "logo_overlay.png"
    generate_logo_overlay(output_path)
    img = Image.open(output_path)
    r, g, b, a = img.getpixel((10, 10))
    assert a == 0
