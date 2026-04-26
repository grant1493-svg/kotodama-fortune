# LINE タスク抽出ツール

LINEのグループチャット履歴（.txtエクスポート）をClaude AIが分析し、タスク・依頼・指示を自動抽出してHTMLタスク表を生成します。

## セットアップ

### 1. Python インストール確認
```bash
python --version  # 3.8以上が必要
```

### 2. 依存パッケージをインストール
```bash
pip install anthropic
```

### 3. APIキーを設定
```bash
# Windows（コマンドプロンプト）
set ANTHROPIC_API_KEY=sk-ant-...

# Windows（PowerShell）
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

## 使い方

```bash
python line_tasks.py "トーク履歴.txt"
```

→ `tasks_20260426.html` が生成されます。ブラウザで開いてください。

### オプション
```bash
python line_tasks.py "トーク履歴.txt" --output 会議タスク.html
```

## LINEのログエクスポート方法

1. LINEアプリでトーク画面を開く
2. 右上のメニュー → 「トーク履歴を送信」
3. 「テキスト形式」で保存
4. 保存した .txt ファイルを本ツールに渡す

## HTMLの使い方

| 操作 | 内容 |
|------|------|
| 進捗ボタンをクリック | 未着手→進行中→完了 と切り替わる |
| 完了にする | 「完了済み」セクションに自動移動 |
| 担当者/優先度フィルター | 絞り込み表示 |
| 印刷ボタン | 印刷用レイアウトで出力 |

状態はブラウザに自動保存されます（再読み込みしても維持）。
