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
function New-CommitHtml { param([hashtable]$commit) }
function New-FileHtml { param([hashtable]$file) }
function New-HistoryHtml { param([hashtable]$gitResult, [array]$files) }
