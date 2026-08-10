# うけとめ相談室 — 日次自動投稿ルーティン 設計書

**作成日:** 2026-08-11
**ステータス:** レビュー待ち
**対象:** `uketome-soudanshitsu/`（note.com「うけとめ相談室」記事シリーズ）

---

## 概要

「うけとめ相談室」note記事シリーズ（現在5ジャンル公開済み）を、毎日1本ペースで完全自動生成・投稿する仕組みを作る。単なる自動投稿ではなく、以下の3つの学習ループを組み込む点が核:

1. **ジャンル選定の学習** — 過去記事のスキ数を見て、当たりジャンルへ徐々に寄せていく
2. **執筆品質の学習** — 編集チェックでNGが出た理由を蓄積し、同じ指摘を繰り返さないようにする
3. **判定基準そのものの学習** — 「特化に切り替えるタイミング」の閾値自体も、過去の判定が正しかったかを振り返って自己調整する

**目的:** note記事の投稿数を増やしつつ、どのジャンルの悩みが強く求められているかのデータを蓄積し、将来の「成長型お悩み相談AIアプリ」構想（[[project_uketome_soudanshitsu]]参照）に向けたデータ基盤を作る。

---

## 全体フロー

```
/schedule（毎日1回、既定 9:00 JST）
  └─ 日次オーケストレーター（1エージェント、daily_routine.md に従って実行）
       │
       ├─ 0. 二重実行チェック
       │     publish_history.json に本日分の記録があれば即終了
       │
       ├─ 1. 分析役サブエージェント（performance-analyst-soudan）
       │     ・publish_history.json の過去記事URLからスキ数を再取得して更新
       │     ・ジャンル別の平均スキ数・直近3投稿のジャンルを集計
       │     ・judgment_policy.json の閾値に基づき「均等ローテーション」か「上位ジャンル優先」かを判定
       │     ・qa_feedback_log.json 直近10件を要約
       │     → 分析ブリーフを次工程へ渡す
       │
       ├─ 2. 企画会議役サブエージェント（concept-planner-soudan）
       │     ・分析ブリーフを受け取り、本日のジャンル・切り口・構成案を決定
       │     ・直近3投稿のジャンルは除外
       │     ・数回に1回、軽いリサーチで genre_candidates.json に新ジャンル候補を追加
       │     ・分析ブリーフの「過去の指摘リスト」を構成案に反映
       │
       ├─ 3. 執筆役サブエージェント（writer-soudan）
       │     ・構成案どおりに本文執筆（承認→見極め→メカニズム→出し分け→統合メソッドの型）
       │     ・articles/<date>_<genre>.md に保存
       │
       ├─ 4. 編集チェック役サブエージェント（qa-reviewer-soudan）
       │     ・構成・内容をGO/NG判定
       │     ・NGの場合、理由を箇条書きで返す → qa_feedback_log.json に記録 → 3で再執筆（最大2回）
       │     ・2回ともNGなら本日はスキップ（8へ）
       │
       ├─ 5. 画像生成
       │     ・ad-designer（既存）でジャンルのシーン設定から背景写真を生成
       │     ・失敗/低品質時は generate_thumbnail.py のグラデーション背景にフォールバック
       │
       ├─ 6. 画像合成（compose_thumbnail.py）
       │     ・背景写真 + static/logo_overlay.png（ロゴ/キャッチコピー、独立管理）を合成
       │     ・thumbnails/<date>_<genre>.png を出力
       │
       ├─ 7. note投稿（claude-in-chromeブラウザ操作）
       │     ・タイトル入力 → Tabで本文欄へ → スクリーンショットでタイトル/本文分離を確認 → 本文流し込み
       │     ・画像アップロード（手動ダイアログ、拡張機能で操作）
       │     ・公開 → 発行後URLを取得
       │     ・失敗時は1回リトライ、それでも失敗ならスキップ
       │
       └─ 8. ログ記録 + Push通知
             ・publish_history.json に本日の結果を追記（成功/スキップいずれも）
             ・要約をPush通知
```

