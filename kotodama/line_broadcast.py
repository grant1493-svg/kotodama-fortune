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

def broadcast_message():
    today = date.today()
    weekday = WEEKDAYS[today.weekday()]
    month = today.month
    day = today.day

    # 曜日別メッセージ
    messages = {
        "月": "今週も新しいスタートです✨ あなたの名前に宿る言霊が、今週の運気を後押しします🔮",
        "火": "火曜日は行動力がアップする日💪 あなたの言霊パワーを確認しましょう！",
        "水": "週の折り返し🌿 今日の運勢をことだま占いでチェックして、後半戦を乗り切ろう！",
        "木": "木曜日は運気が動き始める日🌟 言霊の力で今日を最高の1日に！",
        "金": "週末が近づいてきました🎉 恋愛運・金運もことだま占いで確認を💕",
        "土": "おはようございます🌸 土曜日は相性占いがおすすめ！大切な人との相性を確かめて💑",
        "日": "今日も良い1日を🌈 明日からの1週間の運勢を先取りチェック！",
    }

    text = (
        f"🔮 {month}月{day}日（{weekday}）のことだま占い\n\n"
        f"{messages[weekday]}\n\n"
        f"▼ 今日の運勢を見る\n"
        f"https://kotodama-fortune.onrender.com"
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
        print(f"✅ 配信完了: {text}")
    else:
        print(f"❌ エラー: {response.status_code} {response.text}")

if __name__ == "__main__":
    broadcast_message()
