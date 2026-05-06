import json
import re
import anthropic

_SYSTEM_PROMPT = """あなたは「ことだま占い師」です。名前の言霊（ことだま）と今日の統計データをもとに占い結果を生成します。
温かく親しみやすい文体で、20〜40代の女性に向けて語りかけてください。
必ず以下のJSON形式のみで返答してください。前後に説明文は不要です。

{
  "kotodama_analysis": "名前の言霊分析（60〜80字）",
  "today_message": "今日のあなたへのメッセージ（80〜100字）",
  "morning_message": "朝イチ限定の一言（40〜55字、朝の清々しさを表現）",
  "scores": {"overall": 1〜5の整数, "love": 1〜5の整数, "work": 1〜5の整数, "money": 1〜5の整数},
  "lucky": {"color": "色名", "time": "時間帯", "place": "場所名", "number": 1〜9の整数}
}"""


def build_prompt(name_analysis: dict, today_stats: dict) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for Claude."""
    phonetic_label = "開放的・社交的" if name_analysis["phonetic_type"] == "open" else "内省的・繊細"
    sekki_text = f"・節気: {today_stats['sekki']}" if today_stats.get("sekki") else ""
    holiday_text = "（祝日）" if today_stats["is_holiday"] else ""

    user = f"""名前: {name_analysis['sei']}{name_analysis['mei']}（{name_analysis['yomi']}）
総画数: {name_analysis['total_strokes']}画
名前の意味: {', '.join(name_analysis['mei_meanings'][:3])}
性格キーワード: {', '.join(name_analysis['personality_keywords'])}
音の印象: {phonetic_label}

今日のデータ:
- 日付: {today_stats['date']} {today_stats['weekday']}{holiday_text}
- 六曜: {today_stats['rokuyo']}{sekki_text}
- 天気: {today_stats['weather']}
- 気温: {today_stats['temperature']}°C
- 気圧: {today_stats['pressure']}hPa
- 湿度: {today_stats['humidity']}%"""

    return _SYSTEM_PROMPT, user


_REQUIRED_KEYS = {"kotodama_analysis", "today_message", "morning_message", "scores", "lucky"}
_REQUIRED_SCORE_KEYS = {"overall", "love", "work", "money"}
_REQUIRED_LUCKY_KEYS = {"color", "time", "place", "number"}


def _validate_fortune(data: dict) -> dict:
    """Raise ValueError if required keys are missing."""
    missing = _REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(f"Claude response missing keys: {missing}")
    missing_scores = _REQUIRED_SCORE_KEYS - data["scores"].keys()
    if missing_scores:
        raise ValueError(f"Claude response missing score keys: {missing_scores}")
    missing_lucky = _REQUIRED_LUCKY_KEYS - data["lucky"].keys()
    if missing_lucky:
        raise ValueError(f"Claude response missing lucky keys: {missing_lucky}")
    return data


def parse_fortune_response(text: str) -> dict:
    """Extract and parse JSON from Claude response. Strips markdown fences if present."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    return _validate_fortune(json.loads(cleaned))


def generate_fortune(name_analysis: dict, today_stats: dict) -> dict:
    """Call Claude API and return parsed fortune dict."""
    system_prompt, user_prompt = build_prompt(name_analysis, today_stats)
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return parse_fortune_response(message.content[0].text)
