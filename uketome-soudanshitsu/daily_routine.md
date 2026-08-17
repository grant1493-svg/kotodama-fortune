# うけとめ相談室 日次オーケストレーター

毎日1回、このプレイブックに従って実行する。設計書: `docs/superpowers/specs/2026-08-11-uketome-soudanshitsu-daily-automation-design.md`

## 0. 事前チェック

1. `cd uketome-soudanshitsu && python -c "from control import is_enabled; from pathlib import Path; print(is_enabled(Path('routine_control.json')))"` を実行する
   - `False`なら、Push通知で「うけとめ相談室: 停止中のため本日はスキップ」を送って終了する
2. `cd uketome-soudanshitsu && python -c "from history_store import load_history, already_recorded_today; from pathlib import Path; from datetime import date; h = load_history(Path('publish_history.json')); print(already_recorded_today(h, date.today().isoformat()))"` を実行する
   - `True`なら、二重実行なので何もせず終了する

## 1. 分析（performance-analyst-soudan）

Agentツールで`performance-analyst-soudan`を起動し、分析ブリーフを取得する。

## 2. 企画会議（concept-planner-soudan）

Agentツールで`concept-planner-soudan`を起動し、分析ブリーフを渡して本日の構成案を取得する。

## 3. 執筆〜編集チェックのループ（最大2回リトライ）

1. Agentツールで`writer-soudan`を起動し、構成案から記事本文を書かせる
2. Agentツールで`qa-reviewer-soudan`を起動し、GO/NG判定を取得する
3. GOなら4へ進む
4. NGなら、NG理由を`qa_feedback_log.json`に追記し（`history_store.py`と同じ書き込みパターンでJSON配列にappendする）、`writer-soudan`にNG理由を渡して再執筆させる。これを最大2回まで繰り返す
5. 2回ともNGなら、`publish_history.json`に`{"date": 今日, "status": "skipped", "reason": "qa_ng_max_retry"}`を追記し、Push通知を送って終了する

## 4. 画像生成

1. Agentツールで`ad-designer`を起動し、本日のジャンルのシーン設定から背景写真を生成させる（保存先: `uketome-soudanshitsu/thumbnails/<date>_<genre>_bg.png`）
2. 生成に失敗した場合、`cd uketome-soudanshitsu && python generate_thumbnail.py`相当のグラデーション背景をフォールバックとして使う（`compose_thumbnail.py`の`background_path=None`で自動的にフォールバックされる）

## 5. 画像合成

```bash
cd uketome-soudanshitsu && python -c "
from pathlib import Path
from compose_thumbnail import compose_thumbnail
compose_thumbnail(
    title='<本日のタイトル案>',
    color_start=(<articles_config.pyの該当ジャンルcolor_start>),
    color_end=(<同color_end>),
    output_path=Path('thumbnails/<date>_<genre>.png'),
    background_path=Path('thumbnails/<date>_<genre>_bg.png'),
    logo_overlay_path=Path('static/logo_overlay.png'),
)
"
```

## 6. note投稿（claude-in-chrome）

1. note.comの新規記事作成画面を開く
2. タイトルを入力 → 必ずTabキーで本文欄へ移動
3. スクリーンショットでタイトルが見出しスタイルで本文と分離されていることを確認してから本文を流し込む
4. `mcp__claude-in-chrome__file_upload`でアイキャッチ画像(`thumbnails/<date>_<genre>.png`)のアップロードを試みる
   - 失敗した場合: 画像なしのまま次へ進む（`image_upload_failed`として後でログに記録）
5. 公開し、発行後のURLを取得する
6. 投稿自体が失敗した場合は1回だけリトライする。それでも失敗したら`publish_history.json`に`status: "skipped", "reason": "post_failed"`を記録してPush通知を送り終了する

## 7. ログ記録

`uketome-soudanshitsu/publish_history.json`に本日のエントリをappendする（`history_store.append_entry`と同じ形式）:

```json
{
  "date": "<今日の日付>",
  "status": "published",
  "genre": "<ジャンルkey>",
  "angle": "<切り口>",
  "note_url": "<取得したURL>",
  "like_count": null,
  "like_count_checked_at": null,
  "qa_retry_count": <0,1,2のいずれか>
}
```

画像アップロードが失敗していた場合は`"image_upload_failed": true`も追加する。

## 8. 過去記事のスキ数更新

`publish_history.json`の`status: "published"`かつ`note_url`があるすべてのエントリについて、`like_counter.fetch_like_count`でスキ数を再取得し、`like_count`と`like_count_checked_at`を更新する。

## 9. Push通知

以下を要約してPush通知を送る:
- 選んだジャンル・切り口
- note URL（成功時）／スキップ理由（スキップ時）
- QA再試行回数
- 画像アップロードが手動対応必要な場合はその旨
