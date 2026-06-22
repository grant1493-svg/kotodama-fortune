# ことだま占い アプリ — 作業メモ

このフォルダは「ことだま占い」Webアプリの専用作業フォルダです。
**このフォルダを選択して作業することで、他のプロジェクトと混在しません。**

---

## アプリ概要

- **サービス名**: ことだま占い
- **URL（本番）**: https://www.kotodama-uranai.com ✅ カスタムドメイン設定完了
- **Renderサービス**: https://kotodama-fortune.onrender.com
- **GitHub**: grant1493-svg / kotodama-fortune（masterブランチ自動デプロイ）
- **Google AdSense**: カスタムドメイン取得後に再申請予定

---

## ローカル起動

```bash
# このフォルダ（kotodama/）から起動すること
cd C:\Users\admin\.local\bin\kotodama
python app.py
# → http://localhost:5000
```

---

## ファイル構成

```
kotodama/
  app.py               # Flaskルート（メインエントリ）
  name_analyzer.py     # 姓名の漢字画数・意味・音韻分析
  kanji_dict.py        # 漢字画数・意味データ
  popular_names.py     # 人気名前データ（関連名表示用）
  stats_fetcher.py     # 気象API(Open-Meteo) + 暦データ（六曜・節気・祝日）
  fortune_engine.py    # Claude APIプロンプト構築 + JSON応答パース
  image_generator.py   # 占い結果の画像生成（Pillow）
  cache.py             # メモリキャッシュ（Renderエフェメラル対策済み）
  line_broadcast.py    # LINE公式アカウントへの一斉配信スクリプト
  templates/
    base.html          # 共通レイアウト（OGP・AdSense・JSON-LD含む）
    fortune.html       # 占い結果ページ
    couple.html        # 相性占いページ
    name_page.html     # 名前一覧ページ（SEO用）
    privacy.html       # プライバシーポリシー
    disclaimer.html    # 免責事項
    tokushoho.html     # 特定商取引法
    register.html      # LINE登録ページ
    sitemap.xml        # サイトマップ（Googleに送信済み）
  static/
    ogp.png            # OGP画像
    couple_banner.png  # X投稿用バナー（相性占い）
    banner_feature.png # X投稿用バナー（機能紹介）
    banner_kotodama.png# X投稿用バナー（言霊）
    banner_morning.png # X投稿用バナー（朝の運勢）
    banner_data.png    # X投稿用バナー（データ）
    line_qr_share.png  # LINE友だち追加QRコード
  .env                 # 環境変数（Gitに含まない）
  requirements.txt     # Pythonパッケージ
  tests/               # pytestテスト群
```

---

## 環境変数（.env）

```
ANTHROPIC_API_KEY=...
FLASK_SECRET_KEY=...
LINE_CHANNEL_ACCESS_TOKEN=...
LINE_CHANNEL_SECRET=...
```

---

## デプロイ（Render）

- GitHubのmasterブランチにpushすると自動デプロイ
- `git add . && git commit -m "変更内容" && git push origin master`

---

## DNS・ドメイン設定（完了）

| 項目 | 内容 | 状態 |
|------|------|------|
| ドメイン | kotodama-uranai.com（お名前.com） | 取得済み ✅ |
| ネームサーバー | 01〜04.dnsv.jp に変更 | 完了 ✅ |
| DNSレコード追加 | CNAMEとAレコードをお名前.comに登録 | 完了 ✅（2026/06/11） |
| Render カスタムドメイン | www.kotodama-uranai.com | Verified ✅ |
| Google AdSense | カスタムドメインで再申請 | **次のステップ** ⏳ |

### 次にやること

1. `https://www.kotodama-uranai.com` でサイトが正常表示されるか確認
2. Google AdSense（https://www.google.com/adsense）にログイン
3. サイト追加 → `www.kotodama-uranai.com` で再申請
4. 審査通過後、AdSenseコードをbase.htmlに貼り付け

---

## X（Twitter）自動投稿

- Windows タスクスケジューラで毎日実行
- バナー画像は日付の末尾数字で自動選択：
  - 0・1 → banner_feature.png
  - 2・3 → banner_kotodama.png
  - 4・5 → couple_banner.png
  - 6・7 → banner_morning.png
  - 8・9 → banner_data.png

---

## テスト

```bash
python -m pytest tests/ -q
```
