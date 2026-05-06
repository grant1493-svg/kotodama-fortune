import json
import pytest
from unittest.mock import patch

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret")

from app import app as flask_app


SAMPLE_FORTUNE = {
    "kotodama_analysis": "花の言霊は美しさと開花を示します",
    "today_message": "今日は素晴らしい一日です",
    "morning_message": "朝の光があなたを導きます",
    "scores": {"overall": 4, "love": 3, "work": 5, "money": 3},
    "lucky": {"color": "ピンク", "time": "午前10時", "place": "カフェ", "number": 7},
}

SAMPLE_STATS = {
    "date": "2026年05月05日", "date_iso": "2026-05-05",
    "weekday": "火曜日", "rokuyo": "大安", "sekki": "立夏",
    "is_holiday": True, "weather": "晴れ",
    "temperature": 22.5, "pressure": 1008.2, "humidity": 55,
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_index_redirects_to_register(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/register" in resp.headers["Location"]


def test_register_get_returns_200(client):
    resp = client.get("/register")
    assert resp.status_code == 200
    assert "ことだま占い" in resp.data.decode("utf-8")


def test_register_post_sets_session_and_redirects(client):
    resp = client.post("/register", data={
        "sei": "田中", "mei": "花", "yomi": "たなか はな", "region": "東京"
    }, follow_redirects=False)
    assert resp.status_code == 302
    assert "/fortune" in resp.headers["Location"]


def test_fortune_without_session_redirects(client):
    resp = client.get("/fortune")
    assert resp.status_code == 302
    assert "/register" in resp.headers["Location"]


def test_fortune_with_session_returns_200(client):
    with client.session_transaction() as sess:
        sess["sei"] = "田中"
        sess["mei"] = "花"
        sess["yomi"] = "たなか はな"
        sess["region"] = "東京"

    with patch("app.get_cached", return_value=SAMPLE_FORTUNE), \
         patch("app.get_today_stats", return_value=SAMPLE_STATS):
        resp = client.get("/fortune")

    assert resp.status_code == 200
    assert "田中" in resp.data.decode("utf-8")


def test_privacy_returns_200(client):
    assert client.get("/privacy").status_code == 200


def test_tokushoho_returns_200(client):
    assert client.get("/tokushoho").status_code == 200


def test_disclaimer_returns_200(client):
    assert client.get("/disclaimer").status_code == 200


def test_full_fortune_flow(client):
    """Register → fortune page shows name and stats."""
    with patch("app.get_cached", return_value=None), \
         patch("app.get_today_stats", return_value=SAMPLE_STATS), \
         patch("app.generate_fortune", return_value=SAMPLE_FORTUNE), \
         patch("app.set_cached", return_value=None):

        client.post("/register", data={
            "sei": "山田", "mei": "桜", "yomi": "やまだ さくら", "region": "大阪"
        })
        resp = client.get("/fortune")

    body = resp.data.decode("utf-8")
    assert "山田" in body
    assert "桜" in body
    assert "大安" in body
    assert "今日は素晴らしい" in body


def test_reset_clears_session(client):
    with client.session_transaction() as sess:
        sess["sei"] = "田中"
        sess["mei"] = "花"
    resp = client.get("/reset", follow_redirects=False)
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert "sei" not in sess
