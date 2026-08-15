import json
from unittest.mock import patch, MagicMock

from like_counter import extract_like_count, fetch_like_count


def _html_with_next_data(payload: dict) -> str:
    return (
        "<html><body>"
        f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script>'
        "</body></html>"
    )


def test_extract_like_count_finds_top_level_key():
    html = _html_with_next_data({"props": {"pageProps": {"likeCount": 42}}})
    assert extract_like_count(html) == 42


def test_extract_like_count_finds_snake_case_key():
    html = _html_with_next_data({"data": {"article": {"like_count": 7}}})
    assert extract_like_count(html) == 7


def test_extract_like_count_returns_none_when_no_next_data():
    assert extract_like_count("<html><body>no data here</body></html>") is None


def test_extract_like_count_returns_none_on_invalid_json():
    html = '<script id="__NEXT_DATA__" type="application/json">{not valid json}</script>'
    assert extract_like_count(html) is None


def test_extract_like_count_returns_none_when_key_absent():
    html = _html_with_next_data({"props": {"pageProps": {"title": "記事タイトル"}}})
    assert extract_like_count(html) is None


def test_fetch_like_count_returns_none_on_network_error():
    with patch("like_counter.requests.get", side_effect=Exception("network down")):
        assert fetch_like_count("https://note.com/soudan_labo/n/xxxx") is None


def test_fetch_like_count_parses_successful_response():
    html = _html_with_next_data({"likeCount": 15})
    mock_response = MagicMock()
    mock_response.text = html
    mock_response.raise_for_status = MagicMock()
    with patch("like_counter.requests.get", return_value=mock_response):
        assert fetch_like_count("https://note.com/soudan_labo/n/xxxx") == 15
