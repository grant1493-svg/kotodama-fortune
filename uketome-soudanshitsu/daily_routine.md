# うけとめ相談室 日次オーケストレーター

毎日1回、このプレイブックに従って実行する。設計書: `docs/superpowers/specs/2026-08-11-uketome-soudanshitsu-daily-automation-design.md`

## 0. 事前チェック

1. `cd uketome-soudanshitsu && python -c "from control import is_enabled; from pathlib import Path; print(is_enabled(Path('routine_control.json')))"` を実行する
   - `False`なら、Push通知で「うけとめ相談室: 停止中のため本日はスキップ」を送って終了する
2. `cd uketome-soudanshitsu && python -c "from history_store import load_history, already_recorded_today; from pathlib import Path; from datetime import date; h = load_history(Path('publish_history.json')); print(already_recorded_today(h, date.today().isoformat()))"` を実行する
   - `True`なら、二重実行（またはstatus: "in_progress"のまま未解決の前回実行）なので何もせず終了する。`publish_history.json`の当日エントリが`"in_progress"`のままの場合は、Push通知で「うけとめ相談室: 前回実行が未解決のため要確認」を送って人による調査を促す

## 1. スキ数更新

分析より先に実行する（分析が当日最新のスキ数を使えるようにするため。過去は§8相当の位置で投稿後に行っていたが、それだと分析が常に1日古いデータを見ることになり、かつ本日公開したばかりの記事が`like_count: 0`として即座にその日のジャンル平均へ混入してしまう問題があったため、ここに移動した）。

`publish_history.json`の`status: "published"`かつ`note_url`があるすべてのエントリについて、`like_counter.fetch_like_count`でスキ数を再取得し、`like_count`と`like_count_checked_at`を更新する。

## 2. 分析（performance-analyst-soudan）

Agentツールで`performance-analyst-soudan`を起動し、分析ブリーフを取得する（§1で更新済みの最新`publish_history.json`を読ませる）。

## 3. ジャンル確定（オーケストレーター自身がbashで実行）

企画会議に丸投げせず、テスト済みの`rotation.py`のロジックを実際に呼び出して本日のジャンルを機械的に確定する（gap=3のジャンルローテーション除外はLLMの読解力ではなくこの呼び出しで保証する）:

```bash
cd uketome-soudanshitsu && python -c "
import json
import random
from pathlib import Path

from history_store import load_history
from rotation import eligible_genres, average_likes_by_genre, pick_genre

history = load_history(Path('publish_history.json'))
candidates = json.loads(Path('genre_candidates.json').read_text(encoding='utf-8'))
all_genres = [c['key'] for c in candidates if c['status'] == 'active']

eligible = eligible_genres(all_genres, history, gap=3)
avg_likes = average_likes_by_genre(history)
specialize = <分析ブリーフの「特化フェーズに入るべきか」の判定結果をTrue/Falseで埋める>
genre = pick_genre(eligible, avg_likes, specialize=specialize, rng=random.Random())
print('eligible:', eligible)
print('picked:', genre)
"
```

出力された`picked`のジャンルkeyを、確定ジャンルとして次工程（企画会議）に渡す。

## 4. 企画会議（concept-planner-soudan）

Agentツールで`concept-planner-soudan`を起動し、分析ブリーフと§3で確定したジャンル(key)を渡して本日の切り口・記事構成案を取得する（ジャンル選定は§3で完了済みなので、企画会議はジャンルを選ばず、渡されたジャンルの切り口・構成のみを決める）。

## 5. 執筆〜編集チェックのループ（最大2回の再執筆、合計3回まで試行）

1. Agentツールで`writer-soudan`を起動し、構成案から記事本文を書かせる（1回目の執筆）
2. Agentツールで`qa-reviewer-soudan`を起動し、GO/NG判定を取得する
3. GOなら6へ進む
4. NGなら、NG理由を`qa_feedback_log.json`に追記し（`history_store.py`と同じ書き込みパターンでJSON配列にappendする）、`writer-soudan`にNG理由を渡して再執筆させる。これを最大2回まで繰り返す（＝再執筆2回、合計で最大3回の執筆試行）
5. 再執筆を2回行ってもなおNGなら、`publish_history.json`に`{"date": 今日, "status": "skipped", "reason": "qa_ng_max_retry"}`を追記し、Push通知を送って終了する

