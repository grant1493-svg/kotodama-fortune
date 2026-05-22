# generate_history.ps1

$projectDir   = "C:\Users\admin\.local\bin"
$desktop      = [Environment]::GetFolderPath('Desktop')
$outputFile   = Join-Path $desktop "history.html"
$launchBat    = "$projectDir\launch_claude.bat"
$maxCommits   = 20
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

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
    param($commit)
    $folderUrl  = "file:///$($script:projectDir.Replace('\','/'))"
    $claudeUrl  = "file:///$($script:launchBat.Replace('\','/'))"
    return @"
<div class="item">
  <div class="item-info">
    <span class="badge git">作業ログ</span>
    <span class="date">$($commit.Date)</span>
    <span class="message" title="$($commit.Hash)">$($commit.Message)</span>
  </div>
  <div class="item-actions">
    <a href="$folderUrl" class="btn btn-folder">📁 フォルダを開く</a>
    <button class="btn btn-claude" onclick="copyAndLaunch()">🤖 Claudeで続きから</button>
  </div>
</div>
"@
}

function New-FileHtml {
    param($file)
    $folderUrl  = "file:///$($script:projectDir.Replace('\','/'))"
    $claudeUrl  = "file:///$($script:launchBat.Replace('\','/'))"
    $fileUrl    = "file:///$($file.FullPath.Replace('\','/'))"
    $openBtn    = if ($file.IsHtml) { "<a href=`"$fileUrl`" target=`"_blank`" class=`"btn btn-open`">📄 内容を見る</a>" } else { "" }
    return @"
<div class="item">
  <div class="item-info">
    <span class="badge log">保存ファイル</span>
    <span class="date">$($file.Date)</span>
    <span class="message" title="$($file.Name)">$($file.Name)</span>
  </div>
  <div class="item-actions">
    $openBtn
    <a href="$folderUrl" class="btn btn-folder">📁 フォルダを開く</a>
    <button class="btn btn-claude" onclick="copyAndLaunch()">🤖 Claudeで続きから</button>
  </div>
</div>
"@
}

