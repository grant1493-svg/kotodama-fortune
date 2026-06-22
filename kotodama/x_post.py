"""
ことだま占い — X（Twitter）自動投稿スクリプト
使い方: python x_post.py
Windowsタスクスケジューラで毎日朝7時に実行すること

必要なAPIキーを .env に追加：
  X_BEARER_TOKEN=...
  X_API_KEY=...
  X_API_SECRET=...
  X_ACCESS_TOKEN=...
  X_ACCESS_SECRET=...

インストール: pip install tweepy python-dotenv
"""
import os
import tweepy
from datetime import date
from dotenv import load_dotenv

load_dotenv()

# ─── API認証 ───────────────────────────────────────────
client = tweepy.Client(
    bearer_token=os.environ["X_BEARER_TOKEN"],
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_SECRET"],
)

# ─── バナー画像（日付末尾数字で選択） ─────────────────
BANNERS = {
    frozenset([0, 1]): "static/banner_feature.png",
    frozenset([2, 3]): "static/banner_kotodama.png",
    frozenset([4, 5]): "static/couple_banner.png",
    frozenset([6, 7]): "static/banner_morning.png",
    frozenset([8, 9]): "static/banner_data.png",
}

# ─── 人気名前ページ（曜日で変える） ───────────────────
WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

NAME_LINKS = {
    0: ("さくら", "https://www.kotodama-uranai.com/name/さくら"),  # 月
    1: ("ひな", "https://www.kotodama-uranai.com/name/ひな"),    # 火
    2: ("はると", "https://www.kotodama-uranai.com/name/はると"),  # 水
    3: ("ゆい", "https://www.kotodama-uranai.com/name/ゆい"),    # 木
    4: ("そうた", "https://www.kotodama-uranai.com/name/そうた"),  # 金
    5: ("みお", "https://www.kotodama-uranai.com/name/みお"),    # 土
    6: ("りん", "https://www.kotodama-uranai.com/name/りん"),    # 日
}

# ─── 投稿テキスト（曜日別） ────────────────────────────
MESSAGES = {
    0: "新しい週のスタート🌅\n\nあなたの名前には、今週を切り開く言霊が宿っています。\n今日の運勢を確認して、最高の月曜日を。",
    1: "🔥 火曜日は行動の日。\n\nことだま占いでエネルギーをチェックして、今日を動かそう。",
    2: "週の折り返し🌿\n\n今日の六曜と気象データを組み合わせた、あなただけの言霊メッセージが届きます。",
    3: "木曜日は運気が動き出す日⚡\n\n名前の言霊が、今日のあなたに伝えたいことがあります。",
    4: "今週もよく頑張った🎉\n\n週末前に今日の恋愛運・金運を確認。言霊があなたの背中を押します。",
    5: "土曜日は相性占いの日💕\n\n大切な人との相性を「言霊」で確かめてみて。",
    6: "おはようございます🌸\n\n今週1週間の言霊を振り返り、来週への力を蓄えて。",
}

BASE_URL = "https://www.kotodama-uranai.com"


def get_banner_path():
    day_last = date.today().day % 10
    for keys, path in BANNERS.items():
        if day_last in keys:
            return path
    return "static/banner_feature.png"


def post_tweet():
    today = date.today()
    weekday = today.weekday()
    weekday_str = WEEKDAYS[weekday]
    month, day = today.month, today.day

    name_kanji, name_url = NAME_LINKS[weekday]
    body = MESSAGES[weekday]

    text = (
        f"🔮 {month}月{day}日（{weekday_str}）の言霊\n\n"
        f"{body}\n\n"
        f"▼ 「{name_kanji}」の言霊を見る\n{name_url}\n\n"
        f"▼ 今日の運勢を占う\n{BASE_URL}\n\n"
        f"#ことだま占い #言霊 #今日の運勢 #名前占い"
    )

    # 画像投稿（v1 API が必要な場合はauth1を別途設定）
    # auth1 = tweepy.OAuth1UserHandler(...)
    # api = tweepy.API(auth1)
    # media = api.media_upload(get_banner_path())
    # response = client.create_tweet(text=text, media_ids=[media.media_id])

    # テキストのみ投稿
    response = client.create_tweet(text=text)

    if response.data:
        print(f"✅ 投稿完了: {month}月{day}日（{weekday_str}）")
        print(f"   Tweet ID: {response.data['id']}")
    else:
        print(f"❌ 投稿失敗")


if __name__ == "__main__":
    post_tweet()