---

## コンポーネント（サブエージェント）

既存の `ad-designer`（Canva連携の画像生成）はそのまま流用。新規に4つのサブエージェントを `.claude/agents/` に追加する。物販チーム（market-researcher / concept-designer / copywriter / qa-reviewer / performance-analyst）と同じ「リサーチ→企画→執筆→チェック→分析」パターンを踏襲する。

| サブエージェント | 役割 | 入力 | 出力 |
|---|---|---|---|
| `performance-analyst-soudan` | 過去実績分析・ローテーション判定 | publish_history.json, judgment_policy.json | 分析ブリーフ |
| `concept-planner-soudan` | ジャンル・切り口・構成案の決定 | 分析ブリーフ, genre_candidates.json | 構成案 |
| `writer-soudan` | 記事本文執筆 | 構成案, qa_feedback_log.json直近10件 | 記事本文(md) |
| `qa-reviewer-soudan` | 構成・内容チェック、GO/NG判定 | 記事本文 | GO/NG + 理由リスト |

日次オーケストレーター本体（画像合成・note投稿・ログ記録・通知）は新規サブエージェント化せず、`daily_routine.md`（プレイブック）に沿って動く1つの実行フローとして扱う。

---

## データ構造

すべて `uketome-soudanshitsu/` 配下に新規作成。

### `publish_history.json`（投稿実績ログ）

```json
[
  {
    "date": "2026-08-11",
    "status": "published",
    "genre": "love",
    "angle": "遠距離恋愛の不安",
    "note_url": "https://note.com/soudan_labo/n/xxxx",
    "like_count": 12,
    "like_count_checked_at": "2026-08-18",
    "qa_retry_count": 0
  },
  {
    "date": "2026-08-12",
    "status": "skipped",
    "reason": "qa_ng_max_retry"
  }
]
```

### `qa_feedback_log.json`（NG理由の蓄積）

```json
[
  { "date": "2026-08-11", "genre": "love", "attempt": 1, "reasons": ["STEP0の承認が弱い", "見極め基準が3専門家で重複"] }
]
```

### `genre_candidates.json`（新ジャンル候補ストック）

```json
[
  { "key": "career_change", "name": "転職・キャリアの悩み", "status": "candidate", "discovered_date": "2026-08-11" }
]
```

`status`: `candidate`（未採用） → `active`（採用済み、ローテーション対象） → `retired`（成果が出ず離脱）

### `judgment_policy.json`（特化判定パラメータ＋自己調整履歴）

```json
{
  "min_articles_before_check": 20,
  "min_days_before_check": 30,
  "specialization_ratio_threshold": 1.5,
  "min_data_points": 3,
  "bounds": {
    "ratio_threshold": [1.2, 2.0],
    "min_articles": [10, 40]
  },
  "review_history": [
    {
      "date": "2026-09-15",
      "decision": "specialize_love",
      "params_used": { "ratio_threshold": 1.5, "min_articles": 20 },
      "outcome_checked_at": "2026-09-25",
      "outcome": "維持(loveの優位が10記事後も継続)",
      "adjustment": "ratio_threshold 1.5→1.4に緩和(判断が早くても正しかったため)"
    }
  ]
}
```

---

## ジャンル選定ロジック

1. 候補 = （既存アクティブジャンル ＋ `genre_candidates.json` の `active` 状態） − 直近3投稿で使用したジャンル
2. `judgment_policy.json` の閾値を満たしていなければ、候補から均等ランダムで選ぶ
3. 閾値を満たしていれば（特化フェーズ）、上位ジャンルに重みを寄せた重み付きランダムで選ぶ（切り捨てない）
4. 同一ジャンルを選んだ場合、過去の `angle`（切り口）と重複しない新しい切り口を構成案で指定する

