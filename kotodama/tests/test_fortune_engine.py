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


def test_parse_fortune_response_missing_key_raises():
    bad = json.dumps({"kotodama_analysis": "x", "today_message": "y"})  # missing keys
    with pytest.raises(ValueError, match="missing keys"):
        parse_fortune_response(bad)


def test_generate_fortune_calls_claude_and_returns_dict(monkeypatch):
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=VALID_JSON)]
    mock_client.messages.create.return_value = mock_message

    with patch("fortune_engine.anthropic.Anthropic", return_value=mock_client):
        result = generate_fortune(SAMPLE_NAME, SAMPLE_STATS)

    assert result["scores"]["overall"] == 4
    assert "today_message" in result
