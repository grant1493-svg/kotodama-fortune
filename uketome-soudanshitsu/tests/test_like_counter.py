import json
from unittest.mock import patch, MagicMock

from like_counter import extract_note_key, fetch_like_count


class TestExtractNoteKey:
    """Test URL parsing to extract note key."""

    def test_extract_note_key_from_valid_url(self):
        """Extract key from standard note.com article URL."""
        url = "https://note.com/soudan_labo/n/ned76d2659fb1"
        assert extract_note_key(url) == "ned76d2659fb1"

    def test_extract_note_key_handles_trailing_slash(self):
        """Extract key even with trailing slash."""
        url = "https://note.com/soudan_labo/n/abc123/"
        assert extract_note_key(url) == "abc123"

    def test_extract_note_key_returns_none_on_invalid_url(self):
        """Return None for URLs that don't match the expected pattern."""
        assert extract_note_key("https://note.com/soudan_labo") is None
        assert extract_note_key("https://example.com/n/abc123") is None
        assert extract_note_key("not a url") is None

    def test_extract_note_key_returns_none_on_missing_key(self):
        """Return None if URL lacks the /n/ segment."""
        url = "https://note.com/soudan_labo/"
        assert extract_note_key(url) is None


class TestFetchLikeCount:
    """Test fetching like counts from the note.com API."""

    def test_fetch_like_count_parses_successful_api_response(self):
        """Successfully parse like_count from v3 API response."""
        api_response = {
            "data": {
                "status": "published",
                "key": "ned76d2659fb1",
                "like_count": 42,
                "is_liked": False,
                "anonymous_like_count": 0,
            }
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(api_response)
        mock_response.raise_for_status = MagicMock()

        with patch("like_counter.requests.get", return_value=mock_response):
            result = fetch_like_count("https://note.com/soudan_labo/n/ned76d2659fb1")
            assert result == 42

    def test_fetch_like_count_returns_none_on_network_error(self):
        """Return None on network errors."""
        with patch("like_counter.requests.get", side_effect=Exception("network down")):
            result = fetch_like_count("https://note.com/soudan_labo/n/abc123")
            assert result is None

    def test_fetch_like_count_returns_none_on_invalid_key_url(self):
        """Return None if URL doesn't contain a valid note key."""
        result = fetch_like_count("https://note.com/soudan_labo")
        assert result is None

    def test_fetch_like_count_returns_none_on_http_error(self):
        """Return None when API returns an error (e.g., 400, 404)."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")

        with patch("like_counter.requests.get", return_value=mock_response):
            result = fetch_like_count("https://note.com/soudan_labo/n/unknown_key")
            assert result is None

    def test_fetch_like_count_returns_none_on_invalid_json(self):
        """Return None if API response is not valid JSON."""
        mock_response = MagicMock()
        mock_response.text = "not valid json"
        mock_response.raise_for_status = MagicMock()

        with patch("like_counter.requests.get", return_value=mock_response):
            result = fetch_like_count("https://note.com/soudan_labo/n/abc123")
            assert result is None

    def test_fetch_like_count_returns_none_on_missing_data_key(self):
        """Return None if response lacks 'data' key (e.g., error response)."""
        api_response = {"error": {"code": "not_found", "message": "Article not found"}}
        mock_response = MagicMock()
        mock_response.text = json.dumps(api_response)
        mock_response.raise_for_status = MagicMock()

        with patch("like_counter.requests.get", return_value=mock_response):
            result = fetch_like_count("https://note.com/soudan_labo/n/unknown")
            assert result is None

    def test_fetch_like_count_returns_none_on_missing_like_count_key(self):
        """Return None if response data lacks 'like_count' key."""
        api_response = {"data": {"key": "abc123", "status": "published"}}
        mock_response = MagicMock()
        mock_response.text = json.dumps(api_response)
        mock_response.raise_for_status = MagicMock()

        with patch("like_counter.requests.get", return_value=mock_response):
            result = fetch_like_count("https://note.com/soudan_labo/n/abc123")
            assert result is None