## 判定基準の自己調整ロジック

1. 特化判定（フェーズ切り替え）が発生するたびに、使用したパラメータと判定内容を `review_history` に記録
2. 判定から10記事後、`performance-analyst-soudan` が「その判定は結果的に正しかったか」を振り返る
   - 優位が継続 → 閾値を緩めて次回はより早く判定できるようにする
   - 優位が縮小/逆転 → 閾値を厳しくして次回はより慎重にする
3. 調整は `bounds` の範囲内のみ（暴走防止）。調整理由は必ず文章で `review_history` に残す
4. 振り返りデータが十分でない間は初期値のまま動作する

## 執筆品質の学習ループ

1. QAがNGを出す際は理由を箇条書きで構造化して返す
2. 当日の再チェックでは理由をそのまま執筆役に渡して修正（最大2回）
3. 理由は `qa_feedback_log.json` に消さず蓄積
4. `concept-planner-soudan` / `writer-soudan` は毎回、直近10件を「注意点リスト」として読み込み、構成案・執筆に反映する

---

## 画像/ロゴパイプライン

- **背景写真**: `ad-designer` サブエージェントがジャンルのシーン設定（`articles_config.py` 流用）からCanvaで生成
- **ロゴ/キャッチコピー**: `static/logo_overlay.png`。生成スクリプト `generate_logo_overlay.py` で文字だけ独立して作り直せる透過PNGとして管理（背景写真の品質に関わらず差し替え不要）
- **合成**: `compose_thumbnail.py` が背景+ロゴを重ねて `thumbnails/<date>_<genre>.png` を出力
- **フォールバック**: Canva生成が失敗/低品質時は既存 `generate_thumbnail.py` のグラデーション背景に自動切替。ロゴ合成ステップは共通なので当日の投稿は必ず完成する

---

## note投稿の安全策

2026-08-09の手動代行投稿で「タイトルと本文が混在する事故」が起きた実績（[[project_uketome_soudanshitsu]]参照）を踏まえ、以下を必須ステップとする。

1. タイトル欄入力後、必ずTabキーで本文欄へ移動
2. スクリーンショットでタイトルが見出しスタイルで本文と分離されていることを確認してから本文を流し込む
3. 画像アップロードは `mcp__claude-in-chrome__file_upload` ツールで自動操作を試みる
4. 投稿失敗時は1回だけリトライ、それでも失敗なら当日はスキップして通知

### 既知のリスク: 画像アップロード自動化

2026-08-09時点では「note.comの画像アップロードはネイティブファイル選択ダイアログを伴い、拡張機能から自動操作できない」ため、5記事とも手動アップロードだった実績がある。現在は `mcp__claude-in-chrome__file_upload` という専用ツールが利用可能になっており、これで解消している可能性があるが未検証。

**対応方針:** まず自動アップロードを試す。失敗した場合は記事をブロックせず、**画像なしで本文だけ先に投稿**し、Push通知で「画像は手動追加が必要」と知らせる（当日をまるごとスキップするより、投稿数を優先する）。

---

## 失敗時の扱い（全体）

| ケース | 挙動 |
|---|---|
| 執筆→QAループが2回ともNG | 当日スキップ、`qa_ng_max_retry` として記録、Push通知 |
| 画像生成が背景・フォールバック共に失敗 | 画像なしで本文だけ投稿、`image_missing` として記録、Push通知 |
| 画像アップロード自動化のみ失敗 | 画像なしで本文だけ投稿、`image_upload_failed` として記録、Push通知（手動追加を促す） |
| note投稿がエラー（1回リトライ後も失敗） | 当日スキップ、`post_failed` として記録、Push通知 |
| 本日分が既に `publish_history.json` にある | 即終了（二重投稿防止） |

---

## 運用中の設定変更・一時停止

無人で毎日走り続ける仕組みである以上、「いつでも軌道修正できる」ことを構造として保証する。

### いつでも編集できるもの

