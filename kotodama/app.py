from flask import Flask, redirect, render_template, request, session, url_for
from dotenv import load_dotenv
import os

from cache import get_cached, make_cache_key, set_cached
from fortune_engine import generate_fortune
from name_analyzer import analyze_name
from stats_fetcher import get_today_stats

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

    return render_template(
        "fortune.html",
        sei=sei,
        mei=mei,
        stats=today_stats,
        fortune=fortune_data,
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


if __name__ == "__main__":
    app.run(debug=True)
