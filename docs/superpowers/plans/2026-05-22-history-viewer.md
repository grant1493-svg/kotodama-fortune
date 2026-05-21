# 作業履歴ビューアー 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** デスクトップの `履歴更新.bat` をダブルクリックするだけで git コミット履歴と会話まとめファイルの一覧を HTML でブラウザ表示し、各項目からブラウザ表示・フォルダ表示・Claude Code 起動ができるツールを作る

**Architecture:** `generate_history.ps1` が git ログとファイル一覧を収集して `history.html` をデスクトップに書き出す。`launch_claude.bat` は日本語パスの問題を避けるためプロジェクトフォルダ（`.local\bin`）に配置し、HTML から `file:///` リンクで参照する。

**Tech Stack:** PowerShell 5.1, Windows Batch, HTML/CSS/JavaScript (生成物)

---

## ファイルマップ

| ファイル | 役割 | 場所 |
|---------|------|------|
| `generate_history.ps1` | データ収集 + HTML 生成 | `C:\Users\admin\.local\bin\` |
| `launch_claude.bat` | プロジェクトフォルダで Claude Code 起動 | `C:\Users\admin\.local\bin\` |
| `履歴更新.bat` | エントリーポイント（Desktop に配置） | デスクトップ |
| `history.html` | 生成される履歴一覧（git 管理外） | デスクトップ（生成物） |

---

### Task 1: `launch_claude.bat` を作成する

**Files:**
- Create: `C:\Users\admin\.local\bin\launch_claude.bat`

- [ ] **Step 1: ファイルを作成する**

`C:\Users\admin\.local\bin\launch_claude.bat` の内容:

```batch
@echo off
cd /d C:\Users\admin\.local\bin
start cmd /k claude
```

- [ ] **Step 2: 動作確認**

エクスプローラで `C:\Users\admin\.local\bin\launch_claude.bat` をダブルクリックする。
期待値: 新しい `cmd` ウィンドウが `C:\Users\admin\.local\bin` を作業ディレクトリとして開き `claude` コマンドが起動する。

- [ ] **Step 3: コミット**

```powershell
git -C "C:\Users\admin\.local\bin" add launch_claude.bat
git -C "C:\Users\admin\.local\bin" commit -m "feat: add Claude Code launcher batch"
```

---

### Task 2: `generate_history.ps1` の基本構造を作成する

**Files:**
- Create: `C:\Users\admin\.local\bin\generate_history.ps1`

- [ ] **Step 1: スクリプトの定数・パス定義を書く**

`C:\Users\admin\.local\bin\generate_history.ps1` の内容（この時点では定数と空の関数だけ）:

```powershell
# generate_history.ps1

$projectDir   = "C:\Users\admin\.local\bin"
$desktop      = [Environment]::GetFolderPath('Desktop')
$outputFile   = Join-Path $desktop "history.html"
$launchBat    = "$projectDir\launch_claude.bat"
$maxCommits   = 20

