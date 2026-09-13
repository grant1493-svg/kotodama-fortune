# 言霊ものがたり 初回公開

2026-09-13、ユーザーが見本で停止せず目的達成まで進めるよう指定。

## 今回実装
- /stories/bridge（頼る）、/stories/rest（休む）、/stories/step（一歩踏み出す）の3作×4場面。
- 入力画面・名前紹介・占い結果から案内。占い結果の今日メッセージの単語に基づき休息/挑戦を選び、それ以外は頼る物語。AIによる精密な適合判定ではない。利用者がテーマを選び直せる。
- 追加生成APIなし。32秒自動送り、手動送り、一時停止・途中再開、別タブへ移動時停止。音声なし、動画ファイルではなくWeb紙芝居。
- 一言メモは送信・保存なし。広告スクリプトを読み込まない独立テンプレート。
- GA4 G-XMQ7M4M5J1に任意同意後のみstory_view/story_start/story_final_scene/story_action。作品IDだけを独自パラメータとし、名前・メモ・流入URLのクエリは含めない。最終場面表示は読了や満足の証明ではない。同意者のみの偏った計測であり、全訪問者と同一視しない。
- プライバシー説明を現行利用状況に合わせて追記。新しい外部アカウント・課金・LINE/X送信なし。

## 確認
画面・ルーティング等33テストPASS、再生/停止/計測の同意制御/メモ非送信4テストPASS。ローカルのテーマ切り替え、生成画像12場面、PC表示を確認。元見本では390px幅も確認済み。GAの管理画面での受信確認と利用者反応は未確認。

## 画像
内蔵image_gen使用。static/stories/{bridge,rest,step}.png。原本はCodex生成画像フォルダに保持。bridgeは先の見本画像を再利用。
追加画像の共通プロンプト：Create square 2x2 grid, four equal square watercolor storybook illustrations, seamless grid no gutters, absolutely no words. Consistent small orange fox with teal scarf, sage forest ivory and warm peach palette, beautiful sophisticated picture book style. Each scene independently centered and complete. No danger, gentle emotion, no text, no labels. Same fox across panels. Image for Japanese adult relaxation storytelling website.
rest場面：fox worries beside closed bud / puts down watering can and rests / sleeps under moon / wakes beside opened flower。
step場面：fox hesitates at shallow stream / tests nearest stone / walks one stone at a time / stands on other bank。

## 目的と残件
今回の目的は、無料占いに物語を組み合わせ、再訪したくなる体験を本番で使えるようにすること。作品追加だけでは収益化・満足度を達成したとはしない。
次はGA受信確認と実利用の観察。暫定2週間は拡大制作より現行3作品の反応を確認する。閲覧母数・計測同意率が足りなければ需要なしとは判断しない。入口で離脱するなら案内、最終場面まで進まないなら長さ/操作性、利用されても戻らないなら内容を改善する。有料販売は購入価値と納品方式を具体化してから。完全自動化の親タスクは未完了。
