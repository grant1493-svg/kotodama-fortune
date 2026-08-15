"""
うけとめ相談室 — X（Twitter）自動投稿スクリプト
使い方: python x_post.py
Windowsタスクスケジューラで毎日決まった時刻に実行すること（kotodama/x_post.py と同じ運用方式）。

事前準備:
1. このプロジェクト専用のX developerアカウント／アプリを新規作成し、APIキーを発行する
   （kotodama用のキーとは別物。うけとめ相談室専用のキーを使うこと）
2. .env を作成し、以下を設定する:
     X_BEARER_TOKEN=...
     X_API_KEY=...
     X_API_SECRET=...
     X_ACCESS_TOKEN=...
     X_ACCESS_SECRET=...
3. articles_config.py の各ジャンルについて、note公開後に note_url を埋める
4. pip install tweepy python-dotenv pillow

投稿ロジック:
- articles_config.py の ARTICLES のうち、status が "published"（note公開済み）かつ
  x_post_text が設定されているものだけを対象にする
- 1回の実行につき1ジャンルだけ投稿する（未投稿のジャンルを順番に回す）
- 投稿済みジャンルは posted_log.json に記録し、二重投稿を防ぐ
- 画像はサムネイル（thumbnails/<key>.png）を添付する（v1.1 media_upload が必要なため OAuth1UserHandler を使用）
"""
import json
import os
from pathlib import Path

import tweepy
from dotenv import load_dotenv

from articles_config import ARTICLES

load_dotenv()

BASE_DIR = Path(__file__).parent
LOG_PATH = BASE_DIR / "posted_log.json"


def _load_posted() -> set:
    if LOG_PATH.exists():
        return set(json.loads(LOG_PATH.read_text(encoding="utf-8")))
    return set()


def _save_posted(posted: set):
    LOG_PATH.write_text(
        json.dumps(sorted(posted), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _next_article(posted: set):
    for key, article in ARTICLES.items():
        if key in posted:
            continue
        if article["status"] != "published":
            continue
        if not article["x_post_text"] or not article["note_url"]:
            continue
        return key, article
    return None, None


def build_client():
    return tweepy.Client(
        bearer_token=os.environ["X_BEARER_TOKEN"],
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )


def build_media_api():
    auth = tweepy.OAuth1UserHandler(
        os.environ["X_API_KEY"],
        os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"],
        os.environ["X_ACCESS_SECRET"],
    )
    return tweepy.API(auth)


def post_tweet():
    posted = _load_posted()
    key, article = _next_article(posted)

    if article is None:
        print("投稿対象なし: 全ジャンル投稿済み、または note_url 未設定のジャンルしか残っていません")
        return

    text = f"{article['x_post_text']}\n\n{article['note_url']}"
    thumbnail_path = BASE_DIR / "thumbnails" / f"{key}.png"

    client = build_client()
    media_ids = None

    if thumbnail_path.exists():
        media_api = build_media_api()
        media = media_api.media_upload(str(thumbnail_path))
        media_ids = [media.media_id]

    response = client.create_tweet(text=text, media_ids=media_ids)

    if response.data:
        print(f"投稿完了: ジャンル={article['genre_label']} Tweet ID={response.data['id']}")
        posted.add(key)
        _save_posted(posted)
    else:
        print("投稿失敗")


if __name__ == "__main__":
    post_tweet()