function Get-GitHistory { param([string]$dir, [int]$count) }
function Get-SummaryFiles { param([string]$dir) }
function New-CommitHtml { param([hashtable]$commit) }
function New-FileHtml { param([hashtable]$file) }
function New-HistoryHtml { param([hashtable]$gitResult, [array]$files) }
```

- [ ] **Step 2: スクリプトが構文エラーなく読み込めることを確認**

```powershell
powershell -ExecutionPolicy Bypass -Command ". 'C:\Users\admin\.local\bin\generate_history.ps1'; Write-Host 'OK'"
```

期待値: `OK` と表示されること

---

### Task 3: git 履歴収集ロジックを実装する

**Files:**
- Modify: `C:\Users\admin\.local\bin\generate_history.ps1`

- [ ] **Step 1: `Get-GitHistory` 関数を実装する**

`generate_history.ps1` の `Get-GitHistory` を以下で置き換える:

```powershell
function Get-GitHistory {
    param([string]$dir, [int]$count)
    try {
        $log = & git -C $dir log --format="%H|%ad|%s" --date=format:"%Y-%m-%d" -n $count 2>&1
        if ($LASTEXITCODE -ne 0) {
            return @{ Error = "git 履歴取得に失敗しました" }
        }
        $commits = @()
        foreach ($line in $log) {
            if (-not $line) { continue }
            $parts = $line -split '\|', 3
            if ($parts.Count -eq 3) {
                $commits += [ordered]@{
                    Hash    = $parts[0].Substring(0, [Math]::Min(7, $parts[0].Length))
                    Date    = $parts[1]
                    Message = $parts[2]
                }
            }
        }
        return @{ Commits = $commits }
    } catch {
        return @{ Error = "git コマンドが見つかりません: $_" }
    }
}
```

- [ ] **Step 2: 関数の動作を確認する**

```powershell
powershell -ExecutionPolicy Bypass -Command @"
. 'C:\Users\admin\.local\bin\generate_history.ps1'
$r = Get-GitHistory -dir $projectDir -count 5
$r.Commits | ForEach-Object { Write-Host "$($_.Date) $($_.Hash) $($_.Message)" }
"@
```

期待値: 最新5件のコミットが `2026-05-22 481dd70 Google Analytics追加` 形式で表示されること

---

### Task 4: 会話まとめファイル一覧ロジックを実装する

**Files:**
- Modify: `C:\Users\admin\.local\bin\generate_history.ps1`

- [ ] **Step 1: `Get-SummaryFiles` 関数を実装する**

`generate_history.ps1` の `Get-SummaryFiles` を以下で置き換える:

```powershell
function Get-SummaryFiles {
    param([string]$dir)
    $files = Get-ChildItem -Path $dir -File |
        Where-Object {
            ($_.Extension -eq '.html' -or $_.Extension -eq '.md') -and
            $_.DirectoryName -eq $dir
        } |
        Sort-Object LastWriteTime -Descending
    return @($files | ForEach-Object {
        [ordered]@{
            Name     = $_.Name
            FullPath = $_.FullName
            Date     = $_.LastWriteTime.ToString("yyyy-MM-dd")
            IsHtml   = ($_.Extension -eq '.html')
        }
    })
}
```

- [ ] **Step 2: 関数の動作を確認する**

```powershell
powershell -ExecutionPolicy Bypass -Command @"
. 'C:\Users\admin\.local\bin\generate_history.ps1'
$files = Get-SummaryFiles -dir $projectDir
$files | ForEach-Object { Write-Host "$($_.Date) $($_.Name)" }
"@
```

期待値: `tasks_20260426.html`・`GoldEA_backtest_history.md`・`README_line_tasks.md` などが更新日降順で表示されること

---

### Task 5: HTML生成ロジックとスタイルを実装する

**Files:**
- Modify: `C:\Users\admin\.local\bin\generate_history.ps1`

- [ ] **Step 1: `New-CommitHtml`・`New-FileHtml`・`New-HistoryHtml` を実装してメイン処理を追加する**

`generate_history.ps1` の関数スケルトン3つとファイル末尾を以下で置き換える:

```powershell
function New-CommitHtml {
    param([hashtable]$commit)
    $folderUrl  = "file:///$($projectDir.Replace('\','/'))"
    $claudeUrl  = "file:///$($launchBat.Replace('\','/'))"
    return @"
<div class="item">
  <div class="item-info">
    <span class="badge git">git</span>
    <span class="date">$($commit.Date)</span>
    <span class="hash">$($commit.Hash)</span>
    <span class="message" title="$($commit.Message)">$($commit.Message)</span>
  </div>
  <div class="item-actions">
    <a href="$folderUrl" class="btn btn-folder">フォルダを開く</a>
    <a href="$claudeUrl" class="btn btn-claude">Claudeで続きから</a>
  </div>
</div>
"@
}

