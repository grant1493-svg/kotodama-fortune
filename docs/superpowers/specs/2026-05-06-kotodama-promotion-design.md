# ことだま占い 宣伝機能 — 設計書

**作成日:** 2026-05-06  
**ステータス:** 承認済み

---

## 概要

ことだま占いアプリに3つの宣伝機能を追加する。SNSシェアを促進するOGP設定・Pillow製シェア画像生成、およびGoogleからの自然検索流入を増やすSEO名前別ページ。

---

## 機能1: OGP画像設定

### 目的
XやLINEでURLを貼ったときにリッチプレビュー（タイトル・説明・画像）が表示されるようにする。

### 変更内容

**`kotodama/templates/base.html`**  
`<head>` 内に OGP ブロックを追加：

```html
{% block ogp %}
<meta property="og:title" content="ことだま占い">
<meta property="og:description" content="AIとリアルデータが紡ぐ、今日のあなたへの言霊占い">
<meta property="og:image" content="{{ og_image_url | default('') }}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ og_title | default('ことだま占い') }}">
<meta name="twitter:description" content="{{ og_description | default('AIとリアルデータが紡ぐ、今日のあなたへの言霊占い') }}">
<meta name="twitter:image" content="{{ og_image_url | default('') }}">
{% endblock %}
```

**`kotodama/app.py`**  
- `/fortune` ルート：`og_title`・`og_description`・`og_image_url`（`request.url_root.rstrip('/') + '/fortune/image.png'` で絶対URL化）をテンプレートに渡す
- `/name/<mei>` ルート：名前固有のOGPを設定
- デフォルトはサイト共通のOGP

---

## 機能2: シェア用画像生成（Pillow）

### 目的
ユーザーが「📸 画像を保存」ボタンを押すとダウンロードできる画像を生成。OGPにも使用。

### 画像仕様
- サイズ: 1200 × 630px（Twitterカード推奨サイズ）
- デザイン: ダーク横長（グラデーション背景 `#1a0a2e → #2d1b4e`）
- フォント: `static/fonts/NotoSansJP-Bold.ttf`（Google Fontsから取得、リポジトリに同梱）

### 画像レイアウト
```
┌─────────────────────────────────────────────────────┐
│ 🔮 ことだま占い                              [日付・六曜] │
│                                                      │
│  [名前] さんの言霊           ⭐総合 ⭐恋愛 ⭐仕事 ⭐金運  │
│                                                      │
│  ┃ [kotodama_analysis の冒頭60字]                     │
│                                                      │
│  🎨 [color]  ⏰ [time]  📍 [place]  🔢 [number]       │
│                                                      │
│                               kotodama-fortune.com  │
└─────────────────────────────────────────────────────┘
```

### 新規ファイル
**`kotodama/image_generator.py`**

```python
def generate_fortune_image(sei, mei, stats, fortune) -> bytes:
    """Return PNG bytes of the fortune card."""
```

- 入力: sei, mei, stats dict, fortune dict
- 出力: PNG bytes（`io.BytesIO`）
- 日本語テキストは NotoSansJP-Bold.ttf で描画

### 新規ルート
**`GET /fortune/image.png`**
- セッションに名前がなければ 404
- `make_cache_key(sei, mei, date_iso) + "-image"` をキーにファイルキャッシュ（`.fortune_cache/` に `.png` で保存）
- `Content-Type: image/png` で返す

### 修正ファイル
- `kotodama/requirements.txt`: `Pillow==10.4.0` を追加
- `kotodama/templates/fortune.html`: 「📸 画像を保存」ボタンを share-row に追加（`/fortune/image.png` へのリンク）

---

## 機能3: SEO名前別ページ

### 目的
「さくら 名前 占い」「陽菜 言霊」などの検索クエリでGoogleから集客する。

### ルート
`GET /name/<mei>`  
例: `/name/さくら`、`/name/陽菜`、`/name/翔太`

### コンテンツ（`templates/name_page.html`）

上から順に:
1. **名前ヒーロー** — 名前・読み・漢字の大きい表示
2. **言霊分析カード** — 漢字の意味・画数・性格キーワード（`name_analyzer` 流用）
3. **今日の運勢プレビュー** — ⭐スコア4種のみ、全項目⭐3の固定値で表示（「占うと今日の正確な運勢が出ます」と注記。Claude APIは呼ばない）
4. **CTAボタン** — 「✨ 今すぐ [名前] の言霊を占う →」→ `/register` へ遷移
5. **関連名前リンク** — 「他の名前も見る」として5件リンク

### OGP
```
og:title    = 「{mei}」の言霊占い — 名前に宿る意味と今日の運勢 | ことだま占い
og:description = {sei_meanings} の意味を持つ「{mei}」。今日の運勢スコアと言霊キーワードを無料でチェック。
```

### 収録名前
**`kotodama/popular_names.py`** — 女性名・男性名あわせて50件

```python
POPULAR_NAMES = [
    {"mei": "さくら", "kanji": "桜"},
    {"mei": "ひな",   "kanji": "陽菜"},
    # ... 50件
]
```

各エントリは `mei`（読み）と `kanji`（代表漢字表記）を持つ。`name_analyzer.analyze_name("", kanji, mei)` で分析データを生成。

### サイトマップ
`GET /sitemap.xml` — 全名前ページURLをXML形式で出力。Googleサーチコンソールに登録する。

---

## ファイル変更まとめ

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `app.py` | 修正 | `/fortune/image.png`・`/name/<mei>`・`/sitemap.xml` ルート追加、OGP変数を各ルートに追加 |
| `templates/base.html` | 修正 | OGP `{% block ogp %}` 追加 |
| `templates/fortune.html` | 修正 | 「📸 画像を保存」ボタン追加 |
| `image_generator.py` | 新規 | Pillow画像生成 |
| `popular_names.py` | 新規 | 人気名前50件定義 |
| `templates/name_page.html` | 新規 | SEO名前ページテンプレート |
| `templates/sitemap.xml` | 新規 | サイトマップテンプレート |
| `static/fonts/NotoSansJP-Bold.ttf` | 新規 | 日本語フォント（バイナリ） |
| `requirements.txt` | 修正 | `Pillow==10.4.0` 追加 |

---

## 非機能要件

- **画像キャッシュ:** `/fortune/image.png` は1日1回だけ生成（`.fortune_cache/<key>-image.png`）
- **SEOページのClaude API呼び出し:** SEO名前ページではClaude APIを呼ばない（今日のスコアはダミー固定値を表示し「占うと正確な結果が出ます」と誘導）
- **フォントライセンス:** NotoSansJP は SIL Open Font License — 商用利用・再配布OK
- **`/name/<mei>` の未収録名前:** `popular_names.py` に存在しない名前は 404 を返す（スパム対策）

---

## スコープ外

- 英語名・中国語名への対応
- ユーザーが任意の名前でSEOページを生成する機能
- 画像のInstagram向け正方形バリアント（将来対応）
