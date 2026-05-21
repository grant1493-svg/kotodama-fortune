# generate_history.ps1

$projectDir   = "C:\Users\admin\.local\bin"
$desktop      = [Environment]::GetFolderPath('Desktop')
$outputFile   = Join-Path $desktop "history.html"
$launchBat    = "$projectDir\launch_claude.bat"
$maxCommits   = 20

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
$gitResult    = Get-GitHistory -dir $projectDir -count $maxCommits
$summaryFiles = Get-SummaryFiles -dir $projectDir
$html = New-HistoryHtml -gitResult $gitResult -files $summaryFiles
[System.IO.File]::WriteAllText($outputFile, $html, [System.Text.Encoding]::UTF8)
Write-Host "生成完了: $outputFile"
Start-Process $outputFile