## 6. 画像生成

1. Agentツールで`ad-designer`を起動し、本日のジャンルのシーン設定から背景写真を生成させる（保存先: `uketome-soudanshitsu/thumbnails/<date>_<genre>_bg.png`）
   - 注意（2026-08-17の実運用ドライランで確認済み）: 現在のCanva連携ツールセットには、生成した候補（candidate）を書き出し可能な正式デザインへ実体化する手段が含まれておらず、711×400程度の低解像度プレビューしか得られない場合がある。この場合は無理に高解像度化を試みず、生成失敗として扱い次のフォールバックへ進んでよい。
2. 生成に失敗した場合、`cd uketome-soudanshitsu && python generate_thumbnail.py`相当のグラデーション背景をフォールバックとして使う（`compose_thumbnail.py`の`background_path=None`で自動的にフォールバックされる）

## 7. 画像合成

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

**注意（2026-08-18の実運用ドライランで発見した不具合への対策）**: `title`には改行文字(`\n`)を含めない、折り返しのない1行の文字列を渡すこと。`compose_thumbnail`の内部実装（`generate_thumbnail._wrap_text`）は15文字ごとに機械的に折り返す前提で、折り返した各行を個別に`draw.text`で描画している。ここに`\n`入りの文字列を渡すと、PILがその1行の中でさらに独自の改行処理を行い、外側のループが計算する行送り(68px)とズレて2行が重なって描画され、文字が判読不能なほど潰れる（実例: 「罪悪感を覚える」の行が別の行と重なり「翼悪感あなたへ」のような文字化けになった）。生成後は必ずタイトルが正しく判読できるか画像を確認する。

## 8. note投稿（claude-in-chrome）

1. **二重投稿防止のため、公開を試みる前に`publish_history.json`へ暫定エントリを追記する**（`history_store.append_entry`と同じ形式）: `{"date": 今日, "status": "in_progress", "genre": "<ジャンルkey>"}`。この後の手順が途中で失敗・中断しても、この暫定エントリが残っていれば§0.2の二重実行ガードが働き、同日の再実行で別記事が二重公開されることを防げる（未解決のまま残った場合は§0.2の分岐でPush通知され、人が確認する）。
2. note.comの新規記事作成画面を開く
3. タイトルを入力 → 必ずTabキーで本文欄へ移動
4. スクリーンショットでタイトルが見出しスタイルで本文と分離されていることを確認してから本文を流し込む
5. **体裁チェック（重要・2026-08-17の実運用ドライランで発見した不具合への対策）**: `mcp__claude-in-chrome__computer`の`type`で長文（3,000字前後）を一括流し込むと、note.comのMarkdown自動変換が箇条書き・番号付きリストの2項目目以降で失敗し、自動生成されたマーカーとは別に元の`- `/`N. `が本文側にそのまま残ってしまう事故が起きる（例: 「• - 具体性: …」「2. 2. 区切る: …」。1項目目だけは正しく変換される）。
   - このチェックにスクリーンショットは使わない。挿入直後のnote.comタブは描画が不安定になりやすく（多重描画のゴースト、空白レンダリング、まれにビューポートが極端に縮小する等）、実際には壊れていない内容が壊れて見える／壊れた内容が正常に見える、どちらの誤認も起こりうる。必ず`mcp__claude-in-chrome__get_page_text`でDOMの実テキストを取得して判定する。
   - 各リストのitem 2件目以降のテキストが`- `、または自分の項番と一致する`N. `（もしくはそれが1文字だけ欠けた不完全な残骸、例: 先頭に孤立した数字1文字だけが残っている状態）で始まっていないか確認する。見つかった場合は、そのリスト項目の実テキストが始まる直前（本来の内容の先頭文字の左側）にクリックしてカーソルを置き→`shift+Left`でズレた文字数分（`- `なら2文字＝ハイフン+半角スペース、`N. `ならNの桁数+2文字＝数字+ピリオド+半角スペース。例:「2. 」は3文字）を選択→`Delete`で削除、を項目ごとに行う。選択文字数の確認は、ズームまたはスクリーンショットではなく、note.comエディタが選択中に画面右上へ表示する「選択中 N/合計文字数」というテキストインジケータを読むこと（2026-08-18のドライランで確認済み: 挿入直後のタブはズーム/スクリーンショットでも引き続き不安定で、実際は2文字しか選択されていないのに行全体がハイライトされて見える誤表示が起きた。テキストインジケータの数字は実際の選択範囲と一致していた）。`Delete`を押した直後は必ず`get_page_text`で該当箇所を再取得し、実際にテキストが変化したことを確認する（まれに`Delete`キー入力が反映されず選択状態のまま変わらないことがあったため、反映されていなければもう一度`Delete`を送る）。修正後は再度`get_page_text`で全リストを確認し、`- `/`N. `の完全な残骸だけでなく、孤立した数字やハイフンなど本来の見出し語の前に余分な文字が残っていないかも含めて、他の箇所に波及していないか見る。
   - **見出し（`##`/`###`）が変換されずそのままリスト項目の文字として残る不具合（2026-08-18のドライランで新規発見）**: カーソルがまだ箇条書きリストの中（直前の入力がリスト項目で終わり、続けて`### 見出しテキスト`のような行を入力した場合）にあると、note.comのMarkdown自動変換はリスト継続を優先し、`###`はただの文字列としてリストの新しい項目になってしまう（見出しスタイルにならない）。この不具合は前述の`- `残骸と違い、リスト項目内に埋もれて一見普通の太字テキストのように見えるため、スクロールで斜め読みしただけでは見逃しやすい。対策: 1つのセクションを書き終えて次の見出し（`##`/`###`）を入力する前に、必ず`get_page_text`でその直前の要素がリスト項目（`listitem`）ではなく通常の段落であることを確認してから見出しを入力する。もし変換されずに残ってしまった場合は、`find`でその見出しテキストを検索してリスト項目内にあることを確認し、その行をtriple_clickで全選択→`Backspace`で削除（空のリスト項目になる）→空リスト項目内で`Backspace`をもう一度押して箇条書き自体を抜ける（通常の空段落になる）→そこへ`### 見出しテキスト`を入力し直す（リストの外なので正しく見出しに変換される）。
   - 自動修正後も確証が持てない場合は、無理に公開せず1で追記した暫定エントリを`status: "skipped", "reason": "list_formatting_unverifiable"`に更新し、Push通知を送って終了する（壊れた体裁のまま公開しない）。
