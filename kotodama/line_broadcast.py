"""
毎朝LINE公式アカウントから占いメッセージを一斉配信するスクリプト
使い方: python line_broadcast.py
"""
import os
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv()

CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

# 人気名前ページへの誘導リスト（Amazonアフィリエイト付きページ）
NAME_LINKS = [
    ("さくら", "https://www.kotodama-uranai.com/name/さくら"),
    ("ひな", "https://www.kotodama-uranai.com/name/ひな"),
    ("はると", "https://www.kotodama-uranai.com/name/はると"),
    ("ゆい", "https://www.kotodama-uranai.com/name/ゆい"),
    ("そうた", "https://www.kotodama-uranai.com/name/そうた"),
    ("みお", "https://www.kotodama-uranai.com/name/みお"),
    ("りん", "https://www.kotodama-uranai.com/name/りん"),
]

def broadcast_message():
    today = date.today()
    weekday = WEEKDAYS[today.weekday()]
    month = today.month
    day = today.day

    # 曜日別メッセージ（名前ページへの誘導を追加）
    messages = {
        "月": (
            "今週も新しいスタートです✨\n"
            "あなたの名前に宿る言霊が、今週の運気を後押しします🔮\n\n"
            "▼ 自分の名前の言霊を調べる\n"
            "https://www.kotodama-uranai.com/name/さくら\n\n"
            "▼ 今日の運勢を占う\n"
            "https://www.kotodama-uranai.com"
        ),
        "火": (
            "火曜日は行動力がアップする日💪\n"
            "あなたの言霊パワーで今日を動かそう！\n\n"
            "▼ 恋愛運が高い名前は？\n"
            "https://www.kotodama-uranai.com/name/ゆい\n\n"
            "▼ 今日の運勢を占う\n"
            "https://www.kotodama-uranai.com"
        ),
        "水": (
            "週の折り返し🌿\n"
            "今日の運勢をことだま占いでチェックして後半戦を乗り切ろう！\n\n"
            "▼ 仕事運が強い名前の言霊\n"
            "https://www.kotodama-uranai.com/name/はると\n\n"
            "▼ 今日の運勢を占う\n"
            "https://www.kotodama-uranai.com"
        ),
        "木": (
            "木曜日は運気が動き始める日🌟\n"
            "言霊の力で今日を最高の1日に！\n\n"
            "▼ 金運を高める名前の言霊\n"
            "https://www.kotodama-uranai.com/name/そうた\n\n"
            "▼ 今日の運勢を占う\n"
            "https://www.kotodama-uranai.com"
        ),
        "金": (
            "週末が近づいてきました🎉\n"
            "恋愛運・金運もことだま占いで確認を💕\n\n"
            "▼ 人気急上昇！「りん」の言霊\n"
            "https://www.kotodama-uranai.com/name/りん\n\n"
            "▼ 今日の運勢を占う\n"
            "https://www.kotodama-uranai.com"
        ),
        "土": (
            "おはようございます🌸\n"
            "土曜日は相性占いがおすすめ！大切な人との相性を確かめて💑\n\n"
            "▼ 相性占いはこちら\n"
            "https://www.kotodama-uranai.com/couple\n\n"
            "▼ 今日の運勢を占う\n"
            "https://www.kotodama-uranai.com"
        ),
        "日": (
            "今日も良い1日を🌈\n"
            "明日からの1週間の運勢を先取りチェック！\n\n"
            "▼ 「みお」の言霊 — 美しい名前の意味\n"
            "https://www.kotodama-uranai.com/name/みお\n\n"
            "▼ 今日の運勢を占う\n"
            "https://www.kotodama-uranai.com"
        ),
    }

    text = (
        f"🔮 {month}月{day}日（{weekday}）のことだま占い\n\n"
        f"{messages[weekday]}"
    )

    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messages": [{"type": "text", "text": text}]
    }

    response = requests.post(
        "https://api.line.me/v2/bot/message/broadcast",
        headers=headers,
        json=payload,
    )

    if response.status_code == 200:
        print(f"✅ 配信完了: {month}月{day}日（{weekday}）")
    else:
        print(f"❌ エラー: {response.status_code} {response.text}")

if __name__ == "__main__":
    broadcast_message()
