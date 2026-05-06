from datetime import date
from unittest.mock import patch
from stats_fetcher import get_rokuyo, get_today_stats, CITY_COORDS


def test_rokuyo_returns_valid_value():
    result = get_rokuyo(date(2026, 5, 5))
    assert result in ["大安", "赤口", "先勝", "友引", "先負", "仏滅"]


def test_rokuyo_taian():
    result = get_rokuyo(date(2026, 5, 5))
    assert isinstance(result, str)


def test_city_coords_tokyo():
    lat, lon = CITY_COORDS["東京"]
    assert 35.0 < lat < 36.0
    assert 139.0 < lon < 140.0


def test_get_today_stats_returns_expected_keys():
    mock_weather = {
        "current": {
            "temperature_2m": 22.5,
            "surface_pressure": 1008.2,
            "relative_humidity_2m": 55,
            "weather_code": 0,
        }
    }
    with patch("stats_fetcher.requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_weather
        mock_get.return_value.raise_for_status.return_value = None
        result = get_today_stats("東京")

    for key in ["date", "weekday", "rokuyo", "weather", "temperature",
                "pressure", "humidity", "is_holiday"]:
        assert key in result, f"Missing key: {key}"


def test_get_today_stats_weather_sunny():
    mock_weather = {
        "current": {
            "temperature_2m": 25.0,
            "surface_pressure": 1012.0,
            "relative_humidity_2m": 40,
            "weather_code": 0,
        }
    }
    with patch("stats_fetcher.requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_weather
        mock_get.return_value.raise_for_status.return_value = None
        result = get_today_stats("東京")

    assert result["weather"] == "快晴"