function New-FileHtml {
    param([hashtable]$file)
    $folderUrl  = "file:///$($projectDir.Replace('\','/'))"
    $claudeUrl  = "file:///$($launchBat.Replace('\','/'))"
    $fileUrl    = "file:///$($file.FullPath.Replace('\','/'))"
    $openBtn    = if ($file.IsHtml) { "<a href=`"$fileUrl`" target=`"_blank`" class=`"btn btn-open`">ブラウザで開く</a>" } else { "" }
    return @"
<div class="item">
  <div class="item-info">
    <span class="badge log">&#x1F4AC;</span>
    <span class="date">$($file.Date)</span>
    <span class="message" title="$($file.Name)">$($file.Name)</span>
  </div>
  <div class="item-actions">
    $openBtn
    <a href="$folderUrl" class="btn btn-folder">フォルダを開く</a>
    <a href="$claudeUrl" class="btn btn-claude">Claudeで続きから</a>
  </div>
</div>
"@
}

function New-HistoryHtml {
    param([hashtable]$gitResult, [array]$files)

    if ($gitResult.ContainsKey('Error')) {
        $gitRows = "<p class='empty'>$($gitResult.Error)</p>"
    } elseif ($gitResult.Commits.Count -eq 0) {
        $gitRows = "<p class='empty'>コミット履歴はありません</p>"
    } else {
        $gitRows = ($gitResult.Commits | ForEach-Object { New-CommitHtml -commit $_ }) -join "`n"
    }

    if ($files.Count -eq 0) {
        $fileRows = "<p class='empty'>会話まとめファイルはありません</p>"
    } else {
        $fileRows = ($files | ForEach-Object { New-FileHtml -file $_ }) -join "`n"
    }

    $now = Get-Date -Format "yyyy-MM-dd HH:mm"
    return @"
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>作業履歴ビューアー</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#1a1a2e;color:#e0e0e0;font-family:'Segoe UI',sans-serif;padding:24px}
.container{max-width:1280px;margin:0 auto}
h1{font-size:1.4rem;color:#a0c4ff;margin-bottom:4px}
.updated{font-size:.8rem;color:#888;margin-bottom:24px}
h2{font-size:1rem;color:#7ecbca;border-bottom:1px solid #333;padding-bottom:8px;margin:24px 0 12px}
.item{display:flex;justify-content:space-between;align-items:center;background:#16213e;border:1px solid #0f3460;border-radius:8px;padding:12px 16px;margin-bottom:8px;gap:12px;flex-wrap:wrap}
.item-info{display:flex;align-items:center;gap:10px;flex:1;min-width:0;flex-wrap:wrap}
.badge{font-size:.7rem;padding:2px 8px;border-radius:4px;font-weight:700;white-space:nowrap}
.badge.git{background:#0f3460;color:#a0c4ff}
.badge.log{background:#1a3a2e;color:#7ecbca}
.date{font-size:.8rem;color:#888;white-space:nowrap}
.hash{font-size:.75rem;color:#666;font-family:monospace;white-space:nowrap}
.message{font-size:.9rem;color:#ddd;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:500px}
.item-actions{display:flex;gap:8px;flex-shrink:0;flex-wrap:wrap}
.btn{font-size:.8rem;padding:5px 12px;border-radius:6px;text-decoration:none;white-space:nowrap;transition:opacity .2s;cursor:pointer}
.btn:hover{opacity:.75}
.btn-open{background:#1a5c8a;color:#fff}
.btn-folder{background:#3d3d5c;color:#ccc}
.btn-claude{background:#6b3fa0;color:#fff}
.empty{color:#666;padding:8px 0}
</style>
</head>
<body>
<div class="container">
  <h1>&#x1F4CC; 作業履歴ビューアー</h1>
  <p class="updated">最終更新: $now</p>
  <h2>&#x1F527; git コミット履歴（最新 $maxCommits 件）</h2>
  $gitRows
  <h2>&#x1F4AC; 会話まとめファイル</h2>
  $fileRows
</div>
</body>
</html>
"@
}

# ---- メイン処理 ----
$gitResult   = Get-GitHistory -dir $projectDir -count $maxCommits
$summaryFiles = Get-SummaryFiles -dir $projectDir
$html = New-HistoryHtml -gitResult $gitResult -files $summaryFiles
[System.IO.File]::WriteAllText($outputFile, $html, [System.Text.Encoding]::UTF8)
Write-Host "生成完了: $outputFile"
Start-Process $outputFile
```

- [ ] **Step 2: スクリプトを実行して HTML が生成されることを確認**

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\admin\.local\bin\generate_history.ps1"
```

期待値:
- `生成完了: C:\Users\admin\OneDrive\スキャン\デスクトップ\history.html` と表示される
- ブラウザが自動で開いてダークテーマの履歴一覧が表示される
- git コミット行に「フォルダを開く」「Claudeで続きから」の2ボタンがある
- .html 会話まとめ行に「ブラウザで開く」「フォルダを開く」「Claudeで続きから」の3ボタンがある
- .md 行には「フォルダを開く」「Claudeで続きから」の2ボタンがある

- [ ] **Step 3: 各ボタンの動作を目視確認**

| ボタン | 期待動作 |
|--------|---------|
| ブラウザで開く | 選択した .html ファイルが新しいタブで開く |
| フォルダを開く | エクスプローラで `C:\Users\admin\.local\bin\` が開く |
| Claudeで続きから | Edge: ダウンロードバーに `launch_claude.bat` の「ファイルを開く」プロンプトが表示される → クリックで CMD + Claude が起動する |

> **Note:** 「Claudeで続きから」は Edge (Windows 11 既定ブラウザ) で動作確認済みの想定。Chrome では .bat がダウンロードされるため、ダウンロードフォルダからダブルクリックして起動する。

- [ ] **Step 4: コミット**

```powershell
git -C "C:\Users\admin\.local\bin" add generate_history.ps1
git -C "C:\Users\admin\.local\bin" commit -m "feat: add history viewer PowerShell generator"
```

---

### Task 6: `履歴更新.bat` をデスクトップに作成してエンドツーエンド確認

**Files:**
- Create: デスクトップ\履歴更新.bat  (`[Environment]::GetFolderPath('Desktop')` で取得したパスに配置)

- [ ] **Step 1: デスクトップに `履歴更新.bat` を作成する**

PowerShell で実行:

```powershell
$desktop = [Environment]::GetFolderPath('Desktop')
$content = @'
@echo off
chcp 65001 > nul
powershell -ExecutionPolicy Bypass -File "C:\Users\admin\.local\bin\generate_history.ps1"
if errorlevel 1 (
    echo.
    echo エラーが発生しました。上記のメッセージを確認してください。
    pause
)
'@
[System.IO.File]::WriteAllText((Join-Path $desktop "履歴更新.bat"), $content, [System.Text.Encoding]::GetEncoding(932))
Write-Host "作成完了"
```

> **Note:** `.bat` ファイルは Shift-JIS (CP932) で保存する必要がある（`chcp 65001` で UTF-8 コンソールにしても、`.bat` ファイル自体は CP932 で読まれる）。`履歴更新.bat` というファイル名の日本語を正しく保存するために `Encoding(932)` を使用。

- [ ] **Step 2: デスクトップの `履歴更新.bat` をダブルクリックしてエンドツーエンド動作を確認**

期待値:
1. 黒いコマンドプロンプトウィンドウが一瞬開いて閉じる
2. ブラウザが自動起動して `history.html` が表示される
3. 最終更新日時が現在時刻になっている

- [ ] **Step 3: `history.html` を `.gitignore` に追加して生成物をコミット管理外にする**

`C:\Users\admin\.local\bin\.gitignore` に以下を確認・追記（なければ作成）:

```
# 生成物（デスクトップに出力されるため通常はコミット不要）
history.html
```

- [ ] **Step 4: 最終コミット**

```powershell
git -C "C:\Users\admin\.local\bin" add generate_history.ps1 launch_claude.bat .gitignore
git -C "C:\Users\admin\.local\bin" commit -m "feat: complete history viewer tool"
```
