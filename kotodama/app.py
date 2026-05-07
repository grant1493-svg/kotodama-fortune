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


@app.route("/sitemap.xml")
def sitemap():
    from popular_names import POPULAR_NAMES
    base_url = request.url_root.rstrip("/")
    xml = render_template("sitemap.xml", base_url=base_url, names=POPULAR_NAMES)
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
