from flask import Flask, Response, abort, redirect, render_template, request, session, url_for
from dotenv import load_dotenv
import os

from cache import get_cached, get_cached_image, make_cache_key, set_cached, set_cached_image
from fortune_engine import generate_fortune
from name_analyzer import analyze_name
from popular_names import get_name_entry, get_related_names
from stats_fetcher import get_today_stats
from image_generator import generate_fortune_image

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/")
def index():
    if "sei" in session:
        return redirect(url_for("fortune"))
    return redirect(url_for("register"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        session["sei"] = request.form["sei"].strip()
        session["mei"] = request.form["mei"].strip()
        session["yomi"] = request.form["yomi"].strip()
        session["region"] = request.form.get("region", "東京").strip()
        return redirect(url_for("fortune"))
    return render_template("register.html")


@app.route("/fortune")
def fortune():
    if "sei" not in session:
        return redirect(url_for("register"))

    sei = session["sei"]
    mei = session["mei"]
    yomi = session["yomi"]
    region = session.get("region", "東京")

    try:
        today_stats = get_today_stats(region)
    except Exception:
        today_stats = {
            "date": "本日", "date_iso": "2000-01-01", "weekday": "本日",
            "rokuyo": "大安", "sekki": None, "is_holiday": False,
            "weather": "不明", "temperature": 20.0, "pressure": 1013.0, "humidity": 60,
        }

    cache_key = make_cache_key(sei, mei, today_stats["date_iso"])
    fortune_data = get_cached(cache_key)

    if fortune_data is None:
        try:
            name_analysis = analyze_name(sei, mei, yomi)
            fortune_data = generate_fortune(name_analysis, today_stats)
            set_cached(cache_key, fortune_data)
        except Exception:
            fortune_data = {
                "kotodama_analysis": f"「{mei}」という名前には深い意味が宿っています。",
                "today_message": "今日も素晴らしい一日になりますように。あなたの笑顔が周りを明るくします🌸",
                "morning_message": "朝の光とともに、新しい一日が始まります。",
                "scores": {"overall": 3, "love": 3, "work": 3, "money": 3},
                "lucky": {"color": "ピンク", "time": "午前中", "place": "お気に入りの場所", "number": 7},
            }

    base_url = request.url_root.rstrip("/")
    return render_template(
        "fortune.html",
        sei=sei,
        mei=mei,
        stats=today_stats,
        fortune=fortune_data,
        og_title=f"{sei}{mei}さんの今日の言霊 | ことだま占い",
        og_description=fortune_data["kotodama_analysis"][:80],
        og_image_url=f"{base_url}/fortune/image.png",
    )


@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("register"))


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/tokushoho")
def tokushoho():
    return render_template("tokushoho.html")


@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")


@app.route("/fortune/image.png")
def fortune_image():
    if "sei" not in session:
        abort(404)

    sei = session["sei"]
    mei = session["mei"]
    region = session.get("region", "東京")

    try:
        today_stats = get_today_stats(region)
    except Exception:
        today_stats = {
            "date": "本日", "date_iso": "2000-01-01", "weekday": "本日",
            "rokuyo": "大安", "sekki": None, "is_holiday": False,
            "weather": "不明", "temperature": 20.0, "pressure": 1013.0, "humidity": 60,
        }

    image_key = make_cache_key(sei, mei, today_stats["date_iso"]) + "-image"
    cached = get_cached_image(image_key)
    if cached:
        return Response(cached, mimetype="image/png")

    fortune_data = get_cached(make_cache_key(sei, mei, today_stats["date_iso"]))
    if fortune_data is None:
        abort(404)

    png_bytes = generate_fortune_image(sei, mei, today_stats, fortune_data)
    set_cached_image(image_key, png_bytes)
    return Response(png_bytes, mimetype="image/png")


@app.route("/couple", methods=["GET", "POST"])
def couple():
    if request.method == "GET":
        return render_template("couple.html")

    name1 = request.form.get("name1", "").strip()
    name2 = request.form.get("name2", "").strip()
    if not name1 or not name2:
        return render_template("couple.html", error="お二人の名前を入力してください")

    import hashlib, anthropic as _anthropic
    from stats_fetcher import get_today_stats as _gts
    try:
        stats = _gts("東京")
    except Exception:
        stats = {"date": "本日", "date_iso": "2000-01-01", "rokuyo": "大安", "weather": "晴れ"}

    cache_key = "couple:" + hashlib.sha256(f"{name1}{name2}{stats['date_iso']}".encode()).hexdigest()
    result = get_cached(cache_key)

    if result is None:
        try:
            client = _anthropic.Anthropic()
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                system="""あなたは「ことだま相性占い師」です。2人の名前の言霊から相性を占います。
必ず以下のJSON形式のみで返答してください。前後に説明文は不要です。
{
  "score": 1〜100の整数,
  "label": "相性を一言で表すフレーズ（10字以内）",
  "message": "2人へのメッセージ（80〜100字）",
  "lucky_action": "2人が今日やると良いこと（30字以内）"
}""",
                messages=[{"role": "user", "content": f"名前1: {name1}\n名前2: {name2}\n今日の日付: {stats['date']}\n六曜: {stats['rokuyo']}"}],
            )
            import json as _json, re as _re
            text = msg.content[0].text
            cleaned = _re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=_re.MULTILINE)
            result = _json.loads(cleaned)
            set_cached(cache_key, result)
        except Exception:
            result = {
                "score": 75,
                "label": "心が通じ合う縁",
                "message": f"「{name1}」と「{name2}」、2人の言霊はとても良い響き合いをしています。お互いを大切にすることで、さらに素敵な関係になれるでしょう🌸",
                "lucky_action": "一緒にお茶を飲む",
            }

    share_text = f"「{name1}」×「{name2}」の言霊相性は{result['score']}点！{result['label']} #ことだま占い"
    return render_template("couple.html", name1=name1, name2=name2, result=result, share_text=share_text)


@app.route("/robots.txt")
def robots():
    base_url = request.url_root.rstrip("/")
    content = f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n"
    return Response(content, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    import datetime
    from popular_names import POPULAR_NAMES
    base_url = request.url_root.rstrip("/")
    today = datetime.date.today().isoformat()
    xml = render_template("sitemap.xml", base_url=base_url, names=POPULAR_NAMES, today=today)
    return Response(xml, mimetype="application/xml")


@app.route("/name/<mei>")
def name_page(mei: str):
    entry = get_name_entry(mei)
    if entry is None:
        abort(404)

    analysis = analyze_name("", entry["kanji"], mei)
    related  = get_related_names(mei, count=5)

    mei_meanings_str = "・".join(analysis["mei_meanings"][:3])
    og_desc = f"{mei_meanings_str} の意味を持つ「{entry['kanji']}」。言霊キーワードと今日の運勢を無料でチェック。"

    return render_template(
        "name_page.html",
        name=entry,
        analysis=analysis,
        related=related,
        og_title=f"「{entry['kanji']}」の言霊占い — 名前に宿る意味と今日の運勢 | ことだま占い",
        og_description=og_desc,
        og_image_url="",
    )


if __name__ == "__main__":
    app.run(debug=True)