function New-HistoryHtml {
    param([hashtable]$gitResult, [array]$files)

    if ($gitResult.ContainsKey('Error')) {
        $gitRows = "<p class='empty'>$($gitResult.Error)</p>"
    } elseif ($gitResult.Commits.Count -eq 0) {
        $gitRows = "<p class='empty'>作業ログはありません</p>"
    } else {
        $gitRows = ($gitResult.Commits | ForEach-Object { New-CommitHtml -commit $_ }) -join "`n"
    }

    if ($files.Count -eq 0) {
        $fileRows = "<p class='empty'>保存済みファイルはありません</p>"
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
body{background:#1a1a2e;color:#e0e0e0;font-family:'Meiryo','Segoe UI',sans-serif;padding:24px}
.container{max-width:1280px;margin:0 auto}
h1{font-size:1.5rem;color:#a0c4ff;margin-bottom:4px}
.updated{font-size:.8rem;color:#888;margin-bottom:16px}
.guide{background:#0f2040;border:1px solid #1a4a7a;border-radius:10px;padding:16px 20px;margin-bottom:24px}
.guide h3{font-size:.95rem;color:#a0c4ff;margin-bottom:10px}
.guide-row{font-size:.85rem;color:#ccc;padding:4px 0;line-height:1.6}
.guide-row b{color:#e0e0e0}
.guide-refresh{margin-top:10px;font-size:.85rem;color:#7ecbca;border-top:1px solid #1a4a7a;padding-top:10px}
h2{font-size:1rem;color:#7ecbca;border-bottom:1px solid #333;padding-bottom:8px;margin:24px 0 12px}
.item{display:flex;justify-content:space-between;align-items:center;background:#16213e;border:1px solid #0f3460;border-radius:8px;padding:12px 16px;margin-bottom:8px;gap:12px;flex-wrap:wrap}
.item-info{display:flex;align-items:center;gap:10px;flex:1;min-width:0;flex-wrap:wrap}
.badge{font-size:.7rem;padding:2px 8px;border-radius:4px;font-weight:700;white-space:nowrap}
.badge.git{background:#0f3460;color:#a0c4ff}
.badge.log{background:#1a3a2e;color:#7ecbca}
.date{font-size:.8rem;color:#888;white-space:nowrap}
.message{font-size:.9rem;color:#ddd;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:600px}
.item-actions{display:flex;gap:8px;flex-shrink:0;flex-wrap:wrap}
.btn{font-size:.85rem;padding:6px 14px;border-radius:6px;text-decoration:none;white-space:nowrap;transition:opacity .2s;cursor:pointer;border:none}
.btn:hover{opacity:.75}
.btn-open{background:#1a5c8a;color:#fff}
.btn-folder{background:#3d3d5c;color:#ccc}
.btn-claude{background:#6b3fa0;color:#fff}
.empty{color:#666;padding:8px 0}
#claude-note{display:none;position:fixed;bottom:24px;right:24px;background:#2a1a4a;border:1px solid #6b3fa0;border-radius:10px;padding:16px 20px;max-width:320px;font-size:.85rem;line-height:1.7;z-index:100;box-shadow:0 4px 20px rgba(0,0,0,.5)}
#claude-note b{color:#c4a0ff;display:block;margin-bottom:6px}
#claude-note .close{cursor:pointer;color:#888;float:right;font-size:1.1rem;margin-top:-2px}
</style>
</head>
<body>
<div class="container">
  <h1>&#x1F4CC; 作業履歴ビューアー</h1>
  <p class="updated">最終更新: $now</p>

  <div class="guide">
    <h3>📖 ボタンの使い方</h3>
    <div class="guide-row">📄 <b>内容を見る</b> ― 保存されたHTMLファイルをブラウザで表示します</div>
    <div class="guide-row">📁 <b>フォルダを開く</b> ― 作業フォルダをエクスプローラで開きます</div>
    <div class="guide-row">🤖 <b>Claudeで続きから</b> ― クリックするとコマンドがコピーされます。デスクトップの「Claudeを起動.bat」をダブルクリックするか、コマンドプロンプトに貼り付けてください</div>
    <div class="guide-refresh">🔄 <b>情報を最新にするには</b>：デスクトップの「履歴更新.bat」をダブルクリックしてください</div>
  </div>

  <h2>📋 最近の作業ログ（直近 $maxCommits 件）</h2>
  $gitRows
  <h2>💾 保存済みファイル一覧</h2>
  $fileRows
</div>

<div id="claude-note">
  <span class="close" onclick="document.getElementById('claude-note').style.display='none'">✕</span>
  <b>🤖 Claudeで続きから — 手順</b>
  <div id="cn-copied" style="display:none;color:#7eff9a;margin-bottom:8px">✅ コマンドをコピーしました！</div>
  <div id="cn-manual" style="display:none;color:#ffb347;margin-bottom:8px">⚠ 手動でコピーしてください</div>
  <b style="font-size:.8rem;color:#aaa">コマンド（貼り付け用）：</b>
  <div id="cmd-box" style="background:#1a1a2e;border:1px solid #444;border-radius:4px;padding:6px 10px;margin:6px 0;font-family:monospace;font-size:.85rem;color:#7ecbca;user-select:all">claude</div>
  <div style="font-size:.82rem;color:#ccc;line-height:1.7">
    ① デスクトップの <b>「Claudeを起動.bat」</b> をダブルクリック<br>
    　または<br>
    ② コマンドプロンプト/PowerShell を開いて貼り付け・Enter
  </div>
</div>
<script>
function copyAndLaunch(){
  var n=document.getElementById('claude-note');
  n.style.display='block';
  var el=document.createElement('textarea');
  el.value='claude';
  el.style.position='absolute';el.style.left='-9999px';
  document.body.appendChild(el);
  el.select();
  try{
    document.execCommand('copy');
    document.getElementById('cn-copied').style.display='block';
    document.getElementById('cn-manual').style.display='none';
  }catch(e){
    document.getElementById('cn-manual').style.display='block';
    document.getElementById('cn-copied').style.display='none';
  }
  document.body.removeChild(el);
  setTimeout(function(){n.style.display='none';
    document.getElementById('cn-copied').style.display='none';
    document.getElementById('cn-manual').style.display='none';
  },12000);
}
</script>
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
$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
if (Test-Path $edge) {
    Start-Process $edge -ArgumentList "`"$outputFile`""
} else {
    Start-Process cmd -ArgumentList "/c", "start", '""', "`"$outputFile`""
}
