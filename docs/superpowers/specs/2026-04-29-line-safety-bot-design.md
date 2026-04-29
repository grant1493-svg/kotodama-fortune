# LINE 安全運転・注意喚起ボット — 設計書

**作成日:** 2026-04-29
**ステータス:** 承認済み

---

## 概要

運送会社のドライバーに対し、毎朝 7:00 に LINE グループおよび個人へ安全運転啓発メッセージを自動配信するシステム。ニュースサイトのスクレイピング・気象情報・社内データを収集し、Claude API が温かく具体的な日本語メッセージを生成して LINE Messaging API で送信する。Railway.app のCronジョブで完全自動運用。

---

## アーキテクチャ

```
[毎朝 7:00 JST / Railway Cron]
        ↓
  [1] ニュース収集（スクレイピング）
      ・全日本トラック協会
      ・国土交通省 事故情報
      ・NHKニュース 交通カテゴリ
      ・Yahoo!ニュース キーワード検索
        ↓
  [2] 気象情報取得（気象庁API）
      ・関東主要地点（東京・横浜・千葉・埼玉・茨城・栃木・群馬）
        ↓
  [3] 社内データ読み込み
      ・internal_data.txt（GitHubリポジトリ内）
      ・内容がなければスキップ
        ↓
  [4] Claude API でメッセージ生成
      ・収集情報を整理してプロンプトに渡す
      ・柔らかく・短く・具体的なLINEメッセージを生成
        ↓
  [5] LINE Messaging API で送信
      ・複数グループへ一斉送信
      ・グループ未参加の個人ユーザーへ個別送信
```

---

## ファイル構成

```
line_safety_bot/
├── main.py              # エントリポイント（Railwayが実行）
├── scraper.py           # ニュース収集
├── weather.py           # 気象情報取得
├── message_generator.py # Claude API でメッセージ生成
├── line_sender.py       # LINE Messaging API 送信
├── internal_data.txt    # 社内事故・クレーム情報（毎日 git push で更新）
├── targets.json         # 送信先グループID・ユーザーIDリスト
├── requirements.txt
└── railway.toml         # Railway 設定
```

---

## LINE Messaging API セットアップ手順

### Step 1：LINE公式アカウント作成
1. [LINE Business](https://business.line.me/) でアカウント作成
2. 「Messaging API」を有効化
3. **チャネルアクセストークン**（長期）と**チャネルシークレット**を取得

### Step 2：送信先IDの取得
- グループLINEに公式アカウントを招待すると、Webhookでグループ ID が取得できる
- 個人ユーザーIDも同様にWebhookで取得
- 取得したIDを `targets.json` に保存：

```json
{
  "groups": ["Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"],
  "users":  ["Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"]
}
```

### Step 3：Railway に環境変数を設定
```
LINE_CHANNEL_ACCESS_TOKEN=...
ANTHROPIC_API_KEY=...
```

---

## メッセージフォーマット

```
🚛 今日の安全運転メッセージ（4/29）

【今日の天気リスク】
関東は午後から雨。
路面が滑りやすくなるので、
トラック1台分以上の車間を意識して。

【事故ニュース】
昨日、東名高速でトラックの追突事故。
疲れを感じたら、迷わず休憩しよう。

今日も無事に帰ってきてください。
いつも本当にありがとう。
```

---

## Claude API プロンプト設計

### システムプロンプト
```
あなたは運送会社の安全管理担当者として、ドライバーへ毎日LINEメッセージを送ります。
以下のルールを必ず守ってください。

・専門用語は使わない
・一文を短くする
・「トラック1台分」のように具体的なイメージで書く
・警告ではなく、仲間を気にかける温かい雰囲気で
・全体で200文字以内
・締めの言葉は必ず「今日も無事に帰ってきてください。」
```

### ユーザープロンプト（毎日生成）
```
以下の情報をもとに今日のLINEメッセージを作ってください。

【天気】
{weather_summary}

【ニュース】
{news_summary}  ※なければ「なし」

【社内情報】
{internal_data}  ※なければ「なし」
```

### フォールバック（全情報なし）
ニュースも社内情報もない日は「今日も無事に帰ってきてください。」を中心にした労いメッセージのみ生成。

---

## エラーハンドリング

| 処理 | 失敗時の動作 |
|------|------------|
| ニュース収集失敗 | スキップしてメッセージ生成を続行 |
| 気象API失敗 | 天気情報なしでメッセージ生成を続行 |
| Claude API失敗 | 固定の予備メッセージを送信 |
| LINE送信失敗 | Railway のログに記録、翌日再試行 |

### 固定の予備メッセージ（Claude APIが落ちた場合）
```
🚛 今日も安全運転でお願いします。
車間距離はトラック1台分以上あけて。
今日も無事に帰ってきてください。
```

---

## Railway デプロイ設定

### railway.toml
```toml
[deploy]
startCommand = "python main.py"

[[crons]]
schedule = "0 22 * * *"  # UTC 22:00 = JST 07:00
command = "python main.py"
```

### requirements.txt
```
anthropic
requests
beautifulsoup4
line-bot-sdk
```

### デプロイ手順（初回のみ）
1. GitHub にリポジトリ作成・コードを push
2. [railway.app](https://railway.app) でGitHubと連携
3. 環境変数（`LINE_CHANNEL_ACCESS_TOKEN`、`ANTHROPIC_API_KEY`）を設定
4. 自動デプロイ完了 → 翌朝7:00から自動送信開始

---

## コスト見積もり

| サービス | 費用 |
|----------|------|
| Railway | 無料枠内（月500時間、1日1回なら余裕） |
| LINE Messaging API | 月200通まで無料（超過は有料プランへ移行） |
| Claude API | 約$0.01〜$0.05/日（Sonnet使用） |
| 気象庁API | 完全無料 |

---

## スクレイピング対象サイト

| サイト | 対象コンテンツ |
|--------|--------------|
| 全日本トラック協会（jta.or.jp） | 事故・安全情報 |
| 国土交通省 | 事故情報・通達 |
| NHKニュース 交通カテゴリ | 最新事故ニュース |
| Yahoo!ニュース | 「トラック 事故」キーワード検索 |

---

## 気象情報取得エリア

気象庁の無料JSONAPIを使用。関東主要7地点：
- 東京・横浜・千葉・さいたま・水戸・宇都宮・前橋
