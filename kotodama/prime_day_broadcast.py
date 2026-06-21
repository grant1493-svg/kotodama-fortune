"""
Amazon Prime Day (7/10-7/13) 専用LINE一斉配信スクリプト
使い方: python prime_day_broadcast.py

Windowsタスクスケジューラで 7/10, 7/11, 7/12, 7/13 の朝7時に実行すること
"""
import os
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv()

CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

# Prime Day別メッセージ（4日分）
PRIME_DAY_MESSAGES = {
    10: (  # 7/10（金）初日
        "🎉 Amazon Prime Day スタート！\n"
        "今日から7/13まで「開運グッズ」が紹介料上限なしでお得！\n\n"
        "✨ あなたの名前の言霊に合った\n"
        "パワーストーン・開運グッズを見つけよう\n\n"
        "▼ まず自分の名前の言霊をチェック\n"
        "https://www.kotodama-uranai.com/name/さくら\n\n"
        "▼ 今日の運勢を確認してから買い物を\n"
        "https://www.kotodama-uranai.com\n\n"
        "💎 言霊と相性のいいパワーストーンが\n"
        "Prime Dayなら特別価格で手に入ります🛍️"
    ),
    11: (  # 7/11（土）2日目
        "🔮 Prime Day 2日目！\n"
        "昨日から「開運グッズ」を狙っている方へ📣\n\n"
        "名前の言霊を知ってから買い物すると\n"
        "自分に本当に合ったアイテムが選べます✨\n\n"
        "▼ 人気No.1「はると」の言霊\n"
        "https://www.kotodama-uranai.com/name/はると\n\n"
        "▼ 相性占いで大切な人へのギフト選びも\n"
        "https://www.kotodama-uranai.com/couple\n\n"
        "📖 姓名判断の本もPrime Day価格でお得！"
    ),
    12: (  # 7/12（日）3日目
        "⏰ Prime Day 残り2日！\n"
        "今日の言霊運勢をチェックしてから\n"
        "開運お買い物を楽しんで🛍️\n\n"
        "金運・仕事運を高めたい方へ——\n"
        "名前の言霊を活かした開運グッズが\n"
        "Amazonで特別価格中！\n\n"
        "▼ あなたの名前の言霊パワーを確認\n"
        "https://www.kotodama-uranai.com\n\n"
        "▼ 開運・風水グッズはこちらから\n"
        "https://www.kotodama-uranai.com/name/ゆい\n\n"
        "💰 言霊が後押しする買い物で金運UP🌟"
    ),
    13: (  # 7/13（月）最終日
        "🚨 Prime Day 今日で最終日！\n"
        "開運グッズのお買い物はお早めに🏃‍♀️\n\n"
        "ことだま占いユーザーの皆さんへ——\n"
        "今日の金運スコアを確認してから\n"
        "最後のチャンスを活かして！\n\n"
        "▼ 今日の金運を今すぐチェック\n"
        "https://www.kotodama-uranai.com\n\n"
        "▼ 言霊に合ったパワーストーンを探す\n"
        "https://www.kotodama-uranai.com/name/りん\n\n"
        "✨ 名前の言霊があなたの運命を開く\n"
        "今日が最後のPrime Dayチャンスです！"
    ),
}

def broadcast_prime_day():
    today = date.today()

    if today.month != 7 or today.day not in PRIME_DAY_MESSAGES:
        print(f"⚠️ 今日（{today}）はPrime Day期間外です。7/10〜7/13に実行してください。")
        return

    text = f"🛍️ Amazon Prime Day {today.day}日目\n\n" + PRIME_DAY_MESSAGES[today.day]

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
        print(f"✅ Prime Day配信完了: 7/{today.day}")
    else:
        print(f"❌ エラー: {response.status_code} {response.text}")

if __name__ == "__main__":
    broadcast_prime_day()