6. `mcp__claude-in-chrome__file_upload`でアイキャッチ画像(`thumbnails/<date>_<genre>.png`)のアップロードを試みる
   - 失敗した場合: 画像なしのまま次へ進む（`image_upload_failed`として後でログに記録）。note.comのアイキャッチ画像欄はネイティブOSファイル選択ダイアログを伴い、`input[type=file]`要素がアクセシビリティツリー上に現れないため、ブラウザ拡張からの自動化は現時点（2026-08-17確認）で不可能。`find`/`read_page`で探しても見つからないので、早めに諦めて次へ進んでよい。
7. 公開し、発行後のURLを取得する
8. 投稿自体が失敗した場合は1回だけリトライする。それでも失敗したら1で追記した暫定エントリを`status: "skipped", "reason": "post_failed"`に更新し、Push通知を送り終了する

## 9. ログ記録

§8-1で追記した暫定エントリ（`status: "in_progress"`）を、以下の内容で`status: "published"`に更新する（`history_store.save_history`で該当エントリを書き換える。`in_progress`のまま残さない）:

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

## 10. Push通知

以下を要約してPush通知を送る:
- 選んだジャンル・切り口
- note URL（成功時）／スキップ理由（スキップ時）
- QA再試行回数
- 画像アップロードが手動対応必要な場合は、その旨に加えてサムネイル画像のファイルシステム上の絶対パス（`uketome-soudanshitsu/`からの相対パス`thumbnails/<date>_<genre>.png`ではなく、実行時のカレントディレクトリを起点に組み立てた完全なパス。例: `C:\Users\admin\.local\bin\uketome-soudanshitsu\thumbnails\<date>_<genre>.png`）とnote URLを同じ通知内に含める。Push通知は端末上で単独で読まれるため、相対パスでは手元のターミナルの文脈が失われて役に立たない（手動でのドラッグ&ドロップ添付を1ステップで済ませられるようにするため）