しきい値・ジャンル一覧・切り口ルールなど、挙動を左右するパラメータはすべてJSONファイル（`judgment_policy.json`, `genre_candidates.json`, `articles_config.py` 等）に集約している。コード変更は不要で、会話で「◯◯を△△に変えて」と伝えるだけで該当ファイルを編集すればよい。編集内容は**次回の日次実行から自動的に反映**される（再起動やデプロイの手順は不要）。

### 緊急停止スイッチ

`routine_control.json` を新設し、オーケストレーターは実行冒頭で必ずこれを読む。

```json
{ "enabled": true, "note": "" }
```

- `enabled: false` の間は、オーケストレーターは何もせず「停止中」とだけPush通知して終了する（ジャンル選定や投稿は一切走らない）
- 「今日だけ止めて」「しばらく止めて」等、会話で依頼されたらこのファイルを書き換えるだけで即座に反映される
- `note` に停止理由を書いておけば、再開時に経緯を思い出せる

### 変更の粒度

| 変更したい内容 | 編集するファイル | 反映タイミング |
|---|---|---|
| 特化判定のしきい値 | `judgment_policy.json` | 次回実行時 |
| ジャンルの追加/引退 | `genre_candidates.json` | 次回実行時 |
| 投稿時刻 | `/schedule` の設定 | 次回実行時 |
| 一時停止/再開 | `routine_control.json` | 次回実行時（即時） |
| ロゴ/キャッチコピー | `static/logo_overlay.png`（`generate_logo_overlay.py`で再生成） | 次回実行時 |

---

## 通知

毎日の実行後（成功/スキップいずれも）、Push通知（Claude Codeのプッシュ機能）で以下を要約:
- 選んだジャンル・切り口
- note URL（成功時）
- QA再試行回数
- スキップ時はスキップ理由

---

## ディレクトリ構成（追加分）

```
uketome-soudanshitsu/
  ├─ articles_config.py          # 既存: ジャンル基本情報
  ├─ generate_thumbnail.py       # 既存: グラデーション背景（フォールバック用に流用）
  ├─ x_post.py                   # 既存: X自動投稿（現在保留中、変更なし）
  ├─ daily_routine.md            # 新規: 日次オーケストレーターのプレイブック
  ├─ compose_thumbnail.py        # 新規: 背景+ロゴ合成
  ├─ generate_logo_overlay.py    # 新規: ロゴ/キャッチコピー独立生成
  ├─ publish_history.json        # 新規: 投稿実績ログ
  ├─ qa_feedback_log.json        # 新規: NG理由の蓄積
  ├─ genre_candidates.json       # 新規: 新ジャンル候補
  ├─ judgment_policy.json        # 新規: 特化判定パラメータ+自己調整履歴
  ├─ routine_control.json        # 新規: 一時停止スイッチ
  ├─ articles/                   # 新規: 生成記事本文の保存先
  └─ static/
       └─ logo_overlay.png       # 新規: ロゴ/キャッチコピー透過PNG

.claude/agents/
  ├─ performance-analyst-soudan.md   # 新規
  ├─ concept-planner-soudan.md       # 新規
  ├─ writer-soudan.md                # 新規
  └─ qa-reviewer-soudan.md           # 新規
```

---

## スケジューリング

`/schedule` で日次cron登録。既定は毎日9:00 JST（要望があれば変更可）。実行内容は `daily_routine.md` を参照する形にし、パラメータ変更（閾値調整など）はコード変更ではなくJSONファイル編集で完結させる。

---

## スコープ外（今回は対応しない）

- X（Twitter）自動投稿の再開（API従量課金の支払い設定待ち、[[project_uketome_soudanshitsu]]参照）
- note.comの正式な統計API連携（非公開のため、公開ページのスキ数のみを利用）
- 「成長型お悩み相談AIアプリ」本体の開発（将来構想、本設計はそのためのデータ収集基盤という位置づけ）
