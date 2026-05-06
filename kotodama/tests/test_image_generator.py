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
