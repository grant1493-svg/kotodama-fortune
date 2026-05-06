from datetime import date
import requests
import jpholiday

CITY_COORDS: dict[str, tuple[float, float]] = {
    "東京": (35.6895, 139.6917),
    "大阪": (34.6937, 135.5023),
    "名古屋": (35.1815, 136.9066),
    "札幌": (43.0618, 141.3545),
    "福岡": (33.5904, 130.4017),
    "仙台": (38.2688, 140.8721),
    "広島": (34.3853, 132.4553),
    "京都": (35.0116, 135.7681),
    "神戸": (34.6901, 135.1956),
    "横浜": (35.4478, 139.6425),
}
_DEFAULT_COORDS = (35.6895, 139.6917)  # 東京

_ROKUYO = ["大安", "赤口", "先勝", "友引", "先負", "仏滅"]
_WEEKDAYS = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]

# Approximate 二十四節気 dates (month, day) for 2026
_SEKKI_2026: dict[tuple[int, int], str] = {
    (1, 6): "小寒", (1, 20): "大寒",
    (2, 4): "立春", (2, 19): "雨水",
    (3, 6): "啓蟄", (3, 20): "春分",
    (4, 5): "清明", (4, 20): "穀雨",
    (5, 6): "立夏", (5, 21): "小満",
    (6, 6): "芒種", (6, 21): "夏至",
    (7, 7): "小暑", (7, 23): "大暑",
    (8, 7): "立秋", (8, 23): "処暑",
    (9, 8): "白露", (9, 23): "秋分",
    (10, 8): "寒露", (10, 23): "霜降",
    (11, 7): "立冬", (11, 22): "小雪",
    (12, 7): "大雪", (12, 22): "冬至",
}

_WMO_WEATHER: dict[int, str] = {
    0: "快晴", 1: "晴れ", 2: "やや曇り", 3: "曇り",
    45: "霧", 48: "霧",
    51: "小雨", 53: "雨", 55: "強雨",
    61: "雨", 63: "雨", 65: "大雨",
    71: "雪", 73: "雪", 75: "大雪",
    80: "にわか雨", 81: "にわか雨", 82: "強にわか雨",
    95: "雷雨", 96: "雷雨", 99: "雷雨",
}


def get_rokuyo(d: date) -> str:
    """Simplified 六曜 using (month + day) % 6."""
    return _ROKUYO[(d.month + d.day) % 6]


def get_sekki(d: date) -> str | None:
    """Return 二十四節気 name if today matches, else None."""
    return _SEKKI_2026.get((d.month, d.day))


def _wmo_to_japanese(code: int) -> str:
    return _WMO_WEATHER.get(code, "曇り")


def get_today_stats(region: str) -> dict:
    """Fetch weather + calendar stats for today."""
    today = date.today()
    lat, lon = CITY_COORDS.get(region, _DEFAULT_COORDS)

    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,surface_pressure,relative_humidity_2m,weather_code",
            "timezone": "Asia/Tokyo",
            "forecast_days": 1,
        },
        timeout=10,
    )
    resp.raise_for_status()
    current = resp.json()["current"]

    return {
        "date": today.strftime("%Y年%m月%d日"),
        "date_iso": today.isoformat(),
        "weekday": _WEEKDAYS[today.weekday()],
        "rokuyo": get_rokuyo(today),
        "sekki": get_sekki(today),
        "is_holiday": bool(jpholiday.is_holiday(today)),
        "weather": _wmo_to_japanese(int(current["weather_code"])),
        "temperature": round(float(current["temperature_2m"]), 1),
        "pressure": round(float(current["surface_pressure"]), 1),
        "humidity": int(current["relative_humidity_2m"]),
    }
