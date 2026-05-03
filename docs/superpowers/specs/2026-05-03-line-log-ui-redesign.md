# LINEログ整理アプリ UIリデザイン仕様

**日付:** 2026-05-03  
**対象ファイル:** `line_log_app.py`（Streamlitアプリ）

---

## 1. デザイン方針

| 項目 | 決定内容 |
|---|---|
| スタイル | クリーン（ビジネス）— ホワイト/ライトグレーベース |
| アクセントカラー | ティール `#0d9488` / `#0f766e` |
| レイアウト | ダッシュボード型（KPIカード＋フィルターチップ＋テーブル） |
| 実装アプローチ | ハイブリッド（HTMLカスタムUI ＋ `st.data_editor` 維持） |

---

## 2. 画面構成

### 2-1. ヘッダー
- ティールグラデーション（`#0f766e → #0d9488`）のフルワイドバー
- 左: アプリ名（白文字）＋サブタイトル
- 右: アップロードファイル名 ＋ 対象期間（`YYYY/MM/DD 〜 YYYY/MM/DD`）
- `st.markdown(unsafe_allow_html=True)` で実装

### 2-2. KPIカード（4枚）
- `st.columns(4)` ＋ 各列に `st.markdown()` でカードHTML
- カード1: 総件数（ティール）
- カード2: 事故件数（レッド `#ef4444`）
- カード3: 車両関連件数（アンバー `#f59e0b`）
- カード4: 未対応件数（インディゴ `#6366f1`）
- 「未対応」= `進捗状況 == "未対応"` の件数をカウント

### 2-3. 情報バナー
- 期間外除外件数・重複削除件数を1行のティール系バナーで表示
- `st.markdown()` で実装（現在の `st.info()` を置き換え）

### 2-4. 整理結果テーブルエリア
- セクションタイトルを `st.markdown()` でスタイリング
- 分類フィルターは既存の `st.selectbox()` にCSSを適用してスタイリング（機能は変更なし）
- テーブル本体は `st.data_editor` をそのまま維持（編集・削除チェック機能を保持）
- カスタムCSSで `st.data_editor` のヘッダー・行・フォントを整える

### 2-5. 削除ボタン
- `st.button()` にカスタムCSSでレッド＋ボックスシャドウを適用

### 2-6. 分類別件数
- `st.dataframe()` からカードグリッド（`st.columns` ＋ `st.metric()`）に変更

### 2-7. 削除結果一覧
- `st.dataframe()` のスタイルはデフォルト維持（変更の優先度低）

### 2-8. ダウンロードボタン
- ティールグラデーションのカスタムCSSを `st.download_button` に適用

---

## 3. カラーパレット

```
Primary:    #0d9488  (ティール)
Primary-dk: #0f766e  (ダークティール)
Primary-lt: #ccfbf1  (ライトティール bg)
Primary-tx: #0f766e  (ティールテキスト)

Danger:     #ef4444  (事故バッジ、削除ボタン)
Warning:    #f59e0b  (車両バッジ、未対応)
Info:       #3b82f6  (対応中)
Success:    #22c55e  (完了)
Purple:     #6366f1  (未対応KPI)

Text-1:     #1e293b  (本文)
Text-2:     #64748b  (補助テキスト)
Text-3:     #94a3b8  (プレースホルダー)
Border:     #e2e8f0
Bg-white:   #ffffff
Bg-light:   #f8fafc
Bg-page:    #f1f5f9
```

---

## 4. 実装方針

### カスタムCSS注入
- ファイル先頭で `st.markdown("<style>...</style>", unsafe_allow_html=True)` を1回呼び出す
- `.stButton > button`, `.stDownloadButton > button` などStreamlitのセレクタを対象にスタイルを上書き
- `st.data_editor` のスタイル調整は `:has()` セレクタや `.stDataEditor` クラスで対応

### HTMLコンポーネント
- ヘッダー、KPIカード、情報バナー、セクションタイトル、分類カウントグリッドを `st.markdown(html, unsafe_allow_html=True)` で実装
- Pythonの変数（件数・日付）をf-stringでHTMLに埋め込む

### 変更しないもの
- `st.data_editor` の呼び出しコード（`column_config` 含む）
- ロジック部分（パース、フィルタ、削除処理）は一切変更しない
- セッションステート管理

---

## 5. 対象外（スコープ外）

- モバイルレスポンシブ対応
- ダークモード切り替え
- `st.data_editor` の内部セルスタイル（Streamlit制約上困難）
- 削除結果一覧のスタイル詳細化
